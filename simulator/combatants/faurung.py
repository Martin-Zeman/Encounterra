from simulator.combatant import Combatant
from simulator.attack import Attack
from simulator.dodge import Dodge
from simulator.movement import Movement, MovementGenerator
from simulator.action import Action
from simulator.spellslots import Spellslots
from simulator.misc import DamageType
from simulator.spells.fireball import Fireball
import numpy as np
import logging

logger = logging.getLogger(__name__)


class Faurung(Combatant):

    def __init__(self):
        faurung_attacks = [Attack("Staff of Defence", self, 3, "1d8", -1, Action.ActionClasses.ACTION, DamageType.Bludgeoning, 1)]
        super().__init__("Faurung", actions=faurung_attacks, hp=43, ac=16, init_bonus=2, speed=30, resistances=[], dc=15, num_attacks=1)
        self.sorc_spellslots = Spellslots(Spellslots.Class.SORCERER, 5)

    def get_action(self, battle_map):
        while self.has_action or self.has_bonus_action or self.movement:
            if self.has_action and self.sorc_spellslots.has_spellslots(3):
                placement = battle_map.find_best_placement_harmful_circular(self, 30, 4)
                fireball = Fireball(placement, self.dc)
                self.sorc_spellslots.use_spellslot(3)
                self.has_action = False
                logger.debug(f"{self.name} uses Fireball", extra={"team": self.team_name})
                return fireball
            else:
                return None
        logger.debug(f"{self.name} uses the dodge action", extra={"team": self.team_name})
        return Dodge(self, Action.ActionClasses.ACTION)

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            pass
        return None
