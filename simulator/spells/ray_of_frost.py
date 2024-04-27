from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import BonusAction
from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key
from ..effects.combatant_effect import CombatantEffect
from ..effects.effect import EffectType
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..spells.spell import SpellStats
from ..misc import DamageType, RollType, avg_roll, Visibility
from ..conditions import Conditions, is_affected_by_any, get_swallower
from ..actions.actoid import Actoid, FactoryFlags, ActoidFlags
from ..threat_utils import mean_dmg
from ..threat_interfaces import DirectThreat
from ..factory_interfaces import DirectThreatFactory
import logging
from ..utils.roll_types import ROLL_TYPE_CRIT_DELTA, ROLL_TYPE_DELTA, ThreatModifierType

logger = logging.getLogger("Encounterra")


class RayOfFrostFactory(DirectThreatFactory):
    level = 0
    range = SpellStats.Range.FEET_60.value
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.HARMFUL
    dc = None
    dmg_type = DamageType.Cold

    def __init__(self, to_hit, action_type, caster, resource):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.to_hit = to_hit
        self.action_type = action_type  # RAY_OF_FROST, QUICKENED_RAY_OF_FROST TODO Added twinned?
        self.dmg_dice = self.get_dmg_dice(caster.level)
        self.combatant = caster
        self.resource = resource

    def __str__(self):
        """
        Important for FSM building
        """
        return "RayOfFrostFactory"

    def get_ability_name(self):
        return "Ray of Frost"

    def get_twinned_kwargs(self):
        return {'to_hit': self.to_hit, 'caster': self.combatant, 'resource': self.resource}

    def get_quickened_kwargs(self):
        return {'to_hit': self.to_hit, 'caster': self.combatant, 'resource': self.resource}

    @staticmethod
    def get_dmg_dice(level):
        match level:
            case lvl if 1 <= lvl <= 4:
                return "1d8"
            case lvl if 5 <= lvl <= 10:
                return "2d8"
            case lvl if 11 <= lvl <= 16:
                return "3d8"
            case lvl if lvl <= 17:
                return "4d8"
            case _:
                logger.error("Incorrect caster level of Ray of Frost")
                return "1d8"

    def get_eligible_targets(self):
        swallower = get_swallower(self.combatant)
        if swallower:
            return [swallower]
        return [e for e in Map.get().get_non_swallowed_enemies(self.combatant)]

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [RayOfFrost(t, self) for t in targets]

    def create(self, target):
        return RayOfFrost(target, self)

    def calculate_threat_to_target(self, target, **kwargs):
        battle_map = Map.get()
        if get_swallower(target):
            return 0
        if battle_map.get_cartesian_distance_combatants(self.combatant, target) <= RayOfFrostFactory.range:
            roll_type = RollType.STRAIGHT if not battle_map.is_enemy_adjacent(self.combatant) else RollType.DISADVANTAGE
            to_hit_total = self.to_hit + ROLL_TYPE_DELTA[roll_type][max(0, min(target.ac - self.to_hit, 20))]
            return mean_dmg(to_hit_total, self.dmg_dice, 0, target.ac, target, RayOfFrostFactory.dmg_type, ROLL_TYPE_CRIT_DELTA[roll_type])
        return 0

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications.
        This is useful calculating the potential reduction of threat_in caused by abilities of enemies, e.g. advantage on saving throw
        against fireball or bane on attack rolls etc.
        """
        if target.is_immune_to(RayOfFrostFactory.dmg_type):
            return 0
        mod_to_hit_flat = modifiers.get(ThreatModifierType.TO_HIT_FLAT, 0)
        mod_to_hit_die = modifiers.get(ThreatModifierType.TO_HIT_DIE, '0d0')
        roll_type = modifiers.get(ThreatModifierType.ROLL_TYPE, RollType.STRAIGHT)
        target_ac = modifiers.get(ThreatModifierType.TARGET_AC, 0)

        total_target_ac = target_ac + target.ac
        to_hit_total = self.to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
        to_hit_total += ROLL_TYPE_DELTA[roll_type][max(0, min(total_target_ac - to_hit_total, 20))]
        total_crit = ROLL_TYPE_CRIT_DELTA[roll_type]

        return mean_dmg(to_hit_total, self.dmg_dice, 0, total_target_ac, target, RayOfFrostFactory.dmg_type, total_crit) - mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, target, RayOfFrostFactory.dmg_type, 1)

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        if not targets:
            return 0
        return max([self.calculate_threat_to_target(t) for t in targets])


class RayOfFrost(Actoid, DirectThreat, CombatantEffect, LimitedDurationEffect):
    def __init__(self, target, factory, **kwargs):
        Actoid.__init__(self, ActoidFlags.IS_SPELL | ActoidFlags.IS_ATTACK_LIKE)
        CombatantEffect.__init__(self, factory.combatant, [target])
        LimitedDurationEffect.__init__(self, factory.combatant, turns=1)
        self.target = target
        self.factory = factory
        self.empowered = kwargs.get("empowered", False)
        self.roll_type = RollType.STRAIGHT

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_RAY_OF_FROST else "") + f"Ray of Frost on {self.target}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_RAY_OF_FROST else "") + "Ray of Frost"

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        roll_type = RollType.STRAIGHT if not Map.get().is_enemy_adjacent(self.factory.combatant) else RollType.DISADVANTAGE
        to_hit_total = self.factory.to_hit + ROLL_TYPE_DELTA[roll_type][max(0, min(self.target.ac - self.factory.to_hit, 20))]
        return mean_dmg(to_hit_total, self.factory.dmg_dice, 0, self.target.ac, self.target, RayOfFrostFactory.dmg_type, ROLL_TYPE_CRIT_DELTA[roll_type])

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        self.calculate_threat_delta.cache_clear()
        #self.get_eligible_coords.cache_clear()

    @map_toggled_cache_with_key(key=lambda self, modifiers, *args, **kwargs: hashkey(self.factory.name, tuple(modifiers.items()), tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return self.factory.calculate_threat_to_target_delta(self.target, modifiers, *args, **kwargs)

    def get_effect_type(self):
        return EffectType.RAY_OF_FROST

    def activate(self, **kwargs):
        Map.get().effect_tracker.add(self)
        self.factory.combatant.concentration_effect = self
        logger.error(f"{self.combatants[0]}'s speed is reduced by 10")
        self.combatants[0].speed -= 10

    def deactivate(self):
        self.factory.combatant.break_concentration()
        logger.error(f"{self.combatants[0]}'s speed returns to normal")
        self.combatants[0].speed += 10

    def deactivate_for_combatant(self, combatant):
        assert False

    def is_affecting(self, combatant):
        return combatant is self.combatants[0]

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
            free_coords_in_range = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.target),
                                                                 distances,
                                                                 inflate_to_dist=self.factory.combatant.size.value,
                                                                 rng=RayOfFrostFactory.range, combatant=self.factory.combatant)
            return [coord for coord in free_coords_in_range if battle_map.visibility_dict_for_all_coords[coord][self.target] is not Visibility.NONE]
        elif battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.target) <= RayOfFrostFactory.range and \
                battle_map.visibility_dict_for_all_coords[curr_coord][self.target] is not Visibility.NONE:
            return [curr_coord]
        return None

