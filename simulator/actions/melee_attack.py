import math
from simulator.actions.actoid import FactoryFlags
from simulator.actions.attack import AttackFactory, Attack
from simulator.misc import percent_of_curr_hp
from simulator.threat import mean_dmg
import logging


logger = logging.getLogger(__name__)

class MeleeAttackFactory(AttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, max_num=1, ammo=math.inf, on_hit=None):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, max_num, on_hit)
        self.flags |= FactoryFlags.IS_MELEE
        self.ammo = math.inf

    def find_best_args(self, combatant, battle_map):
        # TODO Deprecated
        potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.movement + self.range + 1)
        hp_percentages = [percent_of_curr_hp(pt, mean_dmg(self.to_hit, self.dmg_dice, self.dmg_bonus, pt.ac, self.crit_range)) for pt
                          in potential_targets]
        potential_targets = list(zip(potential_targets, hp_percentages))
        potential_targets.sort(key=lambda e: e[1], reverse=True)
        return potential_targets[0][0] if potential_targets else None

    def create_all(self, battle_map):
        targets = self.get_eligible_targets(battle_map)
        return [MeleeAttack(t, self) for t in targets]


class MeleeAttack(Attack):

    def get_eligible_coords(self, battle_map):
        target_combatant_coords = battle_map.get_combatant_position(self.target_combatant)
        return battle_map.get_free_coords_in_hop_range(target_combatant_coords, inflate_to_size=self.factory.combatant.size, rng=self.factory.range)