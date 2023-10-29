from ..effects.effect import Effect
import logging

from ..misc import roll_saving_throw, reconcile_roll_types

logger = logging.getLogger("Encounterra")

class StartOfTurnEffect(Effect):
    def __init__(self, initiator, combatant, st, dc):
        Effect.__init__(self, initiator)
        self.combatant = combatant
        self.st = st
        self.dc = dc


    def start_of_turn(self):
        """

        :return: False if the saved against the effect and can be removed, True otherwise
        """
        saved = roll_saving_throw(self.combatant.saving_throws[self.st], self.dc, reconcile_roll_types(self.combatant.saving_throws_roll_type_mod[self.st]))
        if saved:
            logger.info(f"{self.combatant} saved against {self}")
            return False
        logger.info(f"{self.combatant} failed the save against {self}")
        return True
