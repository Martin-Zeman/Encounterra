from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import BonusAction
from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key
from ..combatant_coords import Coords
from ..effects.aoe_square_effect import AoeSquareEffect
from ..effects.effect import EffectType
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..spells.spell import SpellStats
from ..misc import DamageType, avg_roll, roll_spell_dmg, Conditions
from ..actions.actoid import Actoid, ActoidFlags
from ..threat_interfaces import DirectThreat, DirectThreatFactory, AoEThreat
import numpy as np

class CloudOfDaggersFactory(DirectThreatFactory):
    level = 2
    range = SpellStats.Range.FEET_60.value
    target = SpellStats.Target.BOX_5
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL
    dmg_type = DamageType.Slashing

    def __init__(self, action_type, caster, **kwargs):
        super().__init__()
        self.action_type = action_type  # SPIKE_GROWTH, QUICKENED_SPIKE_GROWTH
        self.dmg_dice = "4d4"
        self.combatant = caster


    def __str__(self):
        """
        Important for FSM building
        """
        return "CloudOfDaggersFactory"


    def get_ability_name(self):
        return "Cloud of Daggers"


    def find_best_args(self, combatant):
        # TODO maybe find a smarter placement for this
        coord, _, _ = Map.get().find_best_placement_harmful_square(self.combatant, CloudOfDaggersFactory.range, 1)
        return coord

    def create_all(self):
        # Here there really is no need to iterate over all coords. Just find the best score
        return [CloudOfDaggers(self.find_best_args(self.combatant), self)]

    def create(self, coord):
        return CloudOfDaggers(coord, self)

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates threat to one specific target
        """
        return avg_roll(self.dmg_dice)

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0  # No need

    def calculate_max_threat(self):
        return CloudOfDaggers(self.find_best_args(self.combatant), self).calculate_threat()

class CloudOfDaggers(Actoid, LimitedDurationEffect, AoeSquareEffect, DirectThreat, AoEThreat):

    def __init__(self, coord, factory,  **kwargs):
        super().__init__(actoid_flags=ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, factory.combatant, turns=10)
        AoeSquareEffect.__init__(self, factory.combatant, coord, SpellStats.TRANSLATE_BOX[CloudOfDaggersFactory.target])
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_CLOUD_OF_DAGGERS else "") + f"Cloud of Daggers at {np.squeeze(self.origin)}"

    def get_effect_type(self):
        return EffectType.CLOUD_OF_DAGGERS

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_CLOUD_OF_DAGGERS else "") + f"Cloud of Daggers"

    def on_start_of_turn(self, combatant):
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        combatant.receive_dmg(dmg, CloudOfDaggersFactory.dmg_type)

    def on_end_of_turn(self, combatant):
        pass

    def on_enter(self, combatant):
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        combatant.receive_dmg(dmg, CloudOfDaggersFactory.dmg_type)

    def on_move_within(self, combatant):
        return 0

    def on_exit(self, combatant):
        pass

    def is_affecting(self, combatant):
        coords = self.get_affected_coords()
        battle_map = Map.get()
        return battle_map.get_hop_distance_coords(battle_map.get_combatant_position(combatant).get(), coords) == 0

    def activate(self):
        Map.get().effect_tracker.add(self)
        self.factory.combatant.concentration_effect = self

    def deactivate(self):
        self.factory.combatant.break_concentration()

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        battle_map = Map.get()
        affected = battle_map.get_combatants_affected_by_aoe(self.factory.combatant, CloudOfDaggersFactory.target, CloudOfDaggersFactory.type, self.origin)
        acc = 0
        for aff in affected:
            acc += (1 if battle_map.teams.are_enemies(self.factory.combatant, aff) else -3) * avg_roll(self.factory.dmg_dice)
        return acc

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        #self.get_eligible_coords.cache_clear()

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0  # Not relevant for this ability

    def threat_on_end_of_turn(self, target, *args, **kwargs):
        return 0

    def threat_on_enter(self, target, *args, **kwargs):
        return avg_roll(self.factory.dmg_dice)

    def threat_on_start_of_turn(self, target, *args, **kwargs):
        return avg_roll(self.factory.dmg_dice)

    def threat_on_move_within(self, target, *args, **kwargs):
        return 0

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if self.factory.combatant.get_swallower():
            return None
        if not self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return battle_map.get_free_coords_in_cartesian_range(Coords(self.origin),  # not actually combatant coords
                                                                 distances,
                                                                 inflate_to_size=self.factory.combatant.size,
                                                                 rng=CloudOfDaggersFactory.range, combatant=self.factory.combatant)
        elif battle_map.get_cartesian_distance_coords(battle_map.get_combatant_position(self.factory.combatant).get(), np.array([self.origin])) <= CloudOfDaggersFactory.range:
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
        return None

