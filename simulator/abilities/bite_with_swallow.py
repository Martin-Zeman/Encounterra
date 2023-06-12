import math
from simulator.actions.actoid import FactoryFlags
from simulator.actions.attack import AttackFactory, Attack
from simulator.actions.melee_attack import MeleeAttackFactory, MeleeAttack
from simulator.misc import percent_of_curr_hp
from simulator.threat_utils import mean_dmg
import logging


logger = logging.getLogger("EncounTroll")

class BiteWithSwallowFactory(MeleeAttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=math.inf, on_hit=None, extra_dmg=[]):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg)
        self.flags |= FactoryFlags.IS_MELEE

    def create(self, target_combatant):
        return BiteWithSwallow(target_combatant, self)

    def create_all(self, battle_map):
        targets = self.get_eligible_targets(battle_map)
        return [BiteWithSwallow(t, self) for t in targets]



class BiteWithSwallow(MeleeAttack):

    def shorthand_str(self):
        return "Bite"

    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        return battle_map.get_free_coords_in_hop_range(battle_map.get_combatant_position(self.target_combatant),
                                                       distances,
                                                       inflate_to_size=self.factory.combatant.size,
                                                       rng=self.factory.range,
                                                       combatant=self.factory.combatant)

    def is_current_coord_eligible(self, battle_map):
        return battle_map.are_in_hop_range(self.factory.combatant, self.target_combatant, self.factory.range)