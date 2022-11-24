from simulator.action import *
import random
from dpr_calculator import parse_dmg_dice
import logging

logger = logging.getLogger(__name__)

class CombatManager:

    def __init__(self, characters, teams):
        self.characters = characters
        self.teams = teams

    def resolve_action(self, action):
        target = None
        for character in self.characters:
            if character == action.get_target_character():
                target = character
                # TODO: Cosider including this in the action itself

        if not target:
            logger.warning(f"No target found for action {action.get_name()}")
            return

        if action.get_type() != "ATTACK":
            logger.warning("Non-attack actions not supported yet")
            return

        # if self.hp <= 0:
        #     return False
        rolled = random.randint(1, 20)
        multiplier = 1
        if rolled == 1:
            logger.debug("Natural 1 rolled!", extra={"team": self.teams.get_team(action.character)})
            return
        elif rolled in action.crit_range:
            multiplier = 2
        if rolled + action.to_hit >= target.ac:
            num_dice, dice_size = parse_dmg_dice(action.dmg_dice)
            dmg_dice_sum = 0
            for i in range(num_dice):
                dmg_dice_sum += random.randint(1, dice_size)
            total_dmg = multiplier * dmg_dice_sum + action.dmg_bonus + action.character.get_ability_dmg_bonus()
            logger.debug(f"Attack {'CRITS' if multiplier == 2 else 'hits'} for {total_dmg} of which {action.character.get_ability_dmg_bonus()} is ability dmg", extra={"team": self.teams.get_team(action.character)})
            target.receive_dmg(total_dmg, action.get_dmg_type())
        else:
            logger.debug("Attack misses", extra={"team": self.teams.get_team(action.character)})
