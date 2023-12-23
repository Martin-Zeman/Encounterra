from .combatant_effect import CombatantEffect
import logging

logger = logging.getLogger("Encounterra")


class StartOfTurnAutoEffect(CombatantEffect):
    def __init__(self, initiator, targets):
        CombatantEffect.__init__(self, initiator, targets)

    def activate(self, **kwargs):
        pass

    def deactivate(self, **kwargs):
        return False
