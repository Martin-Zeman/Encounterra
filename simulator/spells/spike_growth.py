import logging
from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import BonusAction
from ..battle_map import Map, map_position_toggled_cache, _get_cartesian_distance_coords, \
    _get_free_coords_in_cartesian_range
from ..combatant_coords import Coords
from ..effects.aoe_spheric_effect import AoeSphericEffect
from ..effects.effect import EffectType
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..spells.spell import SpellStats
from ..misc import DamageType, avg_roll, roll_spell_dmg
from ..conditions import Conditions, is_affected_by_any, get_swallower
from ..actions.actoid import Actoid, ActoidFlags
from ..threat_interfaces import DirectThreat, AoEThreat
from ..factory_interfaces import DirectThreatFactory
import numpy as np

logger = logging.getLogger("Encounterra")

class SpikeGrowthFactory(DirectThreatFactory):
    level = 2
    range = SpellStats.Range.FEET_150.value
    target = SpellStats.Target.RADIUS_20
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL
    dmg_type = DamageType.Piercing

    def __init__(self, action_type, caster, resource):
        super().__init__()
        self.action_type = action_type  # SPIKE_GROWTH, QUICKENED_SPIKE_GROWTH
        self.dmg_dice = "2d4"
        self.combatant = caster
        self.resource = resource

    def __str__(self):
        """
        Important for FSM building
        """
        return "SpikeGrowthFactory"


    def get_ability_name(self):
        return "Spike Growth"

    def find_best_args(self, combatant):
        # TODO maybe find a smarter placement for this
        coord, _ = Map.get().find_best_placement_harmful_circular(combatant, SpikeGrowthFactory.range, SpellStats.TRANSLATE_RADIUS[SpikeGrowthFactory.target], self)
        return coord

    def create_all(self, previous_action_in_dag=None):
        # Here there really is no need to iterate over all coords. Just find the best score
        return [SpikeGrowth(self.find_best_args(self.combatant), self)]

    def create(self, coord):
        return SpikeGrowth(coord, self)

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
        return SpikeGrowth(self.find_best_args(self.combatant), self).calculate_threat()


class SpikeGrowth(Actoid, LimitedDurationEffect, AoeSphericEffect, DirectThreat, AoEThreat):

    def __init__(self, coord, factory,  **kwargs):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, factory.combatant, turns=100)
        AoeSphericEffect.__init__(self, factory.combatant, coord, SpellStats.TRANSLATE_RADIUS[SpikeGrowthFactory.target])
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_SPIKE_GROWTH else "") + f"Spike Growth at {np.squeeze(self.origin)}"

    def get_effect_type(self):
        return EffectType.SPIKE_GROWTH

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_SPIKE_GROWTH else "") + "Spike Growth"

    def on_start_of_turn(self, combatant):
        pass

    def on_end_of_turn(self, combatant):
        pass

    def on_enter(self, combatant):
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        combatant.receive_dmg(dmg, SpikeGrowthFactory.dmg_type)
        Map.get().remove_combatant_if_dead(combatant)

    def on_exit(self, combatant):
        pass

    def on_move_within(self, combatant):
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        combatant.receive_dmg(dmg, SpikeGrowthFactory.dmg_type)
        Map.get().remove_combatant_if_dead(combatant)

    # def is_affecting(self, combatant):
    #     battle_map = Map.get()
    #     coords = self.get_affected_coords()
    #     return battle_map.get_hop_distance_coords(battle_map.get_combatant_position(combatant).get(), coords) == 0

    def activate(self, **kwargs):
        Map.get().effect_tracker.add(self)
        self.factory.combatant.concentration_effect = self

    def deactivate(self):
        self.factory.combatant.break_concentration()

    def deactivate_for_combatant(self, combatant):
        assert False

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        # TODO This needs more intelligence (also subtract dmg caused to allies)
        battle_map = Map.get()
        affected = battle_map.get_combatants_affected_by_sphere_aoe(self.factory.combatant, SpikeGrowthFactory.target, SpikeGrowthFactory.type, self.coord)
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
        return 0

    def threat_on_move_within(self, target, *args, **kwargs):
        return avg_roll(self.factory.dmg_dice)

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        if get_swallower(self.factory.combatant):
            return None
        battle_map = Map.get()
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return _get_free_coords_in_cartesian_range(battle_map.grid,
                                                       Coords(self.origin).get(),  # not actually combatant coords
                                                       distances,
                                                       inflate_to_dist=self.factory.combatant.size.value,
                                                       rng=SpikeGrowthFactory.range, combatant_id=self.factory.combatant.id)
        elif _get_cartesian_distance_coords(battle_map.get_combatant_position(self.factory.combatant).get(), np.array([self.origin])) <= SpikeGrowthFactory.range:
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
        return None
