from simulator.spells.spell import SpellStats
from simulator.actions.action_types import Reaction
import logging
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.threat_interfaces import DirectThreatFactory

logger = logging.getLogger("EncounTroll")

class ShieldFactory(DirectThreatFactory):
    level = 1
    range = SpellStats.Range.SELF.value
    target = SpellStats.Target.SELF
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.BUFF
    dc = None
    dmg_type = None


    def __init__(self, caster):
        self.action_type = Reaction.SHIELD
        self.combatant = caster

    def __str__(self):
        """
        Important for FSM building
        """
        return "ShieldFactory"

    def calculate_threat_to_target(self, target, **kwargs):
        return 0

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        return 0

    def create(self):
        return Shield(self)


class Shield(Actoid):

    def __init__(self, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_SPELL)
        self.actoid_flags |= ActoidFlags.IS_POSITIONING_INDEPENDENT
        self.action_type = Reaction.SHIELD
        self.factory = factory

    def __str__(self):
        return "Shield"

    def shorthand_str(self):
        return "Shield"

    def get_eligible_coords(self, distances, shortest_paths):
        pass  # No need due to IS_POSITIONING_INDEPENDENT, in addition to that it's a reaction anyway

    def is_current_coord_eligible(self):
        return True
