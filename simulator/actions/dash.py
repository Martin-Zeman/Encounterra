from functools import cache
from simulator.actions.action_types import BonusAction, HasteAction
from simulator.actions.actoid import Actoid, ActoidFlags
import logging
from simulator.battle_map import Map
from simulator.threat_interfaces import Factory, AttackThreatModifier

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


class Dash(Actoid, AttackThreatModifier):
    def __init__(self, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_DASH)
        self.name = "Dash"
        self.factory = factory

    def __str__(self):
        prefix = ""
        if self.factory.action_type is BonusAction.CUNNING_DASH:
            prefix = "Cunning "
        elif self.factory.action_type is HasteAction.HASTE_DASH:
            prefix = "Hasted "
        return prefix + f"Dash of {self.factory.combatant}"

    def shorthand_str(self):
        prefix = ""
        if self.factory.action_type is BonusAction.CUNNING_DASH:
            prefix = "Cunning "
        elif self.factory.action_type is HasteAction.HASTE_DASH:
            prefix = "Hasted "
        return prefix + f"Dash"

    def calculate_threat(self, **kwargs):
        return 0  # TODO calculate the danger zone delta here

    def calculate_threat_for_attack(self, combatant, attack, *args, **kwargs):
        return 0  # TODO do the distance mod here

    def get_eligible_coords(self, distances, shortest_paths):
        return Map.get().get_all_accessible_coords(shortest_paths, self.factory.combatant)

    def is_current_coord_eligible(self):
        return True
