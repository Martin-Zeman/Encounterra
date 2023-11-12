from ..actions.action_types import Reaction
import logging
from ..actions.actoid import Actoid, ActoidFlags
from ..threat_interfaces import Factory, DirectThreat

logger = logging.getLogger("Encounterra")

class UncannyDodgeFactory(Factory):

    def __init__(self, combatant):
        super().__init__()
        self.action_type = Reaction.UNCANNY_DODGE
        self.combatant = combatant

    def __str__(self):
        """
        Important for FSM building
        """
        return "UncannyDodgeFactory"


    def get_ability_name(self):
        return "Uncanny Dodge"

    def create(self, attack):
        return UncannyDodge(self, attack)


class UncannyDodge(Actoid, DirectThreat):

    def __init__(self, factory, attack):
        Actoid.__init__(self)
        self.factory = factory
        self.attack = attack  # The attack to be mitigated

    def __str__(self):
        return "Uncanny Dodge"

    def shorthand_str(self):
        return "Uncanny Dodge"

    def get_eligible_coords(self, distances, shortest_paths):
        pass  # No need

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0

    def calculate_threat(self, **kwargs):
        return self.attack.calculate_threat() / 2
