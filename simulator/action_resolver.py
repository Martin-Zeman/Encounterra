import logging
from simulator.misc import *
from simulator.misc import SavingThrow, Conditions
from simulator.action_factory import Passive

logger = logging.getLogger(__name__)


def resolve_dmg_saving_throw(ability, dmg, target_combatant):
    # TODO prompt reaction
    bonus = target_combatant.saving_throws[ability.saving_throw]
    if (target_combatant.is_dodging or (
            target_combatant.has_passive(Passive.DANGER_SENSE) and not target_combatant.is_affected_by_any(Conditions.INCAPACITATED,
                                                                                                           Conditions.BLINDED,
                                                                                                           Conditions.DEAFENED))) and ability.saving_throw is SavingThrow.DEX:
        rolled = max(random.randint(1, 20), random.randint(1, 20))
    else:
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
        f"{type(target_combatant).__name__} deals {dmg if not saved else dmg // 2} to {target_combatant}")
    target_combatant.receive_dmg(dmg if not saved else dmg // 2, ability.dmg_type)


class ActionResolver:

    def __init__(self, combatants, teams, battle_map):
        self.combatants = combatants
        self.teams = teams
        self.battle_map = battle_map

    def resolve_ranged_spell_attack(self, caster, spell):
        if not (spell.target.disadvantage_on_incoming_attacks or spell.target.is_dodging):
            rolled = max(random.randint(1, 20), random.randint(1, 20))
        elif spell.target.disadvantage_on_incoming_attacks or spell.target.is_dodging:
            rolled = min(random.randint(1, 20), random.randint(1, 20))
        else:
            rolled = random.randint(1, 20)
        multiplier = 1
        if rolled == 1:
            logger.debug("Natural 1 rolled!", extra={"team": self.teams.get_team(caster)})
            return False
        elif rolled == 20:
            multiplier = 2

        if rolled + spell.to_hit >= spell.target.ac:
            dmg = multiplier * roll_spell_dmg(spell)
            logger.debug(f"{spell.__class__.__name__} {'CRITS' if multiplier == 2 else 'hits'} {spell.target} for {dmg} damage",
                         extra={"team": self.teams.get_team(caster)})
            spell.target.receive_dmg(dmg, spell.dmg_type)
            if not spell.target.is_alive():
                self.battle_map.remove_combatant(spell.target)
        else:
            logger.debug(f"{spell.__class__.__name__} misses {spell.target}", extra={"team": self.teams.get_team(caster)})

    def resolve_spell(self, caster, spell):
        match spell.__class__.__name__:
            case "Fireball":
                affected = self.battle_map.get_combatants_affected_by_aoe(caster, spell)
                dmg = roll_spell_dmg(spell)
                for combatant in affected:
                    logger.debug(f"{combatant} is hit by Fireball")
                    resolve_dmg_saving_throw(spell, dmg, combatant)
                    if not combatant.is_alive():
                        self.battle_map.remove_combatant(combatant)
            case "Firebolt":
                if self.battle_map.are_in_range(caster, spell.target, spell.range.value):
                    self.resolve_ranged_spell_attack(caster, spell)
                else:
                    logger.debug("Out of Firebolt's range")  # TODO could probably remove this. No map is gonna be that big
            case "MistyStep":
                if self.battle_map.get_distance(caster, spell.coord) <= 6:
                    self.battle_map.move_combatant(caster, spell.coord)
                else:
                    logger.warning("Invalid MistyStep coordinates. Destination is too far!")
            case "Shield":
                assert not caster.shield_spell_active
                caster.shield_spell_active = True
                caster.ac += 5
            case _:
                logger.error("Unknown spell")

    def resolve_after_hit_reaction(self, attacker, target, reaction):
        if reaction is None:
            return
        match reaction.__class__.__name__:
            case "Shield":
                self.resolve_spell(target, reaction)
            case _:
                logger.error("Unknown after hit reaction")

    def resolve_pack_tactics(self, attack, attacker, target):
        if attacker.has_pack_tactics and self.battle_map.is_ally_adjacent(attacker, target):
            attack.advantage = True

    def resolve_attack(self, attack):  # TODO remove combatant from attack and have it as a separate parameter
        """

        :param attack:
        :return: True is hits, false if misses or is not attack
        """
        target = attack.get_target_combatant()
        attacker = attack.combatant
        assert target
        self.resolve_pack_tactics(attack, attacker, target)

        if attack.advantage and not (target.disadvantage_on_incoming_attacks or target.is_dodging):
            rolled = max(random.randint(1, 20), random.randint(1, 20))
        elif not attack.advantage and (target.disadvantage_on_incoming_attacks or target.is_dodging):
            rolled = min(random.randint(1, 20), random.randint(1, 20))
        else:
            rolled = random.randint(1, 20)
        multiplier = 1
        if rolled == 1:
            logger.debug("Natural 1 rolled!", extra={"team": self.teams.get_team(attacker)})
            return False
        elif rolled in attack.crit_range:
            multiplier = 2
        if rolled + attack.to_hit >= target.ac:
            reaction = target.prompt_after_hit_reaction(attacker)
            self.resolve_after_hit_reaction(attacker, target, reaction)
        if rolled + attack.to_hit >= target.ac:  # Potentially missing this time
            num_dice, dice_size = parse_dmg_dice(attack.dmg_dice)
            dmg_dice_sum = roll_dice(num_dice, dice_size)
            total_dmg = multiplier * dmg_dice_sum + attack.dmg_bonus + attacker.ability_dmg_bonus
            logger.debug(
                f"Attack {'CRITS' if multiplier == 2 else 'hits'} for {total_dmg} of which {attacker.ability_dmg_bonus} is ability dmg",
                extra={"team": self.teams.get_team(attacker)})
            target.receive_dmg(total_dmg, attack.get_dmg_type())
            if not target.is_alive():
                self.battle_map.remove_combatant(target)
            return True
        else:
            logger.debug("Attack misses", extra={"team": self.teams.get_team(attacker)})
            return False
