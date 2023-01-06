import logging
from simulator.misc import *
from simulator.misc import SavingThrow, Side, DistanceMetric
from simulator.feasibility import check_feasibility
from simulator.resources import use_resources
from simulator.action_factory import *
from simulator.actoid import Actoid
from simulator.spells.chaosbolt import Chaosbolt
from simulator.geometry import *
from enum import Enum, auto

logger = logging.getLogger(__name__)

class ActionResult(Enum):
    UNFEASIBLE = auto()
    FEASIBLE = auto()
    NOP = auto()
    MISS = auto()
    DMG = auto()
    SOFT_CC = auto()
    MEDIUM_CC = auto()
    HARD_CC = auto()
    WEAK_BUFF = auto()
    MEDIUM_BUFF = auto()
    STRONG_BUFF = auto()

KILL_BONUS = 10

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
    return target_combatant.receive_dmg(dmg if not saved else dmg // 2, ability.dmg_type)


class ActionResolver:

    def __init__(self, combatants, teams, battle_map, effect_tracker):
        self.combatants = combatants
        self.teams = teams
        self.battle_map = battle_map
        self.effect_tracker = effect_tracker

    def resolve_chaos_bolt(self, caster, target, to_hit, dmg_dice, additional_dmg_dice, name):
        jump = True
        curr_target = target
        potential_targets = self.teams.get_allies(curr_target)
        while jump:
            jump = False
            if not (target.disadvantage_on_incoming_attacks or target.is_dodging):
                rolled = max(random.randint(1, 20), random.randint(1, 20))
            elif target.disadvantage_on_incoming_attacks or target.is_dodging:
                rolled = min(random.randint(1, 20), random.randint(1, 20))
            else:
                rolled = random.randint(1, 20)
            multiplier = 1
            if rolled == 1:
                logger.debug("Natural 1 rolled!", extra={"team": self.teams.get_team(caster)})
                return ActionResult.MISS
            elif rolled == 20:
                multiplier = 2

            if rolled + to_hit >= target.ac:
                bolt_dmg, rolled_numbers = roll_chaos_bolt_dmg(dmg_dice, additional_dmg_dice)
                dmg_type = Chaosbolt.DMG_TYPE[rolled_numbers[random.randint(0, 1)] - 1]  # take one of the two numbers randomly
                dmg = multiplier * bolt_dmg
                logger.debug(f"{name} {'CRITS' if multiplier == 2 else 'hits'} {target} for {dmg} damage",
                             extra={"team": self.teams.get_team(caster)})
                curr_target.receive_dmg(dmg, dmg_type)
                if not curr_target.is_alive():
                    self.battle_map.remove_combatant(target)
                if rolled_numbers[0] == rolled_numbers[1]:
                    for i, potential_target in enumerate(potential_targets):
                        if not potential_target.is_alive():
                            continue
                        dist = self.battle_map.get_cartesian_distance(curr_target, potential_target)
                        if dist and dist <= 6:
                            curr_target = potential_target
                            logger.debug(f"Chaos bolt jumping to {potential_target}!", extra={"team": self.teams.get_team(caster)})
                            jump = True
                            del potential_targets[i]
                            break
                return ActionResult.DMG
            else:
                logger.debug(f"{name} misses {target}", extra={"team": self.teams.get_team(caster)})
                return ActionResult.MISS

    def resolve_ranged_spell_attack(self, caster, target, to_hit, dmg_dice, dmg_type, name):
        # TODO consolidate this
        if not (target.disadvantage_on_incoming_attacks or target.is_dodging):
            rolled = max(random.randint(1, 20), random.randint(1, 20))
        elif target.disadvantage_on_incoming_attacks or target.is_dodging:
            rolled = min(random.randint(1, 20), random.randint(1, 20))
        else:
            rolled = random.randint(1, 20)
        multiplier = 1
        if rolled == 1:
            logger.debug("Natural 1 rolled!", extra={"team": self.teams.get_team(caster)})
            return ActionResult.MISS
        elif rolled == 20:
            multiplier = 2

        if rolled + to_hit >= target.ac:
            dmg = multiplier * roll_spell_dmg(dmg_dice)
            logger.debug(f"{name} {'CRITS' if multiplier == 2 else 'hits'} {target} for {dmg} damage",
                         extra={"team": self.teams.get_team(caster)})
            target.receive_dmg(dmg, dmg_type)
            if not target.is_alive():
                self.battle_map.remove_combatant(target)
            return ActionResult.DMG
        else:
            logger.debug(f"{name} misses {target}", extra={"team": self.teams.get_team(caster)})
            return ActionResult.MISS

    def resolve_spell(self, caster, spell):
        match spell.action_type:
            case Action.FIREBALL | BonusAction.QUICKENED_FIREBALL:
                affected = self.battle_map.get_combatants_affected_by_aoe(caster, spell)
                dmg = roll_spell_dmg(spell.dmg_dice)
                actual_total_dmg = 0
                for combatant in affected:
                    logger.debug(f"{combatant} is hit by Fireball")
                    actual_total_dmg += resolve_dmg_saving_throw(spell, dmg, combatant)
                    if not combatant.is_alive():
                        # TODO revisit if this is really needed
                        actual_total_dmg += KILL_BONUS
                        self.battle_map.remove_combatant(combatant)
                return ActionResult.DMG
            case Action.HASTE | BonusAction.QUICKENED_HASTE:
                spell.activate()
                self.effect_tracker.add(spell, caster)
                ActionResult.MEDIUM_BUFF
            case Action.FIREBOLT | BonusAction.QUICKENED_FIREBOLT:
                return self.resolve_ranged_spell_attack(caster, spell.targets[0], spell.to_hit, spell.dmg_dice, spell.dmg_type, spell.__class__.__name__)
            case Action.TWINNED_FIREBOLT:
                ret = (self.resolve_ranged_spell_attack(caster, spell.targets[0], spell.to_hit, spell.dmg_dice, spell.dmg_type, spell.__class__.__name__),
                       self.resolve_ranged_spell_attack(caster, spell.targets[1], spell.to_hit, spell.dmg_dice, spell.dmg_type, spell.__class__.__name__))
                return ActionResult.DMG if any([True if r is ActionResult.DMG else False for r in ret]) else ActionResult.MISS
            case BonusAction.MISTY_STEP:
                self.battle_map.move_combatant(caster, spell.coord)
                return ActionResult.FEASIBLE
            case Action.CHAOSBOLT | BonusAction.QUICKENED_CHAOSBOLT:
                return self.resolve_chaos_bolt(caster, spell.targets[0], spell.to_hit, spell.dmg_dice, spell.additional_dmg_dice, spell.__class__.__name__)
            case Action.TWINNED_CHAOSBOLT:
                ret = (self.resolve_chaos_bolt(caster, spell.targets[0], spell.to_hit, spell.dmg_dice, spell.additional_dmg_dice, spell.__class__.__name__),
                       self.resolve_chaos_bolt(caster, spell.targets[1], spell.to_hit, spell.dmg_dice, spell.additional_dmg_dice, spell.__class__.__name__))
                return ActionResult.DMG if any([True if r is ActionResult.DMG else False for r in ret]) else ActionResult.MISS
            case Reaction.SHIELD:
                assert not caster.shield_spell_active
                caster.shield_spell_active = True
                caster.ac += 5
                return ActionResult.FEASIBLE
            case _:
                logger.error("Unknown spell")
                return ActionResult.UNFEASIBLE

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
            return ActionResult.MISS
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
            return ActionResult.DMG
        else:
            logger.debug("Attack misses", extra={"team": self.teams.get_team(attacker)})
            return ActionResult.MISS

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
        assert actoid is not None
        match actoid.actoid_type:
            case Actoid.Type.IS_ATTACK_LIKE_ACTION:
                return self.resolve_attack(actoid)
            case Actoid.Type.IS_MOVEMENT:
                if not self.request_movement(combatant, actoid):
                    return ActionResult.UNFEASIBLE  # combatant didn't survive
            case Actoid.Type.IS_SPELL:
                return self.resolve_spell(combatant, actoid)
            case Actoid.Type.IS_DODGE:
                combatant.is_dodging = True
                combatant.saving_throws[SavingThrow.DEX][1] = RollModifier.ADVANTAGE
                return ActionResult.FEASIBLE
            case Actoid.Type.IS_DASH:
                combatant.movement += combatant.speed
                return ActionResult.FEASIBLE
            case Actoid.Type.IS_TOGGLE_ABILITY:
                self.resolve_toggle_ability(combatant, actoid)
                return ActionResult.FEASIBLE
            case _:
                logger.error("Unknown actoid type")
                return False

    def resolve_action(self, action_type, args, combatant):
        """
        The core of action resolution
        @param action_type: action type
        @param args: packed arguments of the action, can take on different interpretations based on the action_type
        @param combatant: originator of the action
        @return: only relevant return here is DMG/MISS used for sentinel
        """
        if action_type is MetaAction.DONE:
            return ActionResult.NOP
        action = action_factory(combatant, self.effect_tracker, action_type, *args)
        feasible = check_feasibility(combatant, action, self.battle_map)
        if not feasible and combatant.has_action:
            action = Dodge(combatant)
            logger.warning(f"Action of type {action_type} by {combatant} is non-feasible. Dodging instead.")
        elif not feasible:
            logger.warning(f"Action of type {action_type} by {combatant} is non-feasible.")
            return ActionResult.UNFEASIBLE
        use_resources(combatant, action)
        return self.resolve_by_actoid_type(action, combatant)

    def resolve_action_train(self, action_type, arg1, arg2, combatant):
        """
        The core of action resolution for the training mode
        @param action_type: action type
        @param arg1: can take on different interpretations based on the action_type
        @param arg2: can take on different interpretations based on the action_type
        @param combatant: originator of the action
        @return: resolution of the action as ActionResult
        """
        if action_type is MetaAction.DONE:
            return ActionResult.NOP
        action = action_factory(combatant, self.effect_tracker, action_type, arg1, arg2)
        feasible = check_feasibility(combatant, action, self.battle_map)
        if not feasible and combatant.has_action:
            action = Dodge(combatant)
            logger.warning(f"Action of type {action_type} by {combatant} is non-feasible. Dodging instead.")
        elif not feasible:
            logger.warning(f"Action of type {action_type} by {combatant} is non-feasible.")
            return ActionResult.UNFEASIBLE
        use_resources(combatant, action)
        result = self.resolve_by_actoid_type(action, combatant)
        return result if feasible else ActionResult.UNFEASIBLE

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
