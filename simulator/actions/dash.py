from simulator.actions.actoid import Actoid, ActoidFlags
import logging

from simulator.battle_map import Map
from simulator.threat_interfaces import Factory, ThreatModifier, AttackThreatModifier

logger = logging.getLogger("EncounTroll")

class DashFactory(Factory):
    def __init__(self, action_type, combatant):
        super().__init__()
        self.combatant = combatant
        self.action_type = action_type  # DASH, CUNNING_DASH

    def __str__(self):
        """
        Important for FSM building
        """
        return "DashFactory"

    def create_all(self):
        return [Dash(self)]

    def create(self):
        return Dash(self)


class Dash(Actoid, ThreatModifier, AttackThreatModifier):
    def __init__(self, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_DASH)
        self.name = "Dash"
        self.factory = factory

    def calculate_threat(self, **kwargs):
        return 0  # TODO calculate the danger zone delta here

    def calculate_threat_for_attack(self, combatant, attack, *args, **kwargs):
        return 0  # TODO do the distance mod here

    def get_eligible_coords(self, distances, shortest_paths):
        return Map.get().get_all_accessible_coords(shortest_paths, self.factory.combatant)

    def is_current_coord_eligible(self):
        return True
