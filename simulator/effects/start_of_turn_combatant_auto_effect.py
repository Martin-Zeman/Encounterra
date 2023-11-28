from .combatant_effect import CombatantEffect
import logging

logger = logging.getLogger("Encounterra")


class StartOfTurnAutoEffect(CombatantEffect):
    def __init__(self, initiator, targets):
        CombatantEffect.__init__(self, initiator, targets)

    def activate(self):
        pass

    def deactivate(self):
        pass
