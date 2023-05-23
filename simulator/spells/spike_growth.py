from functools import cache

from simulator.actions.action_types import BonusAction
from simulator.combatant_coords import CombatantCoords
from simulator.effects.aoe_spheric_effect import AoeSphericEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, avg_roll, roll_spell_dmg
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.threat_interfaces import DirectThreat, DirectThreatFactory, AoEThreat
import numpy as np

class SpikeGrowthFactory(DirectThreatFactory):
    level = 2
    range = SpellStats.Range.FEET_150.value
    target = SpellStats.Target.RADIUS_20
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL
    dmg_type = DamageType.Piercing

    def __init__(self, action_type, caster, **kwargs):
        super().__init__()
        self.action_type = action_type  # SPIKE_GROWTH, QUICKENED_SPIKE_GROWTH
        self.dmg_dice = "2d4"
        self.caster = caster


    def __str__(self):
        """
        Important for FSM building
        """
        return "SpikeGrowthFactory"

    def find_best_args(self, combatant, battle_map):
        # TODO maybe find a smarter placement for this
        coord, _, _ = battle_map.find_best_placement_harmful_circular(combatant, SpikeGrowthFactory.range, SpellStats.TRANSLATE_RADIUS[SpikeGrowthFactory.target])
        return coord

    def create_best(self, combatant, battle_map, **kwargs):
        return SpikeGrowth(self.find_best_args(combatant, battle_map), self,  **kwargs)

    def create_all(self, battle_map):
        # Here there really is no need to iterate over all coords. Just find the best score
        return [SpikeGrowth(self.find_best_args(self.caster, battle_map), self)]

    def create(self, coord):
        return SpikeGrowth(coord, self)

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        Calculates threat to one specific target
        """
        try:
            consider_dist = kwargs["consider_dist"]
        except KeyError:
            consider_dist = False

        if not consider_dist or battle_map.get_cartesian_distance(self.caster, target) <= SpikeGrowthFactory.range + SpellStats.TRANSLATE_RADIUS[SpikeGrowthFactory.target]:
            return avg_roll(self.dmg_dice)
        return 0

    def calculate_threat_to_target_delta(self, battle_map, target, modified_stats, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0 # No need


class SpikeGrowth(Actoid, LimitedDurationEffect, AoeSphericEffect, DirectThreat, AoEThreat):

    def __init__(self, coord, factory,  **kwargs):
        super().__init__(actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_DIRECT_THREAT)
        LimitedDurationEffect.__init__(self, turns=100)
        AoeSphericEffect.__init__(self, coord, SpellStats.TRANSLATE_RADIUS[SpikeGrowthFactory.target])
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_SPIKE_GROWTH else "") + f"Spike Growth at {np.squeeze(self.coord)}"


    def on_start_of_turn(self, combatant):
        pass

    def on_end_of_turn(self, combatant):
        pass

    def on_enter(self, combatant):
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        combatant.receive_dmg(dmg, SpikeGrowthFactory.dmg_type)

    def on_move_within(self, combatant):
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        combatant.receive_dmg(dmg, SpikeGrowthFactory.dmg_type)

    def is_affecting(self, combatant, battle_map):
        coords = self.get_affected_coords(battle_map)
        return battle_map.get_hop_distance(combatant, coords) == 0


    def activate(self, battle_map):
        pass

    def deactivate(self, battle_map):
        pass  # TODO remove concentration?


    def clear_cache(self):
        self.calculate_threat.cache_clear()

    @cache
    def calculate_threat(self, combatant, battle_map, combatant_coords: CombatantCoords = None, *args, **kwargs):
        # TODO This needs more intelligence (also subtract dmg caused to allies)
        affected = battle_map.get_combatants_affected_by_aoe_with_caster_mock_position(self.factory.caster, combatant_coords, SpikeGrowthFactory.target, SpikeGrowthFactory.type, self.coord)
        acc = 0
        for aff in affected:
            if battle_map.teams.are_enemies(self.factory.caster, aff):
                acc += avg_roll(self.factory.dmg_dice)
            else:
                acc -= avg_roll(self.factory.dmg_dice)
        return acc

    def calculate_threat_mod(self, battle_map, modified_stats, *args, **kwargs):
        return 0  # Not relevant for this ability

    def threat_on_end_of_turn(self, battle_map, target, *args, **kwargs):
        return 0

    def threat_on_enter(self, battle_map, target, *args, **kwargs):
        return avg_roll(self.factory.dmg_dice)

    def threat_on_start_of_turn(self, battle_map, target, *args, **kwargs):
        return 0

    def threat_on_move_within(self, battle_map, target, *args, **kwargs):
        return avg_roll(self.factory.dmg_dice)

    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        return battle_map.get_free_coords_in_cartesian_range(CombatantCoords(self.coord),  # not actually combatant coords
                                                             distances,
                                                             inflate_to_size=self.factory.caster.size,
                                                             rng=SpikeGrowthFactory.range, combatant=self.factory.caster)

    def is_current_coord_eligible(self, battle_map):
        return battle_map.get_cartesian_distance(self.factory.caster, np.array([self.coord])) <= SpikeGrowthFactory.range