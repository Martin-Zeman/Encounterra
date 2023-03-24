import math

from simulator.action_types import BonusActionOrdering
from simulator.actions.actoid import FactoryFlags
from simulator.actions.attack import AttackFactory
from simulator.misc import percent_of_curr_hp
from simulator.threat import mean_dmg
import logging


logger = logging.getLogger(__name__)

class RangedAttackFactory(AttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, max_num=1, ammo=math.inf, on_hit=None):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, max_num, on_hit)
        self.flags |= FactoryFlags.IS_RANGED
        self.bonus_action_ordering = BonusActionOrdering.INDEPENDENT  # In case this became a bonus action
        self.ammo = ammo

    def __str__(self):
        """
        Important for FSM building
        """
        return "RangedAttackFactory" + self.name

    def find_best_args(self, combatant, battle_map):
        # TODO consider prioritizing the ones you have a change to finish off
        potential_targets = battle_map.get_enemies_within_radius(combatant, combatant.movement + self.range)
        hp_percentages = [percent_of_curr_hp(pt, mean_dmg(self.to_hit, self.dmg_dice, self.dmg_bonus, pt.ac, self.crit_range)) for pt
                          in potential_targets]
        potential_targets = list(zip(potential_targets, hp_percentages))
        potential_targets.sort(key=lambda e: e[1], reverse=True)
        return potential_targets[0][0] if potential_targets else None

    def get_eligible_coords(self, target_combatant, battle_map):
        target_combatant_coords = battle_map.get_combatant_coordinates[target_combatant]
        return battle_map.get_free_coords_in_range(target_combatant_coords, inflate_to_size=self.combatant.size, rng=self.range)