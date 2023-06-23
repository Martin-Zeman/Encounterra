import math
from simulator.actions.actoid import FactoryFlags
from simulator.actions.attack import AttackFactory, Attack
from simulator.actions.melee_attack import MeleeAttackFactory, MeleeAttack
from simulator.misc import percent_of_curr_hp, Size
from simulator.threat_utils import mean_dmg
import logging


logger = logging.getLogger("EncounTroll")

class BiteAndSwallowFactory(MeleeAttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=math.inf, on_hit=None, extra_dmg=[]):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg)
        self.flags |= FactoryFlags.IS_MELEE

    def create(self, target_combatant):
        if self.combatant.constricted_target is target_combatant and target_combatant.size <= Size.MEDIUM:
            return BiteAndSwallow(target_combatant, self)
        return None

    def create_all(self, battle_map):
        if self.combatant.constricted_target is not None and self.combatant.constricted_target.size <= Size.MEDIUM:
            return [BiteAndSwallow(self.combatant.constricted_target)]
        return None



class BiteAndSwallow(MeleeAttack):

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