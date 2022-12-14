from simulator.character import Character
from simulator.attack import Attack
from simulator.dodge import Dodge
from simulator.movement import Movement, MovementGenerator
from simulator.action import Action
from simulator.spellslots import Spellslots
import numpy as np
import logging

logger = logging.getLogger(__name__)

class Faurung(Character):

    def __init__(self):
        faurung_attacks = [Attack("Staff of Defence", self,  3, "1d8", -1, Action.ActionClasses.ACTION, "Bludgeoning", 1)]
        super().__init__("Faurung", faurung_attacks, 43, 16, 2, 30, [], num_attacks=1)
        self.sorc_spellslots = Spellslots(Spellslots.SORCERER, 5)

    def get_action(self, battle_map):
        while self.has_action or self.has_bonus_action or self.movement:
            battle_map.find_best_placement_harmful_circular(self, 30, 4)
            return None
        logger.debug(f"{self.name} uses the dodge action", extra={"team": self.team_name})
        return Dodge("dodge", self, Action.ActionClasses.ACTION)

    def prompt_aoo(self, moving_character):
        if self.has_reaction:
            pass
        return None