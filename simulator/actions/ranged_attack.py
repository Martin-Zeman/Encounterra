import math
from ..actions.actoid import FactoryFlags
from ..actions.attack import AttackFactory, Attack
from ..battle_map import Map, map_position_toggled_cache
from ..misc import Visibility
from ..conditions import Conditions, is_affected_by_any, get_swallower
from ..resources import Uses, ResourceRefreshType
from ..utils.roll_types import RollType, ROLL_TYPE_DELTA
import logging
import numba_functions as nf

logger = logging.getLogger("Encounterra")


class RangedAttackFactory(AttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=Uses(math.inf, ResourceRefreshType.NEVER), on_hit=None, extra_dmg=None, uses_dex=True, to_hit_bonus_die=None, **kwargs):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg, uses_dex, False, to_hit_bonus_die)
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
            acc = nf.mean_dmg(to_hit_total, self.dmg_dice, self.dmg_bonus, target.ac, target.is_immune_to(self.dmg_type),
                           target.is_resistant_to(self.dmg_type), self.crit_range)
            for extra in self.extra_dmg:
                acc += nf.mean_dmg(to_hit_total, [extra[0]], 0, target.ac,
                                target.is_immune_to(extra[1]), target.is_resistant_to(extra[1]), self.crit_range)
            for oh in self.on_hit:
                acc += nf.calc_p_hit(to_hit_total, target.ac) * oh.calculate_threat(self.combatant, target)
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
        swallower = get_swallower(self.factory.combatant)
        if swallower:
            if swallower is self.target:
                return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]  # Makes barely any sense but ok
            return None
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        # if self.factory.combatant.movement > 0 and not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            free_coords_in_range = nf.get_free_coords_in_cartesian_range(
                battle_map.grid,
                battle_map.get_combatant_position(self.target).get(),
                distances,
                self.factory.combatant.size.value,
                self.factory.range, self.factory.combatant.id)
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
