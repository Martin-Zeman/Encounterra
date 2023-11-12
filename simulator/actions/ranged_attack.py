import math
from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.actoid import FactoryFlags
from ..actions.attack import AttackFactory, Attack
from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key
from ..misc import Visibility, Conditions
from ..threat_utils import mean_dmg, calc_p_hit
from ..utils.roll_types import RollType, ROLL_TYPE_DELTA
import logging

logger = logging.getLogger("Encounterra")

class RangedAttackFactory(AttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=math.inf, on_hit=None, extra_dmg=[]):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg)
        self.flags |= FactoryFlags.IS_RANGED

    def get_ability_name(self):
        return "Ranged Attack"

    def create(self, target):
        return RangedAttack(target, self)

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [RangedAttack(t, self) for t in targets]

    def calculate_threat_to_target(self, target, **kwargs):
        consider_dist = kwargs.get("consider_dist", False)
        roll_type = kwargs.get("roll_type", RollType.STRAIGHT)

        to_hit_total = self.to_hit
        to_hit_total += ROLL_TYPE_DELTA[roll_type][max(0, min(target.ac - to_hit_total, 20))]

        # TODO: Should I include roll types here? There may be a use-case in the future
        battle_map = Map.get()
        if not consider_dist or battle_map.get_cartesian_distance_combatants(self.combatant, target) <= self.range:
            acc = mean_dmg(to_hit_total, self.dmg_dice, self.dmg_bonus, target.ac, self.crit_range, target.is_resistant_to(self.dmg_type))
            for extra in self.extra_dmg:
                acc += mean_dmg(to_hit_total, extra[0], 0, target.ac, self.crit_range, target.is_resistant_to(extra[1]))
            if self.on_hit:
                acc += calc_p_hit(to_hit_total, target.ac) * self.on_hit.calculate_threat(self.combatant, target)
            return acc
        return 0


class RangedAttack(Attack):

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        battle_map = Map.get()
        roll_type = RollType.STRAIGHT if not battle_map.is_enemy_adjacent(self.factory.combatant) else RollType.DISADVANTAGE
        roll_type = RollType.DISADVANTAGE if battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.target) > self.factory.short_range else roll_type
        return self.factory.calculate_threat_to_target(self.target, roll_type=roll_type, **kwargs)

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        self.calculate_threat_delta.cache_clear()
        #self.get_eligible_coords.cache_clear()

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        swallower = self.factory.combatant.get_swallower()
        if swallower:
            if swallower is self.target:
                return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]  # Makes barely any sense but ok
            return None
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        # if self.factory.combatant.movement > 0 and not self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
        if not self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            free_coords_in_range = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.target),
                                                                                 distances,
                                                                                 inflate_to_size=self.factory.combatant.size,
                                                                                 rng=self.factory.range, combatant=self.factory.combatant)
            if not battle_map.effect_tracker.is_combatant_hidden_from(self.factory.combatant, self.target):
                return [coord for coord in free_coords_in_range if battle_map.visibility_dict_for_all_coords[coord][self.target] is not Visibility.NONE]
            else:
                # We only consider the coords where Visibility.NONE transitions into any other kind
                ret = list()
                for coord in free_coords_in_range:
                    if battle_map.visibility_dict_for_all_coords[coord][self.target] is not Visibility.NONE:
                        try:
                            if battle_map.visibility_dict_for_all_coords[tuple(shortest_paths[coord])][self.target] is Visibility.NONE:
                                ret.append(coord)
                        except KeyError:
                            ret.append(coord)
                return ret
        elif battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.target) <= self.factory.range and \
                battle_map.visibility_dict_for_all_coords[curr_coord][self.target] is not Visibility.NONE:
            return [curr_coord]
        return None
