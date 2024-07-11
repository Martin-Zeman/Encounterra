from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import BonusAction
from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key, \
    _get_free_coords_in_cartesian_range
from ..spells.spell import SpellStats
from ..misc import DamageType, Visibility
from ..conditions import Conditions, is_affected_by_any, is_affected_by, get_swallower
from ..actions.actoid import Actoid, ActoidFlags
from ..threat_utils import mean_dmg_auto_hit
from ..threat_interfaces import DirectThreat
from ..factory_interfaces import DirectThreatFactory
from itertools import combinations_with_replacement
import logging
from ..utils.roll_types import RollType

logger = logging.getLogger("Encounterra")

class MagicMissileFactory(DirectThreatFactory):
    level = 1
    range = SpellStats.Range.FEET_120.value
    target = SpellStats.Target.THREE_CREATURES
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.HARMFUL
    dc = None
    dmg_type = DamageType.Force

    def __init__(self, action_type, caster, resource):
        super().__init__()
        self.action_type = action_type  # MAGIC_MISSILE, QUICKENED_MAGIC_MISSILE
        self.dmg_dice = ((1, 4),)
        self.dmg_bonus = 1
        self.combatant = caster
        self.resource = resource

    def __str__(self):
        """
        Important for FSM building
        """
        return "MagicMissileFactory"

    def get_ability_name(self):
        return "Magic Missile"


    def get_quickened_kwargs(self):
        return {'caster': self.combatant, 'resource': self.resource}

    def get_eligible_targets(self):
        swallower = get_swallower(self.combatant)
        if swallower:
            return [swallower, swallower, swallower]
        # Range is so big that it doesn't matter
        return combinations_with_replacement([e for e in Map.get().get_non_swallowed_enemies(self.combatant)], 3)

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [MagicMissile(t, self) for t in targets]

    def create(self, targets):
        return MagicMissile(targets, self)

    def calculate_threat_to_target(self, target, **kwargs):
        battle_map = Map.get()
        if battle_map.get_cartesian_distance_combatants(self.combatant, target) <= MagicMissileFactory.range:
            ret = 3 * (mean_dmg_auto_hit(self.dmg_dice, target.is_resistant_to(MagicMissileFactory.dmg_type)) + self.dmg_bonus)
            return ret
        else:
            return 0

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications.
        This is useful calculating the potential reduction of threat_in caused by abilities of enemies, e.g. advantage on saving throw
        against fireball or bane on attack rolls etc.
        """
        return 0

    def calculate_max_threat(self):
        if get_swallower(self.combatant):
            return 0  # Must be able to see
        targets = [e for e in Map.get().get_non_swallowed_enemies(self.combatant)]
        for t in targets:
            threat = self.calculate_threat_to_target(t)
            # We just need one enemy within range which assures we can deal the damage (which is target-agnostic)
            if threat:
                return threat
        return 0


class MagicMissile(Actoid, DirectThreat):

    def __init__(self, targets, factory, **kwargs):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        self.targets = targets
        self.factory = factory
        self.empowered = kwargs.get("empowered", False)
        self.roll_type = RollType.STRAIGHT

    def __str__(self):
        if self.targets[0] is self.targets[1] and self.targets[1] is self.targets[2]:
            return (
                "Quickened " if self.factory.action_type is BonusAction.QUICKENED_SCORCHING_RAY else "") + f"Magic Missile on 3x{self.targets[0]}"
        elif self.targets[0] is self.targets[1]:
            return (
                "Quickened " if self.factory.action_type is BonusAction.QUICKENED_SCORCHING_RAY else "") + f"Magic Missile on 2x{self.targets[0]} and {self.targets[2]}"
        elif self.targets[1] is self.targets[2]:
            return (
                "Quickened " if self.factory.action_type is BonusAction.QUICKENED_SCORCHING_RAY else "") + f"Magic Missile on 2x{self.targets[1]} and {self.targets[0]}"
        elif self.targets[0] is self.targets[2]:
            return (
                "Quickened " if self.factory.action_type is BonusAction.QUICKENED_SCORCHING_RAY else "") + f"Magic Missile on 2x{self.targets[0]} and {self.targets[1]}"
        return (
            "Quickened " if self.factory.action_type is BonusAction.QUICKENED_SCORCHING_RAY else "") + f"Magic Missile on {self.targets[0]}, {self.targets[1]} and {self.targets[2]}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_MAGIC_MISSILE else "") + "Magic Missile"

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        dmg_acc = mean_dmg_auto_hit(self.factory.dmg_dice, self.targets[0].is_resistant_to(MagicMissileFactory.dmg_type)) + self.factory.dmg_bonus
        dmg_acc += mean_dmg_auto_hit(self.factory.dmg_dice, self.targets[1].is_resistant_to(MagicMissileFactory.dmg_type)) + self.factory.dmg_bonus
        dmg_acc += mean_dmg_auto_hit(self.factory.dmg_dice, self.targets[2].is_resistant_to(MagicMissileFactory.dmg_type)) + self.factory.dmg_bonus
        return dmg_acc

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        #self.get_eligible_coords.cache_clear()

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if get_swallower(self.factory.combatant):
            return None  # Must be able to see
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            coords_for_first = set(_get_free_coords_in_cartesian_range(
                battle_map.grid,
                battle_map.get_combatant_position(self.targets[0]).get(),
                distances,
                inflate_to_dist=self.factory.combatant.size.value,
                rng=MagicMissileFactory.range,
                combatant_id=self.factory.combatant.id))
            coords_for_second = set(_get_free_coords_in_cartesian_range(
                battle_map.grid,
                battle_map.get_combatant_position(self.targets[1]).get(),
                distances,
                inflate_to_dist=self.factory.combatant.size.value,
                rng=MagicMissileFactory.range,
                combatant_id=self.factory.combatant.id))
            coords_for_third = set(_get_free_coords_in_cartesian_range(
                battle_map.grid,
                battle_map.get_combatant_position(self.targets[2]).get(),
                distances,
                inflate_to_dist=self.factory.combatant.size.value,
                rng=MagicMissileFactory.range,
                combatant_id=self.factory.combatant.id))
            free_coords_in_range = coords_for_third.intersection(coords_for_first.intersection(coords_for_second))

            return [coord for coord in free_coords_in_range if battle_map.visibility_dict_for_all_coords[coord][self.targets[0]] is not Visibility.NONE
                    and battle_map.visibility_dict_for_all_coords[coord][self.targets[1]] is not Visibility.NONE
                    and battle_map.visibility_dict_for_all_coords[coord][self.targets[2]] is not Visibility.NONE]
        elif battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.targets[0]) <= MagicMissileFactory.range \
            and battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.targets[1]) <= MagicMissileFactory.range \
            and battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.targets[2]) <= MagicMissileFactory.range \
            and battle_map.visibility_dict_for_all_coords[curr_coord][self.targets[0]] is not Visibility.NONE \
            and battle_map.visibility_dict_for_all_coords[curr_coord][self.targets[1]] is not Visibility.NONE \
                and battle_map.visibility_dict_for_all_coords[curr_coord][self.targets[2]] is not Visibility.NONE:
            return [curr_coord]
        return None
