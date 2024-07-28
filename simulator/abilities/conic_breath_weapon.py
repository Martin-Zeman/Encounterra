from ..actions.action_types import Action
from ..actions.actoid import Actoid
from ..battle_map import Map, PLACEHOLDER_MAPPING
from ..conditions import get_swallower
from ..spells.spell import SpellStats
from ..threat_interfaces import DirectThreat
from ..factory_interfaces import DirectThreatFactory, RechargeFactory
from functools import cache, reduce
import logging
import numba_functions as nf

logger = logging.getLogger("Encounterra")


class ConicBreathWeaponFactory(DirectThreatFactory, RechargeFactory):

    def __init__(self, action_type, combatant, recharge, dmg_dice, dmg_type, saving_throw, dc, target_template, name):
        DirectThreatFactory.__init__(self)
        self.combatant = combatant
        self.action_type = action_type
        self.recharge_value = recharge
        self.dmg_dice = dmg_dice
        self.dmg_type = dmg_type
        self.saving_throw = saving_throw
        self.dc = dc
        self.target_template = target_template
        self.name = name

    def __str__(self):
        return self.name + "Factory"

    def get_ability_name(self):
        return self.name

    def create(self, coord):
        return ConicBreathWeapon(coord, 0, self)  # TODO: This is kind of useless but probably not used at all

    def create_all(self, previous_action_in_dag=None):
        best_placement = Map.get().find_best_placement_harmful_cone(self.combatant, SpellStats.TRANSLATE_CONE[self.target_template])
        if best_placement[0].shape[0] == 0:
            return []
        return [ConicBreathWeapon(best_placement[0], best_placement[1], self)]

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates the threat the factory is capable of dealing to a specific target.
        This is useful for calculating threat_in from the abilities of enemies
        """
        return min(target.curr_hp, nf.mean_dmg_dc_attack(self.dc, self.dmg_dice, True,
                                                      target.saving_throws[self.saving_throw],
                                                      target.is_immune_to(self.dmg_type),
                                                      target.is_resistant_to(self.dmg_type)))

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0  # No need

    def calculate_max_threat(self):
        battle_map = Map.get()
        enemies = [e for e in battle_map.get_enemies(self.combatant)]
        return reduce(lambda dmg, e: dmg + self.calculate_threat_to_target(e), enemies, 0)


class ConicBreathWeapon(Actoid, DirectThreat):

    def __init__(self, coord, angle, factory):
        Actoid.__init__(self)
        self.coord = coord
        self.angle = angle
        self.factory = factory

    def __str__(self):
        return f"{self.factory.get_ability_name()} from {self.coord} at {round(self.angle, 1)} deg"

    def shorthand_str(self):
        return f"{self.factory.get_ability_name()}"

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if get_swallower(self.factory.combatant):
            return None, None
        # We allow the conic effect to originate from any square the combatant takes up
        return battle_map.find_possible_combatant_positions_for_cone_or_line_aoe_placement(self.coord, self.factory.combatant, shortest_paths), PLACEHOLDER_MAPPING

    @cache
    def calculate_threat(self, **kwargs):
        battle_map = Map.get()
        affected = battle_map.get_combatants_affected_by_cone_aoe(self.factory.combatant, self.factory.target_template, self.coord, self.angle)
        acc = 0
        for aff in affected:
            avg_dmg = min(aff.curr_hp, nf.mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, True,
                                                           aff.saving_throws[self.factory.saving_throw],
                                                           aff.is_immune_to(self.factory.dmg_type),
                                                           aff.is_resistant_to(self.factory.dmg_type)))
            acc += (1 if battle_map.teams.are_enemies(self.factory.combatant, aff) else -3) * avg_dmg
        return acc

    def clear_cache(self):
        self.calculate_threat.cache_clear()

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0  # Not relevant for this ability
