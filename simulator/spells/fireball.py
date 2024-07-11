from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import BonusAction
from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key, \
    _get_free_coords_in_cartesian_range, _get_cartesian_distance_coords
from ..combatant_coords import Coords
from ..spells.spell import SpellStats
from ..misc import SavingThrow, DamageType
from ..conditions import Conditions, is_affected_by_any, get_swallower
from ..actions.actoid import Actoid, ActoidFlags, FactoryFlags
from ..threat_utils import mean_dmg_dc_attack
from ..threat_interfaces import DirectThreat
from ..factory_interfaces import DirectThreatFactory
import numpy as np


class FireballFactory(DirectThreatFactory):
    level = 3
    range = SpellStats.Range.FEET_150.value
    target = SpellStats.Target.RADIUS_20
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.HARMFUL
    dmg_type = DamageType.Fire

    def __init__(self, dc, action_type, caster, resource, has_spell_sculpting=False):
        super().__init__()
        self.flags |= FactoryFlags.DEX_SAVE_APPLIES
        self.dc = dc
        self.action_type = action_type  # FIREBALL, QUICKENED_FIREBALL
        self.saving_throw = SavingThrow.DEX
        self.dmg_dice = ((8, 6),)
        self.additional_upcast_dmg = ((1, 6),)
        self.combatant = caster
        self.has_spell_sculpting = has_spell_sculpting
        self.resource = resource

    def __str__(self):
        """
        Important for FSM building
        """
        return "FireballFactory"

    def get_ability_name(self):
        return "Fireball"

    def get_twinned_kwargs(self):
        return {'dc': self.dc, 'caster': self.combatant, 'has_spell_sculpting': self.has_spell_sculpting, 'resource': self.resource}

    def get_quickened_kwargs(self):
        return {'dc': self.dc, 'caster': self.combatant, 'has_spell_sculpting': self.has_spell_sculpting, 'resource': self.resource}

    def find_best_args(self, combatant):
        coord, _ = Map.get().find_best_placement_harmful_circular(combatant, FireballFactory.range, SpellStats.TRANSLATE_RADIUS[FireballFactory.target], self)
        return coord[0]

    def create_all(self, previous_action_in_dag=None):
        # Here there really is no need to iterate over all coords. Just find the best score
        return [Fireball(self.find_best_args(self.combatant), self)]

    def create(self, coord):
        return Fireball(coord, self)

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates threat to one specific target
        """
        if Map.get().get_cartesian_distance_combatants(self.combatant, target) <= FireballFactory.range + SpellStats.TRANSLATE_RADIUS[FireballFactory.target]:
            return min(target.curr_hp, mean_dmg_dc_attack(self.dc, self.dmg_dice, True,
                                                          target.saving_throws[self.saving_throw],
                                                          target.is_immune_to(FireballFactory.dmg_type),
                                                          target.is_resistant_to(FireballFactory.dmg_type)))
        return 0

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0  # No need

    def calculate_max_threat(self):
        return Fireball(self.find_best_args(self.combatant), self).calculate_threat()


class Fireball(Actoid, DirectThreat):

    def __init__(self, coord, factory,  **kwargs):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        # self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.coord = coord
        self.factory = factory
        self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.heightened = False if "heightened " not in kwargs or not kwargs["heightened "] else True

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FIREBALL else "") + f"Fireball at {np.squeeze(self.coord)}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FIREBALL else "") + "Fireball"

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        battle_map = Map.get()
        affected = battle_map.get_combatants_affected_by_sphere_aoe(self.factory.combatant, FireballFactory.target, FireballFactory.type, self.coord)
        acc = 0
        for aff in affected:
            mean_dmg = min(aff.curr_hp, mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, True,
                                                           aff.saving_throws[self.factory.saving_throw],
                                                           aff.is_immune_to(FireballFactory.dmg_type),
                                                           aff.is_resistant_to(FireballFactory.dmg_type)))
            acc += (1 if battle_map.teams.are_enemies(self.factory.combatant, aff) else -3) * mean_dmg
        return acc

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        #self.get_eligible_coords.cache_clear()

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0  # Not relevant for this ability

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        if get_swallower(self.factory.combatant):
            return None
        battle_map = Map.get()
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return _get_free_coords_in_cartesian_range(
                battle_map.grid,
                Coords(self.coord).get(),  # not actually combatant coords
                distances,
                inflate_to_dist=self.factory.combatant.size.value,
                rng=FireballFactory.range,
                combatant_id=self.factory.combatant.id)
        elif _get_cartesian_distance_coords(battle_map.get_combatant_position(self.factory.combatant).get(), np.array([self.coord])) <= FireballFactory.range:
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
        return None
