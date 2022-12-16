from simulator.action import *
import random
import logging
import re

logger = logging.getLogger(__name__)

def parse_dmg_dice(dice_string):
    p = re.compile('(\d+)d(\d+)')
    m = p.match(dice_string)
    num_dice = int(m.group(1))
    dice_size = int(m.group(2))
    return num_dice, dice_size

class CombatManager:

    def __init__(self, characters, teams, battle_map):
        self.characters = characters
        self.teams = teams
        self.battle_map = battle_map

    def resolve_dmg_saving_throw(self, ability, target_char):
        # TODO prompt reaction
        bonus = target_char.saving_throws[ability.saving_throw]
        rolled = random.randint(1, 20)
        if rolled == 1:
            result = False
        elif rolled == 20:
            result = True
        elif rolled + bonus >= ability.dc:
            result = True
        else:
            result = False
        dmg = parse_dmg_dice(ability.dmg)
        target_char.receive_dmg(dmg, ability.dmg_type)

    def resolve_spell(self, caster, spell):
        match spell.__class__.__name__:
            case "Fireball":
                affected = self.battle_map.get_characters_affected_by_aoe(caster, spell)
                for ch in affected:
                    self.resolve_dmg_saving_throw(spell, ch)
            case _:
                logger.error("Unknown spell")




    def resolve_attack(self, attack):  # TODO remove character from attack and have it as a separate parameter
        """

        :param attack:
        :return: True is hits, false if misses or is not attack
        """
        target = None
        for character in self.characters:
            if character == attack.get_target_character():
                target = character
                # TODO: Consider including this in the action itself

        if not target:
            logger.warning(f"No target found for action {attack.get_name()}")
            return False

        if attack.get_type() != "ATTACK":
            logger.warning("Non-attack actions not supported yet")
            return False

        if attack.advantage and not target.disadvantage_on_incoming_attacks:
            rolled = max(random.randint(1, 20), random.randint(1, 20))
        elif not attack.advantage and target.disadvantage_on_incoming_attacks:
            rolled = min(random.randint(1, 20), random.randint(1, 20))
        else:
            rolled = random.randint(1, 20)
        multiplier = 1
        if rolled == 1:
            logger.debug("Natural 1 rolled!", extra={"team": self.teams.get_team(attack.character)})
            return False
        elif rolled in attack.crit_range:
            multiplier = 2
        if rolled + attack.to_hit >= target.ac:
            num_dice, dice_size = parse_dmg_dice(attack.dmg_dice)
            dmg_dice_sum = 0
            for i in range(num_dice):
                dmg_dice_sum += random.randint(1, dice_size)
            total_dmg = multiplier * dmg_dice_sum + attack.dmg_bonus + attack.character.get_ability_dmg_bonus()
            logger.debug(f"Attack {'CRITS' if multiplier == 2 else 'hits'} for {total_dmg} of which {attack.character.get_ability_dmg_bonus()} is ability dmg", extra={"team": self.teams.get_team(attack.character)})
            target.receive_dmg(total_dmg, attack.get_dmg_type())
            if not target.is_alive():
                self.battle_map.remove_character(target)
            return True
        else:
            logger.debug("Attack misses", extra={"team": self.teams.get_team(attack.character)})
            return False
