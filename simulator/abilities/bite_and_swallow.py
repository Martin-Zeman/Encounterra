import math
from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.actoid import FactoryFlags
from ..actions.melee_attack import MeleeAttackFactory, MeleeAttack
from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key
from ..misc import Size, Conditions
import logging

logger = logging.getLogger("Encounterra")

class BiteAndSwallowFactory(MeleeAttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=math.inf, on_hit=[], extra_dmg=[]):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg)
        self.flags |= FactoryFlags.IS_MELEE

    def get_ability_name(self):
        return "Bite and swallow"

    def create(self, target):
        grappled_target = self.combatant.get_grappled()
        if grappled_target is target and target.is_alive() and target.size.value <= Size.MEDIUM.value:
            return BiteAndSwallow(target, self)
        return None

    def create_all(self, previous_action_in_dag=None):
        grappled_target = self.combatant.get_grappled()
        if grappled_target and grappled_target.is_alive():
            return [BiteAndSwallow(grappled_target, self)]
        return None


class BiteAndSwallow(MeleeAttack):

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

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        # The swallow itself it hard to quantify, but we just need to make sure it wins out over the regular bite
        return self.factory.calculate_threat_to_target(self.target, **kwargs)

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        self.calculate_threat_delta.cache_clear()
        #self.get_eligible_coords.cache_clear()

    @map_toggled_cache_with_key(key=lambda self, modifiers, *args, **kwargs: hashkey(self.factory.name, tuple(modifiers.items()), tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        battle_map = Map.get()
        return self.factory.calculate_threat_to_target_delta(battle_map, self.target, modifiers, *args, **kwargs)