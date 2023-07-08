from simulator.effects.effect import Effect
import logging

logger = logging.getLogger("EncounTroll")

class StartOfTurnAutoEffect(Effect):
    def __init__(self, target):
       self.target = target

    def is_affecting(self, combatant):
        return combatant is self.target
