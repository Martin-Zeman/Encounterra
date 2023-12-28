from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import Action
from ..actions.actoid import Actoid, ActoidFlags, FactoryFlags
import logging
from ..battle_map import Map, map_toggled_cache_with_key
from ..conditions import Conditions, is_affected_by_any, is_affected_by, get_swallower
from ..misc import SHORTER_ROUND_HORIZON
from ..threat_interfaces import DirectThreat
from ..factory_interfaces import Factory

logger = logging.getLogger("Encounterra")


class ShakeAllyAwakeFactory(Factory):
    def __init__(self, combatant):
        super().__init__()
        self.combatant = combatant
        self.action_type = Action.SHAKE_ALLY_AWAKE

    def __str__(self):
        """
        Important for FSM building
        """
        return "ShakeAllyAwakeFactory"

    def create_all(self, previous_action_in_dag=None):
        allies = Map.get().get_allies(self.combatant)
        return [ShakeAllyAwake(self, ally) for ally in allies if is_affected_by(ally, Conditions.CAN_BE_SHAKEN_AWAKE)]

    def create(self, target):
        return ShakeAllyAwake(self, target)


class ShakeAllyAwake(Actoid, DirectThreat):
    def __init__(self, factory, target):
        Actoid.__init__(self, ActoidFlags.IS_DASH)
        self.factory = factory
        self.target = target

    def __str__(self):
        return f"Shaking {self.target} awake"

    def shorthand_str(self):
        return f"Shaking ally awake"

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0  # Not relevant for this

    @map_toggled_cache_with_key(key=lambda self, **kwargs: hashkey(kwargs["movement_threat"], self.factory.combatant.movement, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def calculate_threat(self, **kwargs):
        max_action_threat = 0
        for f in self.target.action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags:
                max_action_threat = max(max_action_threat, f[1].calculate_max_threat())
        for f in self.target.bonus_action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags:
                max_action_threat = max(max_action_threat, f[1].calculate_max_threat())
        return max_action_threat * SHORTER_ROUND_HORIZON

    def clear_cache(self):
        self.calculate_threat.cache_clear()

    def calculate_threat_for_attack(self, combatant, attack, *args, **kwargs):
        return 0  # TODO do the distance mod here

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        if get_swallower(self.factory.combatant):
            return None
        battle_map = Map.get()
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return battle_map.get_free_coords_in_hop_range(battle_map.get_combatant_position(self.target),
                                                           distances,
                                                           inflate_to_dist=self.factory.combatant.size.value,
                                                           rng=1,
                                                           combatant=self.factory.combatant)
        elif battle_map.are_in_hop_range(self.factory.combatant, self.target, self.factory.range):
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
