from simulator.effects.effect import Effect
import logging

from simulator.misc import roll_saving_throw, reconcile_roll_types

logger = logging.getLogger("Encounterra")
class EndOfTurnEffect(Effect):
    def __init__(self, combatant, st, dc):
       self.combatant = combatant
       self.st = st
       self.dc = dc


    def end_of_turn(self):
        """

        :return: False if the saved against the effect and can be removed, True otherwise
        """
        saved = roll_saving_throw(self.combatant.saving_throws[self.st], self.dc, reconcile_roll_types(self.combatant.saving_throws_roll_type_mod[self.st]))
        if saved:
            logger.info(f"{self.combatant} saved against {self}")
            return False
        logger.info(f"{self.combatant} failed the save against {self}")
        return True
