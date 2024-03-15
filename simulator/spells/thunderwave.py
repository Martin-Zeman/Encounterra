import numpy as np

from ..battle_map import Map, map_position_toggled_cache
from ..combatant_coords import Coords
from ..spells.spell import SpellStats
from ..actions.action_types import BonusAction
from ..actions.actoid import Actoid, ActoidFlags
from ..threat_interfaces import  DirectThreat
from ..factory_interfaces import ThreatModifierFactory
from ..misc import SavingThrow
from ..conditions import Conditions, is_affected_by_any, get_swallower
import logging
from ..threat_utils import mean_dmg_dc_attack

logger = logging.getLogger("Encounterra")


class ThunderwaveFactory(ThreatModifierFactory):
    level = 1
    range = SpellStats.Range.TOUCH.value  # It's not really TOUCH, but the value needs to be 1
    target = SpellStats.Target.BOX_15
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL
    dmg_type = None

    def __init__(self, dc, action_type, caster, resource):
        super().__init__()
        self.dc = dc
        self.action_type = action_type  # QUICKENED_THUNDERWAVE, THUNDERWAVE
        self.combatant = caster
        self.saving_throw = SavingThrow.CON
        self.resource = resource
        self.dmg_dice = "2d8"

    def __str__(self):
        """
        Important for FSM building
        """
        return "ThunderwaveFactory"

    def get_ability_name(self):
        return "Thunderwave"

    def get_quickened_kwargs(self):
        return {'combatant': self.combatant, 'resource': self.resource}

    def find_best_args(self, combatant):
        coord, _, _ = Map.get().find_best_placement_harmful_square(combatant, ThunderwaveFactory.range, SpellStats.TRANSLATE_BOX[ThunderwaveFactory.target])
        return coord

    def create_all(self, previous_action_in_dag=None):
        # Here there really is no need to iterate over all coords. Just find the best score
        return [Thunderwave(self.find_best_args(self.combatant), self)]

    def create(self, coord):
        return Thunderwave(coord, self)

    def calculate_threat_to_target(self, target, **kwargs):
        if Map.get().get_cartesian_distance_combatants(self.combatant, target) <= ThunderwaveFactory.range + SpellStats.TRANSLATE_BOX[ThunderwaveFactory.target]:
            return mean_dmg_dc_attack(self.dc, self.dmg_dice, True, target.saving_throws[self.saving_throw])
        return 0

    def calculate_max_threat(self):
        ret = Thunderwave(self.find_best_args(self.combatant), self).calculate_threat()
        return ret


class Thunderwave(Actoid, DirectThreat):

    def __init__(self, coord, factory,  **kwargs):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        self.coord = coord
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_THUNDERWAVE else "") + f"Thunderwave at {self.coord}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_THUNDERWAVE else "") + "Thunderwave"

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        battle_map = Map.get()
        affected = battle_map.get_combatants_affected_by_aoe(self.factory.combatant, ThunderwaveFactory.target, ThunderwaveFactory.type, self.coord)
        acc = 0
        for aff in affected:
            mean_dmg = mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, True, aff.saving_throws[self.factory.saving_throw])
            acc += (1 if battle_map.teams.are_enemies(self.factory.combatant, aff) else -3) * mean_dmg
        return -acc

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0  # Not relevant for this ability

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        #self.get_eligible_coords.cache_clear()

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        if get_swallower(self.factory.combatant):
            return None
        battle_map = Map.get()
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return Map.get().get_free_coords_in_cartesian_range(Coords(self.coord),  # not actually combatant coords
                                                                 distances,
                                                                 inflate_to_dist=self.factory.combatant.size.value,
                                                                 rng=ThunderwaveFactory.range, combatant=self.factory.combatant)
        elif battle_map.get_cartesian_distance_coords(battle_map.get_combatant_position(self.factory.combatant).get(), np.array([self.coord])) <= ThunderwaveFactory.range:
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
        return None

