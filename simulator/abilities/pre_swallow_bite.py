import math

from ..actions.actoid import FactoryFlags
from ..actions.melee_attack import MeleeAttackFactory, MeleeAttack
from ..battle_map import Map
from ..misc import Conditions
import logging


logger = logging.getLogger("Encounterra")

class PreSwallowBiteFactory(MeleeAttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=math.inf, on_hit=None, extra_dmg=[]):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg)
        self.flags |= FactoryFlags.IS_MELEE


    def get_ability_name(self):
        return "Bite with grapple"

    def create(self, target):
        if self.combatant.constricted_target is None or (self.combatant.constricted_target is target and target.is_alive()):
            return PreSwallowBite(target, self)
        return None


    def create_all(self, previous_action_in_dag=None):
        if self.combatant.constricted_target is not None and self.combatant.constricted_target.is_alive():
            return [PreSwallowBite(self.combatant.constricted_target, self)]
        targets = self.get_eligible_targets()
        return [PreSwallowBite(t, self) for t in targets]



class PreSwallowBite(MeleeAttack):

    def shorthand_str(self):
        return "Bite"


    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if not self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return battle_map.get_free_coords_in_hop_range(battle_map.get_combatant_position(self.target),
                                                           distances,
                                                           inflate_to_size=self.factory.combatant.size,
                                                           rng=self.factory.range,
                                                           combatant=self.factory.combatant)
        elif battle_map.are_in_hop_range(self.factory.combatant, self.target, self.factory.range):
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
        return None
