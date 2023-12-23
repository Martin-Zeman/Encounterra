import copy
from itertools import combinations

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import Passive
from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key
from ..effects.effect import EffectType
from ..effects.end_of_turn_combatant_effect import EndOfTurnEffect
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..spells.spell import SpellStats
from ..misc import RollType, avg_roll, Visibility, SavingThrow, reconcile_roll_types, \
    roll_saving_throw, get_strength_based_attack_factories, ROUND_HORIZON
from ..conditions import Conditions, is_affected_by_any, is_affected_by, get_swallower
from ..actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import cache
from ..threat_utils import calc_p_hit
from ..threat_interfaces import Threat
from ..factory_interfaces import DirectThreatFactory
import logging
from ..utils.roll_types import ROLL_TYPE_DELTA, ThreatModifierType

logger = logging.getLogger("Encounterra")


class TwinnedRayOfEnfeeblementFactory(DirectThreatFactory):
    level = 2
    range = SpellStats.Range.FEET_60.value
    target = SpellStats.Target.TWO_CREATURES
    duration = SpellStats.Duration.MINUTE
    concentration = True
    type = SpellStats.Type.HARMFUL
    dmg_type = None

    def __init__(self, action_type, caster, resource):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.flags |= FactoryFlags.USES_CALCULATE_THREAT_IN_DELTA
        self.to_hit = caster.spell_to_hit
        self.dc = caster.dc
        self.action_type = action_type  # RAY_OF_ENFEEBLEMENT, TWINNED_RAY_OF_ENFEEBLEMENT, QUICKENED_RAY_OF_ENFEEBLEMENT
        self.dmg_dice = "0d0"
        self.combatant = caster
        self.resource = resource
        self.saving_throw = SavingThrow.CON

    def __str__(self):
        """
        Important for FSM building
        """
        return "TwinnedRayOfEnfeeblementFactory"

    def get_ability_name(self):
        return "Twinned Ray of Enfeeblement"

    def get_twinned_kwargs(self):
        return {'caster': self.combatant, 'resource': self.resource}

    def get_quickened_kwargs(self):
        return {'caster': self.combatant, 'resource': self.resource}

    def get_eligible_targets(self):
        swallower = get_swallower(self.combatant)
        if swallower:
            return []
        enemies = Map.get().get_enemies(self.combatant)
        if len(enemies) < 2:
            return []  # Let's not waste a twinned version on this
        return combinations([e for e in enemies if not is_affected_by(e, Conditions.SWALLOWED)], 2)

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [RayOfEnfeeblement(t, self) for t in targets]

    def create(self, targets):
        return RayOfEnfeeblement(targets, self)

    def calculate_threat_to_target(self, target, **kwargs):
        max_threat = 0
        p_hit = calc_p_hit(self.to_hit, target.ac)
        afs = get_strength_based_attack_factories(target)
        for af in afs:
            dmg_inc = af.calculate_threat_to_target(self.combatant) / 2
            max_threat = max(dmg_inc, max_threat)
        return p_hit * max_threat * ROUND_HORIZON

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications.
        This is useful calculating the potential reduction of threat_in caused by abilities of enemies, e.g. advantage on saving throw
        against fireball or bane on attack rolls etc.
        """
        mod_to_hit_flat = modifiers.get(ThreatModifierType.TO_HIT_FLAT, 0)
        mod_to_hit_die = modifiers.get(ThreatModifierType.TO_HIT_DIE, '0d0')
        target_ac = modifiers.get(ThreatModifierType.TARGET_AC, 0)
        roll_type = modifiers.get(ThreatModifierType.ROLL_TYPE, RollType.STRAIGHT)

        total_target_ac = target.ac + target_ac
        to_hit_total = self.to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
        try:
            to_hit_total += ROLL_TYPE_DELTA[roll_type][max(0, min(total_target_ac - to_hit_total, 20))]
        except KeyError:  # Can happen for extreme differences between the AC and the to_hit
            pass  # The effect is negligible in that case

        max_threat = 0
        baseline_p_hit = calc_p_hit(self.to_hit, target.ac)
        modified_p_hit = calc_p_hit(to_hit_total, total_target_ac)
        afs = get_strength_based_attack_factories(target)
        for af in afs:
            dmg_inc = af.calculate_threat_to_target(self.combatant) / 2
            max_threat = max(dmg_inc, max_threat)
        return (modified_p_hit - baseline_p_hit) * max_threat * ROUND_HORIZON

    def calculate_max_threat(self):
        if get_swallower(self.combatant):
            return 0
        targets = [e for e in Map.get().get_enemies(self.combatant) if not is_affected_by(e, Conditions.SWALLOWED)]
        threats = sorted([self.calculate_threat_to_target(t) for t in targets], reverse=True)
        return (threats[0] if threats else 0) + (threats[1] if len(threats) > 1 else 0)


class RayOfEnfeeblement(Actoid, LimitedDurationEffect, EndOfTurnEffect, Threat):
    def __init__(self, targets, factory, **kwargs):
        Actoid.__init__(self, ActoidFlags.IS_SPELL | ActoidFlags.IS_ATTACK_LIKE)
        LimitedDurationEffect.__init__(self, factory.combatant, turns=10)
        EndOfTurnEffect.__init__(self, factory.combatant, targets, factory.saving_throw, factory.dc)
        self.targets = targets
        self.factory = factory
        self.roll_type = RollType.STRAIGHT
        self.combatant_0_name = str(self.combatants[0])  # Making a copy, because it can be deleted as combatant saves
        self.combatant_1_name = str(self.combatants[1])  # Making a copy, because it can be deleted as combatant saves

    def __str__(self):
        return f"Twinned Ray of Enfeeblement on {self.combatant_0_name} and {self.combatant_1_name}"

    def shorthand_str(self):
        return "Twinned Ray of Enfeeblement"

    def get_effect_type(self):
        return EffectType.RAY_OF_ENFEEBLEMENT

    def activate(self, **kwargs):
        Map.get().effect_tracker.add(self)
        self.factory.combatant.concentration_effect = self

    def end_of_turn(self, **kwargs):
        combatant = kwargs["combatant"]
        roll_type_modifiers = copy.copy(combatant.saving_throws_roll_type_mod[self.st])
        if combatant.has_passive(Passive.MAGIC_RESISTANCE):
            logger.info(f"{combatant} gains advantage against Hold Person through Magic Resistance")
            roll_type_modifiers.add(RollType.ADVANTAGE)
        saved = roll_saving_throw(self.combatants[0].saving_throws[self.st], self.dc, reconcile_roll_types(roll_type_modifiers))
        if saved:
            logger.info(f"{combatant} saved against {self}")
            self.combatants = [c for c in self.combatants if c is not combatant]
            return False
        logger.info(f"{combatant} failed the save against {self}")
        return True

    def deactivate(self, **kwargs):
        if not self.combatants:
            self.factory.combatant.break_concentration()
            return False
        return True

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        roll_type = RollType.STRAIGHT if not Map.get().is_enemy_adjacent(self.factory.combatant) else RollType.DISADVANTAGE
        to_hit_total_1 = self.factory.to_hit + ROLL_TYPE_DELTA[roll_type][max(0, min(self.combatants[0].ac - self.factory.to_hit, 20))]
        max_threat_1 = 0
        p_hit_1 = calc_p_hit(to_hit_total_1, self.combatants[0].ac)
        afs_1 = get_strength_based_attack_factories(self.combatants[0])
        for af in afs_1:
            dmg_inc = af.calculate_threat_to_target(self.factory.combatant) / 2
            max_threat_1 = max(dmg_inc, max_threat_1)

        to_hit_total_2 = self.factory.to_hit + ROLL_TYPE_DELTA[roll_type][max(0, min(self.combatants[1].ac - self.factory.to_hit, 20))]
        max_threat_2 = 0
        p_hit_2 = calc_p_hit(to_hit_total_2, self.combatants[1].ac)
        afs_2 = get_strength_based_attack_factories(self.combatants[1])
        for af in afs_2:
            dmg_inc = af.calculate_threat_to_target(self.factory.combatant) / 2
            max_threat_2 = max(dmg_inc, max_threat_2)

        return (p_hit_1 * max_threat_1 + p_hit_2 * max_threat_2) * ROUND_HORIZON

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        # self.calculate_threat_delta.cache_clear()
        #self.get_eligible_coords.cache_clear()

    # @map_toggled_cache_with_key(key=lambda self, modifiers, *args, **kwargs: hashkey(self.factory.name, tuple(modifiers.items()), tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    # def calculate_threat_delta(self, modifiers, *args, **kwargs):
    #     roll_type = RollType.STRAIGHT if not Map.get().is_enemy_adjacent(self.factory.combatant) else RollType.DISADVANTAGE
    #     modifiers[ThreatModifierType.ROLL_TYPE] = reconcile_roll_types({modifiers.get(ThreatModifierType.ROLL_TYPE, RollType.STRAIGHT), roll_type})
    #     return self.factory.calculate_threat_to_target_delta(self.combatants[0], modifiers, *args, **kwargs) + self.factory.calculate_threat_to_target_delta(self.combatants[1], modifiers, *args, **kwargs)

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        if get_swallower(self.factory.combatant):
            return None  # Not possible while blinded
        battle_map = Map.get()
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            coords_for_first = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.combatants[0]),
                                                                 distances,
                                                                 inflate_to_dist=self.factory.combatant.size.value,
                                                                 rng=TwinnedRayOfEnfeeblementFactory.range, combatant=self.factory.combatant)

            coords_for_second = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.combatants[1]),
                                                                  distances,
                                                                  inflate_to_dist=self.factory.combatant.size.value,
                                                                  rng=TwinnedRayOfEnfeeblementFactory.range)
            free_coords_in_range = set(coords_for_first).intersection(set(coords_for_second))

            return [coord for coord in free_coords_in_range if
                    battle_map.visibility_dict_for_all_coords[coord][self.combatants[0]] is not Visibility.NONE
                    and battle_map.visibility_dict_for_all_coords[coord][self.combatants[1]] is not Visibility.NONE]
        elif battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.combatants[0]) <= TwinnedRayOfEnfeeblementFactory.range and \
            battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.combatants[1]) <= TwinnedRayOfEnfeeblementFactory.range and \
                battle_map.visibility_dict_for_all_coords[curr_coord][self.combatants[0]] is not Visibility.NONE and \
                battle_map.visibility_dict_for_all_coords[curr_coord][self.combatants[1]] is not Visibility.NONE:
            return [curr_coord]
        return None

