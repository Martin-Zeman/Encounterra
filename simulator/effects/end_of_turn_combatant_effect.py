from .combatant_effect import CombatantEffect
import logging

from ..misc import roll_saving_throw, reconcile_roll_types

logger = logging.getLogger("Encounterra")


class EndOfTurnEffect(CombatantEffect):
    def __init__(self, initiator, targets, st, dc):
        CombatantEffect.__init__(self, initiator, targets)
        self.st = st
        self.dc = dc

    def combatant_saved_at_end_of_turn(self, combatant):
        """

        :return: False if the saved against the effect and can be removed, True otherwise
        """
        saved = roll_saving_throw(self.combatants[0].saving_throws[self.st], self.dc, reconcile_roll_types(self.combatants[0].saving_throws_roll_type_mod[self.st]))
        if saved:
            logger.info(f"{self.combatants[0]} saved against {self}")
            return False
        logger.info(f"{self.combatants[0]} failed the save against {self}")
        return True
