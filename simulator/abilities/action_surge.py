from ..battle_map import Map
from ..misc import get_missing_hp, percentile_roll
from ..conditions import Conditions, is_affected_by_any
from ..actions.actoid import Actoid, FactoryFlags
from ..actions.action_types import FreeAction
from ..factory_interfaces import DirectThreatFactory
import logging

from ..threat_interfaces import DirectThreat

logger = logging.getLogger("Encounterra")


class ActionSurgeFactory(DirectThreatFactory):

    @staticmethod
    def get_action_surge_uses(level):
        match level:
            case lvl if 1 <= lvl <= 16:
                return 1
            case lvl if 17 <= lvl <= 20:
                return 2
            case _:
                logger.error("Incorrect combatant level of rage")
                return 1

    def __init__(self, combatant):
        super().__init__()
        self.flags |= FactoryFlags.IS_DIRECT_THREAT
        self.flags |= FactoryFlags.TARGETS_SELF
        self.combatant = combatant
        self.action_type = FreeAction.ACTION_SURGE

    def __str__(self):
        """
        Important for FSM building
        """
        return "ActionSurgeFactory"

    def get_ability_name(self):
        return "Action Surge"

    def get_eligible_targets(self):
        pass  # No need due to the TARGETS_SELF flag

    def create_all(self, previous_action_in_dag=None):
        return [ActionSurge(self)]

    def create(self, target):
        # Doesn't make much sense here
        return ActionSurge(self)

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates the threat the factory is capable of dealing to a specific target.
        This is useful for calculating threat_in from the abilities of enemies
        """
        # return min(get_missing_hp(self.combatant), percentile_roll((1, 10), 70) + self.combatant.level)
        return self.calculate_max_threat()

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        return 0

    def calculate_max_threat(self):
        missing_hp = get_missing_hp(self.combatant)
        healing = percentile_roll((1, 10), 70) + self.combatant.level
        return min([missing_hp - healing, missing_hp, healing])
        # return min(get_missing_hp(self.combatant), percentile_roll((1, 10), 70) + self.combatant.level)


class ActionSurge(Actoid, DirectThreat):

    def __init__(self, factory):
        Actoid.__init__(self)
        self.factory = factory

    def __str__(self):
        return f"Action Surge of {self.factory.combatant}"

    def shorthand_str(self):
        return "Action Surge"

    def calculate_threat(self, **kwargs):
        # return min(get_missing_hp(self.factory.combatant), percentile_roll((1, 10), 70) + self.factory.combatant.level)
        return self.factory.calculate_max_threat()

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)
        return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0
