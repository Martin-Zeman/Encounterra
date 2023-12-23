from ..effects.effect import Effect
import logging

logger = logging.getLogger("Encounterra")


class LimitedDurationEffect(Effect):
    def __init__(self, initiator, turns):
        Effect.__init__(self, initiator)
        self.turns = turns

    def start_of_turn_tick(self):
        """

        :return: False if the effect expired and can be removed, True otherwise
        """
        self.turns -= 1
        if self.turns <= 0:
            return False
        return True
