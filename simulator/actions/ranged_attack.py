import math
from functools import cache

from simulator.actions.actoid import FactoryFlags
from simulator.actions.attack import AttackFactory, Attack
from simulator.battle_map import Map
from simulator.combatant_coords import Coords
from simulator.misc import percent_of_curr_hp
from simulator.threat_utils import mean_dmg
import logging

from simulator.utils.roll_types import RollType, ROLL_TYPE

logger = logging.getLogger("EncounTroll")

class RangedAttackFactory(AttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=math.inf, on_hit=None, extra_dmg=[]):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg)
        self.flags |= FactoryFlags.IS_RANGED

    def create(self, target):
        return RangeAttack(target, self)

    def create_all(self):
        targets = self.get_eligible_targets()
        return [RangeAttack(t, self) for t in targets]

    def calculate_threat_to_target(self, target, **kwargs):
        try:
            consider_dist = kwargs["consider_dist"]
        except KeyError:
            consider_dist = False
        try:
            roll_type = kwargs['roll_type']
        except KeyError:
            roll_type = RollType.STRAIGHT

        to_hit_total = self.to_hit
        to_hit_total += ROLL_TYPE[roll_type][max(0, min(target.ac - to_hit_total, 20))]

        # TODO: Should I include roll types here? There may be a use-case in the future
        battle_map = Map.get()
        if not consider_dist or battle_map.get_cartesian_distance(self.combatant, target) <= self.range:
            acc = mean_dmg(to_hit_total, self.dmg_dice, self.dmg_bonus, target.ac, self.crit_range, target.is_resistant_to(self.dmg_type))
            for extra in self.extra_dmg:
                acc += mean_dmg(to_hit_total, extra[0], 0, target.ac, self.crit_range, target.is_resistant_to(extra[1]))
            return acc
        return 0


class RangeAttack(Attack):

    def calculate_threat(self, combatant_coords: Coords = None, *args, **kwargs):
        battle_map = Map.get()
        roll_type = RollType.STRAIGHT if not battle_map.is_enemy_adjacent(self.factory.combatant) else RollType.DISADVANTAGE
        roll_type = RollType.DISADVANTAGE if battle_map.get_cartesian_distance(self.factory.combatant, self.target) > self.factory.short_range else roll_type
        return self.factory.calculate_threat_to_target(self.target, roll_type=roll_type, **kwargs)

    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        return battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.target),
                                                             distances,
                                                             inflate_to_size=self.factory.combatant.size,
                                                             rng=self.factory.range, combatant=self.factory.combatant)

    def is_current_coord_eligible(self):
        if self.factory.combatant.get_swallower() is self.target:
            return True
        battle_map = Map.get()
        return battle_map.get_cartesian_distance(self.factory.combatant, self.target) <= self.factory.range