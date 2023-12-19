import logging
from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import BonusAction
from ..battle_map import Map, map_position_toggled_cache
from ..combatant_coords import Coords
from ..effects.combatant_effect import CombatantEffect
from ..effects.effect import EffectType
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..spells.spell import SpellStats
from ..misc import Conditions, roll_dice, ConditionWithoutDC
from ..actions.actoid import Actoid, ActoidFlags, FactoryFlags
from ..threat_utils import mean_dmg_dc_attack
from ..threat_interfaces import DirectThreat
from ..factory_interfaces import DirectThreatFactory
import numpy as np


logger = logging.getLogger("Encounterra")


class SleepFactory(DirectThreatFactory):
    level = 1
    range = SpellStats.Range.FEET_90.value
    target = SpellStats.Target.RADIUS_20
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL
    dmg_type = None

    def __init__(self, dc, action_type, caster, resource):
        super().__init__()
        self.flags |= FactoryFlags.DEX_SAVE_APPLIES
        self.action_type = action_type  # SLEEP, QUICKENED_SLEEP
        self.combatant = caster
        self.resource = resource

    def __str__(self):
        """
        Important for FSM building
        """
        return "SleepFactory"

    def get_ability_name(self):
        return "Sleep"

    def get_twinned_kwargs(self):
        return {'caster': self.combatant, 'resource': self.resource}

    def get_quickened_kwargs(self):
        return {'caster': self.combatant, 'resource': self.resource}

    def find_best_args(self, combatant):
        coord, _ = Map.get().find_best_placement_harmful_circular(combatant, SleepFactory.range, SpellStats.TRANSLATE_RADIUS[SleepFactory.target], self)
        return coord[0]

    def create_all(self, previous_action_in_dag=None):
        # Here there really is no need to iterate over all coords. Just find the best score
        return [Sleep(self.find_best_args(self.combatant), self)]

    def create(self, coord):
        return Sleep(coord, self)

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates threat to one specific target
        """
        if Map.get().get_cartesian_distance_combatants(self.combatant, target) <= SleepFactory.range + SpellStats.TRANSLATE_RADIUS[SleepFactory.target]:
            return mean_dmg_dc_attack(self.dc, self.dmg_dice, True, target.saving_throws[self.saving_throw])
        return 0

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0  # No need

    def calculate_max_threat(self):
        return Sleep(self.find_best_args(self.combatant), self).calculate_threat()


class Sleep(Actoid, LimitedDurationEffect, CombatantEffect, DirectThreat):

    def __init__(self, coord, factory,  **kwargs):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, factory.combatant, turns=10)
        affected = Map.get().get_combatants_affected_by_aoe(factory.combatant, SleepFactory.target, SleepFactory.type, coord)
        affected.sort(key=lambda combatant: combatant.curr_hp)
        put_to_sleep = []
        hp_acc = 0
        total_hp_affected = roll_dice([(5, 8)])
        for combatant in affected:
            if hp_acc + combatant.curr_hp <= total_hp_affected:
                put_to_sleep.append(combatant)
                hp_acc += combatant.curr_hp
            else:
                break
        CombatantEffect.__init__(self, factory.combatant, put_to_sleep)
        self.coord = coord
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FIREBALL else "") + f"Sleep at {np.squeeze(self.coord)}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FIREBALL else "") + "Sleep"

    def get_effect_type(self):
        return EffectType.SLEEP

    def activate(self, **kwargs):
        if self.combatants:
            # TODO Add free action to all enemies
            self.factory.combatant.concentration_effect = self
            for combatant in self.combatants:
                logger.info(f"{combatant} is put to sleep.")
                combatant.apply_condition(ConditionWithoutDC(Conditions.UNCONSCIOUS, self))
        else:
            logger.info(f"Sleep failed to affect anyone. The rolled HP wasn't high enough.")

    def deactivate(self):
        # TODO Remove free action from all enemies
        self.factory.combatant.break_concentration()
        for combatant in self.combatants:
            combatant.remove_condition(Conditions.UNCONSCIOUS, self)
        return False  # There's only one target -> automatic removal


    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        battle_map = Map.get()
        affected = battle_map.get_combatants_affected_by_aoe(self.factory.combatant, SleepFactory.target, SleepFactory.type, self.coord)
        acc = 0
        for aff in affected:
            mean_dmg = mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, True, aff.saving_throws[self.factory.saving_throw])
            acc += (1 if battle_map.teams.are_enemies(self.factory.combatant, aff) else -3) * mean_dmg
        return acc

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        #self.get_eligible_coords.cache_clear()

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0  # Not relevant for this ability

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        if self.factory.combatant.get_swallower():
            return None
        battle_map = Map.get()
        if not self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return battle_map.get_free_coords_in_cartesian_range(Coords(self.coord),  # not actually combatant coords
                                                                 distances,
                                                                 inflate_to_dist=self.factory.combatant.size.value,
                                                                 rng=SleepFactory.range,
                                                                 combatant=self.factory.combatant)
        elif battle_map.get_cartesian_distance_coords(battle_map.get_combatant_position(self.factory.combatant).get(), np.array([self.coord])) <= SleepFactory.range:
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
        return None
