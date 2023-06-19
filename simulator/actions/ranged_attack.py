import math
from functools import cache

from simulator.actions.actoid import FactoryFlags
from simulator.actions.attack import AttackFactory, Attack
from simulator.combatant_coords import CombatantCoords
from simulator.misc import percent_of_curr_hp
from simulator.threat_utils import mean_dmg
import logging

from simulator.utils.roll_types import RollType

logger = logging.getLogger("EncounTroll")

class RangedAttackFactory(AttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=math.inf, on_hit=None, extra_dmg=[]):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg)
        self.flags |= FactoryFlags.IS_RANGED

    def create(self, target_combatant):
        return RangeAttack(target_combatant, self)

    def create_all(self, battle_map):
        targets = self.get_eligible_targets(battle_map)
        return [RangeAttack(t, self) for t in targets]


class RangeAttack(Attack):

    # @cache
    def calculate_threat(self, combatant, battle_map, combatant_coords: CombatantCoords = None, *args, **kwargs):
        roll_type = RollType.STRAIGHT if not battle_map.is_enemy_adjacent(self.factory.combatant) else RollType.DISADVANTAGE
        roll_type = RollType.DISADVANTAGE if battle_map.get_cartesian_distance(self.factory.combatant, self.target_combatant) > self.factory.short_range else roll_type
        return self.factory.calculate_threat_to_target(battle_map, self.target_combatant, roll_type=roll_type, **kwargs)

    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        return battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.target_combatant),
                                                             distances,
                                                             inflate_to_size=self.factory.combatant.size,
                                                             rng=self.factory.range, combatant=self.factory.combatant)

    def is_current_coord_eligible(self, battle_map):
        return battle_map.get_cartesian_distance(self.factory.combatant, self.target_combatant) <= self.factory.range