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


def roll_dice(num_dice, dice_size):
    dice_sum = 0
    for i in range(num_dice):
        dice_sum += random.randint(1, dice_size)
    return dice_sum


def resolve_dmg_saving_throw(ability, dmg, target_combatant):
    # TODO prompt reaction
    bonus = target_combatant.saving_throws[ability.saving_throw]
    rolled = random.randint(1, 20)
    if rolled == 1:
        saved = False
    elif rolled == 20:
        saved = True
    elif rolled + bonus >= ability.dc:
        saved = True
    else:
        saved = False
    logger.debug(
        f"{type(target_combatant).__name__} deals {dmg if not saved else dmg // 2} to {target_combatant.get_name()}")
    target_combatant.receive_dmg(dmg if not saved else dmg // 2, ability.dmg_type)


def roll_spell_dmg(spell):
    num_dice, dice_size = parse_dmg_dice(spell.dmg_dice)
    return roll_dice(num_dice, dice_size)


class CombatManager:

    def __init__(self, combatants, teams, battle_map):
        self.combatants = combatants
        self.teams = teams
        self.battle_map = battle_map

    def resolve_spell(self, caster, spell):
        match spell.__class__.__name__:
            case "Fireball":
                affected = self.battle_map.get_combatants_affected_by_aoe(caster, spell)
                dmg = roll_spell_dmg(spell)
                for combatant in affected:
                    logger.debug(f"{combatant.get_name()} is hit by Fireball")
                    resolve_dmg_saving_throw(spell, dmg, combatant)
            case _:
                logger.error("Unknown spell")

    def resolve_attack(self, attack):  # TODO remove combatant from attack and have it as a separate parameter
        """

        :param attack:
        :return: True is hits, false if misses or is not attack
        """
        target = None
        for combatant in self.combatants:
            if combatant == attack.get_target_combatant():
                target = combatant
                # TODO: Consider including this in the action itself

        if not target:
            logger.warning(f"No target found for action {attack.get_name()}")
            return False

        if type(attack).__name__ != "Attack":
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
            logger.debug("Natural 1 rolled!", extra={"team": self.teams.get_team(attack.combatant)})
            return False
        elif rolled in attack.crit_range:
            multiplier = 2
        if rolled + attack.to_hit >= target.ac:
            num_dice, dice_size = parse_dmg_dice(attack.dmg_dice)
            dmg_dice_sum = roll_dice(num_dice, dice_size)
            total_dmg = multiplier * dmg_dice_sum + attack.dmg_bonus + attack.combatant.get_ability_dmg_bonus()
            logger.debug(
                f"Attack {'CRITS' if multiplier == 2 else 'hits'} for {total_dmg} of which {attack.combatant.get_ability_dmg_bonus()} is ability dmg",
                extra={"team": self.teams.get_team(attack.combatant)})
            target.receive_dmg(total_dmg, attack.get_dmg_type())
            if not target.is_alive():
                self.battle_map.remove_combatant(target)
            return True
        else:
            logger.debug("Attack misses", extra={"team": self.teams.get_team(attack.combatant)})
            return False
