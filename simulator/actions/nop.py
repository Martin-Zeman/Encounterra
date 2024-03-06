from .action_types import BonusAction
from ..battle_map import Map, map_position_toggled_cache
from ..conditions import Conditions, is_affected_by_any
from ..actions.actoid import Actoid
from ..threat_interfaces import DirectThreat
from ..factory_interfaces import DirectThreatFactory
import logging

logger = logging.getLogger("Encounterra")


class NopFactory(DirectThreatFactory):

    def __init__(self, action_type, combatant):
        super().__init__()
        self.action_type = action_type
        self.combatant = combatant


    def __str__(self):
        """
        Important for FSM building
        """
        return "NopFactory"

    def create_all(self, previous_action_in_dag=None):
        return [Nop(self)]

    def create(self, target):
        return Nop(self)

    def calculate_threat_to_target(self, target, **kwargs):
        return 0

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        return 0  # No need

    def calculate_max_threat(self):
        return 0


class Nop(Actoid, DirectThreat):

    def __init__(self, factory):
        Actoid.__init__(self)
        self.factory = factory

    def __str__(self):
        return f"{'Bonus ' if isinstance(self.factory.action_type, BonusAction) else ''}NOP of {self.factory.combatant}"

    def shorthand_str(self):
        return f"NOP"

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        return 0

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0  # Doesn't apply here

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)
        return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
