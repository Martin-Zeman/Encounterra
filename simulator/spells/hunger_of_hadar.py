from functools import cache
from simulator.action_resolver import resolve_dmg_saving_throw
from simulator.actions.action_types import BonusAction
from simulator.battle_map import Map, map_position_toggled_cache
from simulator.combatant_coords import Coords
from simulator.effects.aoe_spheric_effect import AoeSphericEffect
from simulator.effects.effect import EffectType
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.spells.spell import SpellStats
from simulator.misc import SavingThrow, DamageType, avg_roll, roll_spell_dmg, Conditions, ConditionWithoutDC
from simulator.actions.actoid import Actoid, ActoidFlags, FactoryFlags
from simulator.threat_utils import mean_dmg_dc_attack
from simulator.threat_interfaces import DirectThreat, DirectThreatFactory, AoEThreat
import numpy as np

class HungerOfHadarFactory(DirectThreatFactory):
    level = 3
    range = SpellStats.Range.FEET_150.value
    target = SpellStats.Target.RADIUS_20
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL
    dmg_type = DamageType.Cold

    def __init__(self, dc, action_type, caster, **kwargs):
        super().__init__()
        self.flags |= FactoryFlags.DEX_SAVE_APPLIES
        self.dc = dc
        self.action_type = action_type  # HUNGER_OF_HADAR, QUICKENED_HUNGER_OF_HADAR
        self.saving_throw = SavingThrow.DEX
        self.dmg_dice = "2d6"
        self.combatant = caster


    def __str__(self):
        """
        Important for FSM building
        """
        return "HungerOfHadarFactory"

    def find_best_args(self, combatant):
        # TODO Deprecated
        battle_map = Map.get()
        coord, _ = battle_map.find_best_placement_harmful_circular(combatant, HungerOfHadarFactory.range, SpellStats.TRANSLATE_RADIUS[HungerOfHadarFactory.target], self)
        return coord

    def create_all(self):
        # Here there really is no need to iterate over all coords. Just find the best score
        return [HungerOfHadar(self.find_best_args(self.combatant), self)]

    def create(self, coord):
        return HungerOfHadar(coord, self)

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates threat to one specific target
        """
        # The 0.5 is a heuristic which expresses the fact that most targets would leave the area immediately
        return avg_roll(self.dmg_dice) + 0.5 * mean_dmg_dc_attack(self.dc, self.dmg_dice, False, target.saving_throws[self.saving_throw])

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0 # No need


class HungerOfHadar(Actoid, LimitedDurationEffect, AoeSphericEffect, DirectThreat, AoEThreat):

    def __init__(self, coord, factory,  **kwargs):
        super().__init__(actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_DIRECT_THREAT)
        LimitedDurationEffect.__init__(self, turns=10)
        AoeSphericEffect.__init__(self, coord, SpellStats.TRANSLATE_RADIUS[HungerOfHadarFactory.target])
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_HUNGER_OF_HADAR else "") + f"Hunger Of Hadar at {np.squeeze(self.origin)}"

    def get_effect_type(self):
        return EffectType.HUNGER_OF_HADAR

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_HUNGER_OF_HADAR else "") + "Hunger Of Hadar"


    def on_start_of_turn(self, combatant):
        combatant.apply_condition(ConditionWithoutDC(Conditions.BLINDED, self))
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        combatant.receive_dmg(dmg, self.dmg_type)

    def on_end_of_turn(self, combatant):
        combatant.apply_condition(ConditionWithoutDC(Conditions.BLINDED, self))
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        self.dmg_type = DamageType.Acid
        resolve_dmg_saving_throw(self, dmg, combatant)
        self.dmg_type = DamageType.Cold

    def on_enter(self, combatant):
        combatant.apply_condition(ConditionWithoutDC(Conditions.BLINDED, self))

    def on_move_within(self, combatant):
        pass

    def on_exit(self, combatant):
        combatant.remove_condition(Conditions.BLINDED, self)

    def is_affecting(self, combatant):
        battle_map = Map.get()
        coords = self.get_affected_coords()
        return battle_map.get_hop_distance(combatant, coords) == 0


    def activate(self):
        Map.get().effect_tracker.add(self)
        self.factory.combatant.concentration_effect = self
        # TODO make the area difficult terrain

    def deactivate(self):
        # TODO remove difficult terrain
        self.factory.combatant.break_concentration()

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        battle_map = Map.get()
        affected = battle_map.get_combatants_affected_by_aoe(self.factory.combatant, HungerOfHadarFactory.target, HungerOfHadarFactory.type, self.origin)
        acc = 0
        for aff in affected:
            acc += avg_roll(self.factory.dmg_dice)  # the initial cold dmg
            # The 0.5 is a heuristic which expresses the fact that most targets would leave the area immediately
            acc += 0.5 * mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, False, aff.saving_throws[self.factory.saving_throw], aff.is_resistant_to(DamageType.Acid))
            acc *= (1 if battle_map.teams.are_enemies(self.factory.combatant, aff) else -3)
        return acc

    def clear_cache(self):
        self.calculate_threat.cache_clear()

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0  # Not relevant for this ability

    def threat_on_end_of_turn(self, target, *args, **kwargs):
        return mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, False, target.saving_throws[self.factory.saving_throw], target.is_resistant_to(DamageType.Acid))

    def threat_on_enter(self, target, *args, **kwargs):
        return 0

    def threat_on_start_of_turn(self, target, *args, **kwargs):
        threat = avg_roll(self.factory.dmg_dice)
        return threat if not target.is_resistant_to(self.dmg_type) else threat / 2

    def threat_on_move_within(self, target, *args, **kwargs):
        return 0

    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        return battle_map.get_free_coords_in_cartesian_range(Coords(self.origin),  # not actually combatant coords
                                                             distances,
                                                             inflate_to_size=self.factory.combatant.size,
                                                             rng=HungerOfHadarFactory.range, combatant=self.factory.combatant)

    def is_current_coord_eligible(self):
        if self.factory.combatant.get_swallower():
            return False
        battle_map = Map.get()
        return battle_map.get_cartesian_distance(self.factory.combatant, np.array([self.origin])) <= HungerOfHadarFactory.range
