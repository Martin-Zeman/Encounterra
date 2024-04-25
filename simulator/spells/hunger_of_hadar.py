from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..action_resolver import resolve_dmg_saving_throw
from ..actions.action_types import BonusAction
from ..battle_map import Map, map_position_toggled_cache
from ..combatant_coords import Coords
from ..effects.aoe_spheric_effect import AoeSphericEffect
from ..effects.effect import EffectType
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..spells.spell import SpellStats
from ..misc import SavingThrow, DamageType, avg_roll, roll_spell_dmg
from ..conditions import Conditions, Condition, is_affected_by_any, get_swallower, apply_condition, \
    remove_condition
from ..actions.actoid import Actoid, ActoidFlags, FactoryFlags
from ..threat_utils import mean_dmg_dc_attack
from ..threat_interfaces import DirectThreat, AoEThreat
from ..factory_interfaces import DirectThreatFactory
import numpy as np


class HungerOfHadarFactory(DirectThreatFactory):
    level = 3
    range = SpellStats.Range.FEET_150.value
    target = SpellStats.Target.RADIUS_20
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL

    def __init__(self, dc, action_type, caster, resource):
        super().__init__()
        self.flags |= FactoryFlags.DEX_SAVE_APPLIES
        self.dc = dc
        self.action_type = action_type  # HUNGER_OF_HADAR, QUICKENED_HUNGER_OF_HADAR
        self.saving_throw = SavingThrow.DEX
        self.dmg_dice = "2d6"
        self.combatant = caster
        self.resource = resource
        self.dmg_type = DamageType.Cold

    def __str__(self):
        """
        Important for FSM building
        """
        return "HungerOfHadarFactory"

    def get_ability_name(self):
        return "Hunger of Hadar"

    def find_best_args(self, combatant):
        # TODO Deprecated
        battle_map = Map.get()
        coord, _ = battle_map.find_best_placement_harmful_circular(combatant, HungerOfHadarFactory.range, SpellStats.TRANSLATE_RADIUS[HungerOfHadarFactory.target], self)
        return coord

    def create_all(self, previous_action_in_dag=None):
        # Here there really is no need to iterate over all coords. Just find the best score
        return [HungerOfHadar(self.find_best_args(self.combatant), self)]

    def create(self, coord):
        return HungerOfHadar(coord, self)

    def calculate_max_threat(self):
        return HungerOfHadar(self.find_best_args(self.combatant), self).calculate_threat()

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates threat to one specific target
        """
        # The 0.5 is a heuristic which expresses the fact that most targets would leave the area immediately
        mean_dmg = min(target.curr_hp, mean_dmg_dc_attack(self.dc, self.dmg_dice, False, target.saving_throws[self.saving_throw], target.is_resistant_to(DamageType.Acid)))
        return avg_roll(self.dmg_dice) + 0.5 * mean_dmg

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0 # No need


class HungerOfHadar(Actoid, LimitedDurationEffect, AoeSphericEffect, DirectThreat, AoEThreat):

    def __init__(self, coord, factory,  **kwargs):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, factory.combatant, turns=10)
        AoeSphericEffect.__init__(self, factory.combatant, coord, SpellStats.TRANSLATE_RADIUS[HungerOfHadarFactory.target])
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_HUNGER_OF_HADAR else "") + f"Hunger Of Hadar at {np.squeeze(self.origin)}"

    def get_effect_type(self):
        return EffectType.HUNGER_OF_HADAR

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_HUNGER_OF_HADAR else "") + "Hunger Of Hadar"

    def on_start_of_turn(self, combatant):
        apply_condition(combatant, Condition(Conditions.BLINDED, self.factory.combatant, self))
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        combatant.receive_dmg(dmg, self.factory.dmg_type)
        Map.get().remove_combatant_if_dead(combatant)

    def on_end_of_turn(self, combatant):
        apply_condition(combatant, Condition(Conditions.BLINDED, self.factory.combatant, self))
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        self.factory.dmg_type = DamageType.Acid
        resolve_dmg_saving_throw(self, dmg, combatant, False, True)
        self.factory.dmg_type = DamageType.Cold

    def on_enter(self, combatant):
        apply_condition(combatant, Condition(Conditions.BLINDED, self.factory.combatant, self))

    def on_move_within(self, combatant):
        pass

    def on_exit(self, combatant):
        remove_condition(combatant, Conditions.BLINDED, self.factory.combatant)

    # def is_affecting(self, combatant):
    #     battle_map = Map.get()
    #     coords = self.get_affected_coords()
    #     return battle_map.get_hop_distance_coords(battle_map.get_combatant_position(combatant).get(), coords) == 0

    def activate(self, **kwargs):
        Map.get().effect_tracker.add(self)
        self.factory.combatant.concentration_effect = self
        # TODO make the area difficult terrain

    def deactivate(self):
        # TODO remove difficult terrain
        self.factory.combatant.break_concentration()

    def deactivate_for_combatant(self, combatant):
        assert False

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        battle_map = Map.get()
        affected = battle_map.get_combatants_affected_by_sphere_aoe(self.factory.combatant, HungerOfHadarFactory.target, HungerOfHadarFactory.type, self.origin)
        acc = 0
        for aff in affected:
            acc += avg_roll(self.factory.dmg_dice)  # the initial cold dmg
            # The 0.5 is a heuristic which expresses the fact that most targets would leave the area immediately
            mean_dmg = min(aff.curr_hp, mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, False, aff.saving_throws[self.factory.saving_throw], aff.is_resistant_to(DamageType.Acid)))
            acc += 0.5 * mean_dmg
            acc *= (1 if battle_map.teams.are_enemies(self.factory.combatant, aff) else -3)
        return acc

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        #self.get_eligible_coords.cache_clear()

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0  # Not relevant for this ability

    def threat_on_end_of_turn(self, target, *args, **kwargs):
        return min(target.curr_hp, mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, False, target.saving_throws[self.factory.saving_throw], target.is_resistant_to(DamageType.Acid)))

    def threat_on_enter(self, target, *args, **kwargs):
        return 0

    def threat_on_start_of_turn(self, target, *args, **kwargs):
        threat = avg_roll(self.factory.dmg_dice)
        return threat if not target.is_resistant_to(self.dmg_type) else threat / 2

    def threat_on_move_within(self, target, *args, **kwargs):
        return 0

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        if get_swallower(self.factory.combatant):
            return None
        battle_map = Map.get()
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return battle_map.get_free_coords_in_cartesian_range(Coords(self.origin),  # not actually combatant coords
                                                                 distances,
                                                                 inflate_to_dist=self.factory.combatant.size.value,
                                                                 rng=HungerOfHadarFactory.range, combatant=self.factory.combatant)
        elif battle_map.get_cartesian_distance_coords(battle_map.get_combatant_position(self.factory.combatant).get(), np.array([self.origin])) <= HungerOfHadarFactory.range:
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
        return None
