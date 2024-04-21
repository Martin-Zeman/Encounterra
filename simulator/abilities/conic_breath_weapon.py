from ..actions.action_types import Action
from ..actions.actoid import Actoid
from ..battle_map import Map, map_position_toggled_cache
from ..conditions import Conditions, is_affected_by_any, get_swallower
from ..spells.spell import SpellStats
from ..threat_interfaces import DirectThreat
from ..factory_interfaces import DirectThreatFactory, RechargeFactory
from ..threat_utils import mean_dmg_dc_attack
from ..misc import Visibility
import logging

logger = logging.getLogger("Encounterra")


class ConicBreathWeaponFactory(DirectThreatFactory, RechargeFactory):

    def __init__(self, combatant, recharge, dmg_dice, dmg_type, saving_throw, dc, target_template, name):
        DirectThreatFactory.__init__(self)
        self.combatant = combatant
        self.action_type = Action.CONIC_BREATH_WEAPON
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
        best_placements = Map.get().find_best_placements_harmful_cone(self.combatant, SpellStats.TRANSLATE_CONE[self.target_template])
        return [ConicBreathWeapon(bp[0], bp[1], self) for bp in best_placements]

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates the threat the factory is capable of dealing to a specific target.
        This is useful for calculating threat_in from the abilities of enemies
        """
        return mean_dmg_dc_attack(self.dc, self.dmg_dice, True, target.saving_throws[self.saving_throw])

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0  # No need

    def calculate_max_threat(self):
        all_placements = self.create_all()
        return max([p.calculate_threat() for p in all_placements])


class ConicBreathWeapon(Actoid, DirectThreat):

    def __init__(self, coord, angle, factory):
        Actoid.__init__(self)
        self.coord = coord
        self.angle = angle
        self.factory = factory

    def __str__(self):
        return f"{self.factory} at {self.coord} at {self.angle} deg"

    def shorthand_str(self):
        return {self.factory}

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if get_swallower(self.factory.combatant):
            return None  # Webbing someone from the inside doesn't make sense
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            free_coords_in_range = battle_map.get_free_coords_in_hop_range(battle_map.get_combatant_position(self.target),
                                                           distances,
                                                           inflate_to_dist=self.factory.combatant.size.value + self.factory.distance,
                                                           rng=battle_map.size,  # approximation, could theoretically be longer
                                                           combatant=self.factory.combatant)
            return [coord for coord in free_coords_in_range if battle_map.visibility_dict_for_all_coords[coord][self.target] is not Visibility.NONE]
        elif battle_map.get_hop_distance_combatants(self.factory.combatant, self.target) >= self.factory.distance and \
                battle_map.visibility_dict_for_all_coords[curr_coord][self.target] is not Visibility.NONE:
            return [curr_coord]
        return None

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        battle_map = Map.get()
        affected = battle_map.get_combatants_affected_by_cone_aoe(self.factory.target_template, self.coord, self.angle)
        acc = 0
        for aff in affected:
            mean_dmg = mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, True, aff.saving_throws[self.factory.saving_throw])
            acc += (1 if battle_map.teams.are_enemies(self.factory.combatant, aff) else -3) * mean_dmg
        return acc

    def clear_cache(self):
        self.calculate_threat.cache_clear()

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0  # Not relevant for this ability
