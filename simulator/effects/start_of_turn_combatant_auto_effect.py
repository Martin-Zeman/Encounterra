from ..effects.effect import Effect
import logging

logger = logging.getLogger("Encounterra")


class StartOfTurnAutoEffect(Effect):
    def __init__(self, initiator, target):
        Effect.__init__(self, initiator)
        self.target = target

    def is_affecting(self, combatant):
        return combatant is self.target

    def activate(self):
        pass

    def deactivate(self):
        pass
