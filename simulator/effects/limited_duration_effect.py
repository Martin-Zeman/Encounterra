from simulator.effects.effect import Effect
import logging

logger = logging.getLogger(__name__)
class LimitedDurationEffect(Effect):
    def __init__(self, turns):
       self.turns = turns


    def new_turn(self):
        """

        :return: False if the effect expired and can be removed, True otherwise
        """
        self.turns -= 1
        if self.turns <= 0:
            logger.debug(f"{self.__class__.__name__} expires")
            self.deactivate()
            return False
        return True
