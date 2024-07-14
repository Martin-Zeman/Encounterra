import copy

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import BonusAction, Passive
from ..battle_map import Map, map_position_toggled_cache, _get_free_coords_in_cartesian_range
from ..effects.effect import EffectType
from ..effects.end_of_turn_combatant_effect import EndOfTurnEffect
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..spells.spell import SpellStats
from ..misc import RollType, _avg_roll, Visibility, SavingThrow, reconcile_roll_types, \
    roll_saving_throw, get_strength_based_attack_factories, ROUND_HORIZON
from ..conditions import Conditions, is_affected_by_any, get_swallower
from ..actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import cache
from ..threat_utils import calc_p_hit
from ..threat_interfaces import Threat
from ..factory_interfaces import DirectThreatFactory
import logging
from ..utils.roll_types import ROLL_TYPE_DELTA, ThreatModifierType

logger = logging.getLogger("Encounterra")


class RayOfEnfeeblementFactory(DirectThreatFactory):
    level = 2
    range = SpellStats.Range.FEET_60.value
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.MINUTE
    concentration = True
    type = SpellStats.Type.HARMFUL
    dmg_type = None

    def __init__(self, action_type, caster, resource):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.flags |= FactoryFlags.PREVENT_ENDLESS_RECURSION
        self.to_hit = caster.spell_to_hit
        self.dc = caster.dc
        self.action_type = action_type  # RAY_OF_ENFEEBLEMENT, TWINNED_RAY_OF_ENFEEBLEMENT, QUICKENED_RAY_OF_ENFEEBLEMENT
        self.dmg_dice = ((0, 0),)
        self.combatant = caster
        self.resource = resource
        self.saving_throw = SavingThrow.CON

    def __str__(self):
        """
        Important for FSM building
        """
        return "RayOfEnfeeblementFactory"

    def get_ability_name(self):
        return "Ray of Enfeeblement"

    def get_twinned_kwargs(self):
        return {'caster': self.combatant, 'resource': self.resource}

    def get_quickened_kwargs(self):
        return {'caster': self.combatant, 'resource': self.resource}

    def get_eligible_targets(self):
        swallower = get_swallower(self.combatant)
        if swallower:
            return [swallower]
        return [e for e in Map.get().get_non_swallowed_enemies(self.combatant)]

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [RayOfEnfeeblement(t, self) for t in targets]

    def create(self, target):
        return RayOfEnfeeblement(target, self)

    def calculate_threat_to_target(self, target, **kwargs):
        max_threat = 0
        p_hit = calc_p_hit(self.to_hit, target.ac)
        afs = get_strength_based_attack_factories(target)
        for af in (a for a in afs if FactoryFlags.PREVENT_ENDLESS_RECURSION not in a.flags):
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
        mod_to_hit_die = modifiers.get(ThreatModifierType.TO_HIT_DIE, (0, 0))
        target_ac = modifiers.get(ThreatModifierType.TARGET_AC, 0)
        roll_type = modifiers.get(ThreatModifierType.ROLL_TYPE, RollType.STRAIGHT)

        total_target_ac = target.ac + target_ac
        to_hit_total = self.to_hit + mod_to_hit_flat + _avg_roll(mod_to_hit_die)
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
        targets = self.get_eligible_targets()
        if not targets:
            return 0
        return max([self.calculate_threat_to_target(t) for t in targets])


class RayOfEnfeeblement(Actoid, LimitedDurationEffect, EndOfTurnEffect, Threat):
    def __init__(self, target, factory, **kwargs):
        Actoid.__init__(self, ActoidFlags.IS_SPELL | ActoidFlags.IS_ATTACK_LIKE)
        LimitedDurationEffect.__init__(self, factory.combatant, turns=10)
        EndOfTurnEffect.__init__(self, factory.combatant, [target], factory.saving_throw, factory.dc)
        self.target = target
        self.factory = factory
        self.roll_type = RollType.STRAIGHT

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_RAY_OF_ENFEEBLEMENT else "") + f"Ray of Enfeeblement on {self.target}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_RAY_OF_ENFEEBLEMENT else "") + "Ray of Enfeeblement"

    def get_effect_type(self):
        return EffectType.RAY_OF_ENFEEBLEMENT

    def activate(self, **kwargs):
        Map.get().effect_tracker.add(self)
        self.factory.combatant.concentration_effect = self

    def combatant_saved_at_end_of_turn(self, combatant):
        roll_type_modifiers = copy.copy(combatant.saving_throws_roll_type_mod[self.st])
        if combatant.has_passive(Passive.MAGIC_RESISTANCE):
            logger.info(f"{combatant} gains advantage against Hold Person through Magic Resistance")
            roll_type_modifiers.add(RollType.ADVANTAGE)
        saved = roll_saving_throw(combatant.saving_throws[self.st], self.dc, reconcile_roll_types(roll_type_modifiers))
        if saved:
            logger.info(f"{combatant} saved against {self}")
            return False
        logger.info(f"{combatant} failed the save against {self}")
        return True

    def deactivate(self):
        self.factory.combatant.break_concentration()

    def deactivate_for_combatant(self, combatant):
        assert False

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        roll_type = RollType.STRAIGHT if not Map.get().is_enemy_adjacent(self.factory.combatant) else RollType.DISADVANTAGE
        to_hit_total = self.factory.to_hit + ROLL_TYPE_DELTA[roll_type][max(0, min(self.target.ac - self.factory.to_hit, 20))]
        max_threat = 0
        p_hit = calc_p_hit(to_hit_total, self.target.ac)
        afs = get_strength_based_attack_factories(self.target)
        for af in (a for a in afs if FactoryFlags.PREVENT_ENDLESS_RECURSION not in a.flags):
            dmg_inc = af.calculate_threat_to_target(self.factory.combatant) / 2
            max_threat = max(dmg_inc, max_threat)
        return p_hit * max_threat * ROUND_HORIZON

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        # self.calculate_threat_delta.cache_clear()
        #self.get_eligible_coords.cache_clear()

    # @map_toggled_cache_with_key(key=lambda self, modifiers, *args, **kwargs: hashkey(self.factory.name, tuple(modifiers.items()), tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    # def calculate_threat_delta(self, modifiers, *args, **kwargs):
    #     roll_type = RollType.STRAIGHT if not Map.get().is_enemy_adjacent(self.factory.combatant) else RollType.DISADVANTAGE
    #     modifiers[ThreatModifierType.ROLL_TYPE] = reconcile_roll_types({modifiers.get(ThreatModifierType.ROLL_TYPE, RollType.STRAIGHT), roll_type})
    #     return self.factory.calculate_threat_to_target_delta(self.target, modifiers, *args, **kwargs)

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        swallower = get_swallower(self.factory.combatant)
        battle_map = Map.get()
        if swallower:
            if swallower is self.target:
                return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
            return None
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            free_coords_in_range = _get_free_coords_in_cartesian_range(
                battle_map.grid,
                battle_map.get_combatant_position(self.target).get(),
                distances,
                inflate_to_dist=self.factory.combatant.size.value,
                rng=RayOfEnfeeblementFactory.range, combatant_id=self.factory.combatant.id)
            return [coord for coord in free_coords_in_range if battle_map.visibility_dict_for_all_coords[coord][self.target] is not Visibility.NONE]
        elif battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.target) <= RayOfEnfeeblementFactory.range and \
                battle_map.visibility_dict_for_all_coords[curr_coord][self.target] is not Visibility.NONE:
            return [curr_coord]
        return None

