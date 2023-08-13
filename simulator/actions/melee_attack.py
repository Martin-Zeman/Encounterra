import math

from cachetools import cached
from cachetools.keys import hashkey

from simulator.actions.actoid import FactoryFlags
from simulator.actions.attack import AttackFactory, Attack
from simulator.battle_map import Map, map_toggled_cache_with_key
from simulator.misc import percent_of_curr_hp, Conditions
from simulator.threat_utils import mean_dmg
import logging


logger = logging.getLogger("Encounterra")

class MeleeAttackFactory(AttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=math.inf, on_hit=None, extra_dmg=[], finesse=False):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg)
        self.flags |= FactoryFlags.IS_MELEE
        if finesse:
            self.flags |= FactoryFlags.IS_FINESSE

    def create(self, target):
        return MeleeAttack(target, self)

    def create_all(self):
        targets = self.get_eligible_targets()
        return [MeleeAttack(t, self) for t in targets]


class MeleeAttack(Attack):

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        swallower = self.factory.combatant.get_swallower()
        if swallower:
            if swallower is self.target:
                return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
            return None
        if self.factory.combatant.movement > 0 and not self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return battle_map.get_free_coords_in_hop_range(battle_map.get_combatant_position(self.target),
                                                           distances,
                                                           inflate_to_size=self.factory.combatant.size,
                                                           rng=self.factory.range,
                                                           combatant=self.factory.combatant)
        elif battle_map.are_in_hop_range(self.factory.combatant, self.target, self.factory.range):
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
