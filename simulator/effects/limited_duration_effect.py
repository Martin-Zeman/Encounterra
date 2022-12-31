from simulator.effects.effect import Effect
import logging

logger = logging.getLogger(__name__)
class LimitedDurationEffect(Effect):
    def __init__(self, rounds):
       self.rounds = rounds


    def new_round(self):
        self.rounds -= 1
        if self.rounds <= 0:
            logger.debug(f"{self.__class__.__name__} expires")
            self.deactivate()
