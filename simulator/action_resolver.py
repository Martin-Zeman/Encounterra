import logging
from simulator.misc import *
from simulator.misc import SavingThrow, Conditions
from simulator.feasibility import check_feasibility
from simulator.resources import use_resources
from simulator.action_factory import *
from simulator.actoid import Actoid

logger = logging.getLogger(__name__)


def resolve_dmg_saving_throw(ability, dmg, target_combatant):
    # TODO prompt reaction
    bonus = target_combatant.saving_throws[ability.saving_throw][0]

    # TODO unify this with the attack (dis)advantage
    advantage_counter = 0
    disadvantage_counter = 0
    if target_combatant.saving_throws[ability.saving_throw][1] is RollModifier.ADVANTAGE:
        advantage_counter += 1
    elif target_combatant.saving_throws[ability.saving_throw][1] is RollModifier.DISADVANTAGE:
        disadvantage_counter += 1
    if ability.saving_throw is SavingThrow.DEX and target_combatant.has_passive(
            Passive.DANGER_SENSE) and not target_combatant.is_affected_by_any(Conditions.INCAPACITATED,
                                                                              Conditions.BLINDED,
                                                                              Conditions.DEAFENED):
        advantage_counter += 1

    if advantage_counter > 0 and disadvantage_counter == 0:
        rolled = max(random.randint(1, 20), random.randint(1, 20))
    elif disadvantage_counter > 0 and advantage_counter == 0:
        rolled = min(random.randint(1, 20), random.randint(1, 20))
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
        f"{type(ability).__name__} deals {dmg if not saved else dmg // 2} to {target_combatant}")
    target_combatant.receive_dmg(dmg if not saved else dmg // 2, ability.dmg_type)


class ActionResolver:

    def __init__(self, combatants, teams, battle_map, effect_tracker):
        self.combatants = combatants
        self.teams = teams
        self.battle_map = battle_map
        self.effect_tracker = effect_tracker

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
            case "Haste":
                spell.activate()
                self.effect_tracker.add(spell, caster)
            case "Firebolt":
                if self.battle_map.are_in_range(caster, spell.target, spell.range.value):
                    self.resolve_ranged_spell_attack(caster, spell)
                else:
                    logger.debug("Out of Firebolt's range")  # TODO could probably remove this. No map is gonna be that big
            case "MistyStep":
                if self.battle_map.get_hop_distance(caster, spell.coord) <= 6:
                    self.battle_map.move_combatant(caster, spell.coord)
                else:
                    logger.warning("Invalid MistyStep coordinates. Destination is too far!")
            case "Chaosbolt":
                pass
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

    def has_advantage(self, attack, attacker, target):
        if attacker.has_pack_tactics and self.battle_map.is_ally_adjacent(attacker, target):
            return True
        if hasattr(attacker, "reckless_attack_active") and attacker.reckless_attack_active:
            return True
        if hasattr(target, "reckless_attack_active") and target.reckless_attack_active:
            logger.debug(f"{attacker} gains advantage since {target} attacked recklessly")
            return True
        return False

    def has_disadvantage(self, attack, attacker, target):
        if target.disadvantage_on_incoming_attacks:
            return True
        if target.is_dodging:
            return True
        return False

    def resolve_attack(self, attack):  # TODO remove combatant from attack and have it as a separate parameter
        """

        :param attack:
        :return: True is hits, false if misses or is not attack
        """
        target = attack.get_target_combatant()
        attacker = attack.combatant
        assert target
        advantage = self.has_advantage(attack, attacker, target)
        disadvantage = self.has_disadvantage(attack, attacker, target)

        if advantage and not disadvantage:
            rolled = max(random.randint(1, 20), random.randint(1, 20))
        elif disadvantage and not advantage:
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
            reaction, *args = target.prompt_after_hit_reaction(attacker)
            self.resolve_action(reaction, args, target)
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

    def request_movement(self, moving_combatant, movement):
        if movement.incurs_aoo:
            aoo_candidates = self.battle_map.get_aoo_eligible_combatants(moving_combatant, movement.increment)
            if aoo_candidates:
                for candidate in aoo_candidates:
                    aoo, *args = candidate.prompt_aoo(moving_combatant)
                    if aoo and moving_combatant.is_alive():
                        self.resolve_action(aoo, args, candidate)

            pam_candidates = self.battle_map.get_pam_eligible_combatants(moving_combatant, movement.increment)
            if pam_candidates:
                for candidate in pam_candidates:
                    pam_attack, *args = candidate.prompt_pam(moving_combatant)
                    if pam_attack and moving_combatant.is_alive():
                        did_attack_hit = self.resolve_action(pam_attack, args, candidate)
                        if did_attack_hit and candidate.has_passive(Passive.SENTINEL):
                            moving_combatant.movement = 0
                            logger.debug(f"Combatant {moving_combatant} was stopped by sentinel")

        if moving_combatant.is_alive():
            self.battle_map.move_combatant_by_increment(moving_combatant, movement.increment)
            return True
        return False

    def resolve_by_actoid_type(self, actoid, combatant):
        """
        Resolves an action by its actoid type
        :param actoid: actoid to be resolved
        :param combatant: acting combatant
        :return: in case of an attack returns True if the attack hit, false otherwise. Dodge always returns True, unknown parameters false.
        Other cases return None.
        """
        if actoid is None:
            return None
        match actoid.actoid_type:
            case Actoid.Type.IS_ATTACK_LIKE_ACTION:
                return self.resolve_attack(actoid)
            case Actoid.Type.IS_MOVEMENT:
                if not self.request_movement(combatant, actoid):
                    return None  # combatant didn't survive
            case Actoid.Type.IS_SPELL:
                return self.resolve_spell(combatant, actoid)
            case Actoid.Type.IS_DODGE:
                combatant.is_dodging = True
                combatant.saving_throws[SavingThrow.DEX][1] = RollModifier.ADVANTAGE
                return True
            case Actoid.Type.IS_DASH:
                combatant.movement += combatant.speed
                return True
            case Actoid.Type.IS_TOGGLE_ABILITY:
                self.resolve_toggle_ability(combatant, actoid)
                return None
            case _:
                logger.error("Unknown actoid type")
                return False

    def resolve_action(self, action_type, args, combatant):
        # TODO consider turning this into a pipeline
        if action_type is None:
            return
        action = action_factory(combatant, self.effect_tracker, action_type, *args)
        if not check_feasibility(combatant, action, self.battle_map):
            logger.warning(f"Action of type {action_type} by {combatant} is non-feasible")
            return
        use_resources(combatant, action)
        return self.resolve_by_actoid_type(action, combatant)

    def resolve_toggle_ability(self, combatant, ability):
        match ability.__class__.__name__:
            case "TotemRage" | "Rage" | "RecklessAttack":
                ability.activate()
                self.effect_tracker.add(ability, combatant)
            case _:
                logger.error("Unknown toggle ability")

    def resolve_effects(self, effects, combatant):
        """
        Applies the aspect of effects that need to be reapplied at the beginning of a turn or would otherwise be reset by the new turn
        :param effects:
        :param combatant:
        :return:
        """
        for effect in effects:
            match effect.__class__.__name__:
                case "Haste":
                    # resolves the part of the haste spell which needs to be applied every turn
                    combatant.movement = combatant.speed * 2
                    combatant.has_haste_action = True
                case "PostHasteLethargy":
                    combatant.movement = 0
                    combatant.has_action = False
                    combatant.has_bonus_action = False
                    combatant.has_reaction = False
                case "Shield":
                    pass
                case "TotemRage" | "Rage":
                    pass  # TODO track if the barbarian attacked or received dmg
                case _:
                    logger.error("Unknown effect")
