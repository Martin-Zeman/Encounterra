import math
from simulator.actions.actoid import FactoryFlags
from simulator.actions.attack import AttackFactory, Attack
from simulator.actions.melee_attack import MeleeAttackFactory, MeleeAttack
from simulator.battle_map import Map
from simulator.misc import percent_of_curr_hp
from simulator.threat_utils import mean_dmg
import logging


logger = logging.getLogger("EncounTroll")

class PreSwallowBiteFactory(MeleeAttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=math.inf, on_hit=None, extra_dmg=[]):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg)
        self.flags |= FactoryFlags.IS_MELEE

    def create(self, target_combatant):
        if self.combatant.constricted_target is None or (self.combatant.constricted_target is target_combatant and target_combatant.is_alive()):
            return PreSwallowBite(target_combatant, self)
        return None


    def create_all(self):
        if self.combatant.constricted_target is not None and self.combatant.constricted_target.is_alive():
            return [PreSwallowBite(self.combatant.constricted_target, self)]
        targets = self.get_eligible_targets()
        return [PreSwallowBite(t, self) for t in targets]



class PreSwallowBite(MeleeAttack):

    def shorthand_str(self):
        return "Bite"

    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        return battle_map.get_free_coords_in_hop_range(battle_map.get_combatant_position(self.target_combatant),
                                                       distances,
                                                       inflate_to_size=self.factory.combatant.size,
                                                       rng=self.factory.range,
                                                       combatant=self.factory.combatant)

    def is_current_coord_eligible(self):
        battle_map = Map.get()
        return battle_map.are_in_hop_range(self.factory.combatant, self.target_combatant, self.factory.range)