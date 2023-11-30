from ..actions.action_types import Reaction
import logging
from ..actions.actoid import Actoid, ActoidFlags
from ..factory_interfaces import DirectThreatFactory

logger = logging.getLogger("Encounterra")

class ParryFactory(DirectThreatFactory):

    def __init__(self, ac):
        DirectThreatFactory.__init__(self)
        self.action_type = Reaction.PARRY
        self.ac = ac

    def __str__(self):
        """
        Important for FSM building
        """
        return "ParryFactory"


    def get_ability_name(self):
        return "Parry"


    def calculate_threat_to_target(self, target, **kwargs):
        return 0

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        return 0

    def create(self):
        return Parry(self)


class Parry(Actoid):

    def __init__(self, factory):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        self.action_type = Reaction.SHIELD
        self.factory = factory

    def __str__(self):
        return "Parry"

    def shorthand_str(self):
        return "Parry"

    def get_eligible_coords(self, distances, shortest_paths):
        pass  # No need

