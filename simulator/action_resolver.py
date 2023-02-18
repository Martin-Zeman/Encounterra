from simulator.misc import *
from simulator.misc import SavingThrow
from simulator.feasibility import check_feasibility
from simulator.resources import use_resources
from simulator.action_factory import *
from simulator.actions.actoid import Actoid, ActoidFlags
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
    TRAINEE_DEAD = auto()

def has_advantage_saving_throw(ability, target):
    if RollModifier.ADVANTAGE in target.saving_throws[ability.factory.saving_throw][1]:
        return True
    if ability.factory.saving_throw is SavingThrow.DEX and target.has_passive(
            Passive.DANGER_SENSE) and not target.is_affected_by_any(Conditions.INCAPACITATED,
                                                                              Conditions.BLINDED,
                                                                              Conditions.DEAFENED):
        return RollModifier.ADVANTAGE
    if ability.factory.saving_throw is SavingThrow.DEX and target.is_dodging:
        return RollModifier.ADVANTAGE
    return RollModifier.STRAIGHT

def has_disadvantage_saving_throw(ability, target):
    if RollModifier.DISADVANTAGE in target.saving_throws[ability.factory.saving_throw][1]:
        return True
    if ability.factory.saving_throw is SavingThrow.DEX and target.is_affected_by_any(Conditions.RESTRAINED):
        return True
    return False


def resolve_dmg_saving_throw(ability, dmg, target_combatant):
    # TODO prompt reaction
    # TODO Conditions
    bonus = target_combatant.saving_throws[ability.factory.saving_throw][0]

    modifiers = {has_advantage_saving_throw(ability, target_combatant), has_disadvantage_saving_throw(ability, target_combatant)}
    final_modifier = reconcile_roll_modifiers(modifiers)

    if final_modifier == RollModifier.STRAIGHT:
        rolled = random.randint(1, 20)
    elif final_modifier == RollModifier.ADVANTAGE:
        rolled = max(random.randint(1, 20), random.randint(1, 20))
    else:
        rolled = min(random.randint(1, 20), random.randint(1, 20))

    if rolled == 1:
        saved = False
    elif rolled == 20:
        saved = True
    elif rolled + bonus >= ability.factory.dc:
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

    def has_advantage_ranged(self, attack, attacker, target):
        if attack.roll_modifier is RollModifier.ADVANTAGE:
            return RollModifier.ADVANTAGE
        if hasattr(target, "reckless_attack_active") and target.reckless_attack_active:
            logger.debug(f"{attacker} gains advantage since {target} attacked recklessly")
            return RollModifier.ADVANTAGE
        return RollModifier.STRAIGHT

    def has_disadvantage_spell_ranged(self, attack, attacker, target):
        if attack.roll_modifier is RollModifier.DISADVANTAGE:
            return RollModifier.DISADVANTAGE
        if target.disadvantage_on_incoming_attacks:
            return RollModifier.DISADVANTAGE
        if target.is_dodging:
            return RollModifier.DISADVANTAGE
        return RollModifier.STRAIGHT

    def has_disadvantage_ranged(self, attack, attacker, target):
        if attack.roll_modifier is RollModifier.DISADVANTAGE:
            return RollModifier.ADVANTAGE
        if target.disadvantage_on_incoming_attacks:
            return RollModifier.ADVANTAGE
        if target.is_dodging:
            return RollModifier.ADVANTAGE
        if self.battle_map.get_cartesian_distance(attacker, target) > attack.factory.short_range:
            return RollModifier.ADVANTAGE
        return RollModifier.STRAIGHT

    def resolve_chaos_bolt(self, caster, spell):
        # TODO Conditions
        jump = True
        curr_target = spell.targets[0]
        potential_targets = self.teams.get_allies(curr_target)
        while jump:
            jump = False
            modifiers = {self.has_advantage_ranged(spell, caster, curr_target), self.has_disadvantage_spell_ranged(spell, caster, curr_target)}
            final_modifier = reconcile_roll_modifiers(modifiers)

            if final_modifier == RollModifier.STRAIGHT:
                rolled = random.randint(1, 20)
            elif final_modifier == RollModifier.ADVANTAGE:
                rolled = max(random.randint(1, 20), random.randint(1, 20))
            else:
                rolled = min(random.randint(1, 20), random.randint(1, 20))

            multiplier = 1
            if rolled == 1:
                logger.debug("Natural 1 rolled!", extra={"team": self.teams.get_team(caster)})
                return ActionResult.MISS
            elif rolled == 20:
                multiplier = 2

            if rolled + spell.to_hit >= curr_target.ac:
                bolt_dmg, rolled_numbers = roll_chaos_bolt_dmg(spell.factory.dmg_dice, spell.additional_dmg_dice)
                dmg_type = Chaosbolt.DMG_TYPE[rolled_numbers[random.randint(0, 1)] - 1]  # take one of the two numbers randomly
                dmg = multiplier * bolt_dmg
                logger.debug(f"Chaosbolt {'CRITS' if multiplier == 2 else 'hits'} {curr_target} for {dmg} damage",
                             extra={"team": self.teams.get_team(caster)})
                curr_target.receive_dmg(dmg, dmg_type)
                if not curr_target.is_alive():
                    self.battle_map.remove_combatant(curr_target)
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
                logger.debug(f"Chaosbolt misses {curr_target}", extra={"team": self.teams.get_team(caster)})
                return ActionResult.MISS

    def resolve_ranged_spell_attack(self, caster, spell, target):
        # TODO Conditions
        modifiers = {self.has_advantage_ranged(spell, caster, target), self.has_disadvantage_spell_ranged(spell, caster, target)}
        final_modifier = reconcile_roll_modifiers(modifiers)

        if final_modifier == RollModifier.STRAIGHT:
            rolled = random.randint(1, 20)
        elif final_modifier.ADVANTAGE:
            rolled = max(random.randint(1, 20), random.randint(1, 20))
        else:
            rolled = min(random.randint(1, 20), random.randint(1, 20))

        multiplier = 1
        if rolled == 1:
            logger.debug("Natural 1 rolled!", extra={"team": self.teams.get_team(caster)})
            return ActionResult.MISS
        elif rolled == 20:
            multiplier = 2

        if rolled + spell.factory.to_hit >= target.ac:
            dmg = multiplier * roll_spell_dmg(spell.factory.dmg_dice)
            logger.debug(f"{spell} {'CRITS' if multiplier == 2 else 'hits'} {target} for {dmg} damage",
                         extra={"team": self.teams.get_team(caster)})
            spell.target.receive_dmg(dmg, spell.dmg_type)
            if not spell.target.is_alive():
                self.battle_map.remove_combatant(target)
            return ActionResult.DMG
        else:
            logger.debug(f"{spell} misses {target}", extra={"team": self.teams.get_team(caster)})
            return ActionResult.MISS

    def resolve_spell(self, caster, spell):
        match spell.factory.action_type:
            case Action.FIREBALL | BonusAction.QUICKENED_FIREBALL:
                affected = self.battle_map.get_combatants_affected_by_aoe(caster, spell.target, spell.type, spell.coord)
                dmg = roll_spell_dmg(spell.factory.dmg_dice)
                for combatant in affected:
                    logger.debug(f"{combatant} is hit by Fireball")
                    resolve_dmg_saving_throw(spell, dmg, combatant)
                    if not combatant.is_alive():
                        # TODO revisit if this is really needed
                        self.battle_map.remove_combatant(combatant)
                return ActionResult.DMG
            case Action.HASTE | BonusAction.QUICKENED_HASTE:
                spell.activate()
                self.effect_tracker.add(spell, caster)
                return ActionResult.MEDIUM_BUFF
            case Action.FIREBOLT | BonusAction.QUICKENED_FIREBOLT:
                return self.resolve_ranged_spell_attack(caster, spell, spell.target)
            case Action.TWINNED_FIREBOLT:
                ret = (self.resolve_ranged_spell_attack(caster, spell, spell.targets[0]),
                       self.resolve_ranged_spell_attack(caster, spell, spell.targets[1]))
                return ActionResult.DMG if any([True if r is ActionResult.DMG else False for r in ret]) else ActionResult.MISS
            case BonusAction.MISTY_STEP:
                self.battle_map.move_combatant(caster, spell.coord)
                return ActionResult.FEASIBLE
            case Action.CHAOSBOLT | BonusAction.QUICKENED_CHAOSBOLT:
                return self.resolve_chaos_bolt(caster, spell)
            case Reaction.SHIELD:
                assert not caster.shield_spell_active
                caster.shield_spell_active = True
                caster.ac += 5
                return ActionResult.FEASIBLE
            case _:
                logger.error("Unknown spell")
                return ActionResult.UNFEASIBLE

    def has_advantage_melee(self, attack, attacker, target):
        try:
            if attack.roll_modifier is RollModifier.ADVANTAGE:
                return RollModifier.ADVANTAGE
        except AttributeError:
            print("FIXME")
        if attacker.has_pack_tactics and self.battle_map.is_ally_adjacent(attacker, target):
            return RollModifier.ADVANTAGE
        if hasattr(attacker, "reckless_attack_active") and attacker.reckless_attack_active:
            # TODO Consider moving this to the attack factory
            return RollModifier.ADVANTAGE
        if hasattr(target, "reckless_attack_active") and target.reckless_attack_active:
            logger.debug(f"{attacker} gains advantage since {target} attacked recklessly")
            return RollModifier.ADVANTAGE
        return RollModifier.STRAIGHT

    def has_disadvantage_melee(self, attack, attacker, target):
        if attack.roll_modifier is RollModifier.DISADVANTAGE:
            return RollModifier.DISADVANTAGE
        if target.disadvantage_on_incoming_attacks:
            return RollModifier.DISADVANTAGE
        if target.is_dodging:
            return RollModifier.DISADVANTAGE
        return RollModifier.STRAIGHT

    def resolve_attack(self, attack, attacker):  # TODO remove combatant from attack and have it as a separate parameter
        """

        :param attack:
        :return: True is hits, false if misses or is not attack
        """
        # TODO Conditions
        target = attack.target_combatant
        assert target
        logger.debug(f"{attacker} attacks {target} with {attack}", extra={"team": self.teams.get_team(attacker)})
        if attack.factory.attack_type is AttackFactory.Type.MELEE:
            modifiers = {self.has_advantage_melee(attack, attacker, target), self.has_disadvantage_melee(attack, attacker, target)}
        else:
            modifiers = {self.has_advantage_ranged(attack, attacker, target), self.has_disadvantage_ranged(attack, attacker, target)}

        final_modifier = reconcile_roll_modifiers(modifiers)
        if final_modifier is RollModifier.STRAIGHT:
            rolled = random.randint(1, 20)
        elif final_modifier is RollModifier.ADVANTAGE:
            rolled = max(random.randint(1, 20), random.randint(1, 20))
        else:
            rolled = min(random.randint(1, 20), random.randint(1, 20))

        multiplier = 1
        if rolled == 1:
            logger.debug("Natural 1 rolled!", extra={"team": self.teams.get_team(attacker)})
            return ActionResult.MISS
        elif rolled in attack.factory.crit_range:
            multiplier = 2
        if rolled + attack.factory.to_hit >= target.ac:
            reaction = target.prompt_after_hit_reaction(attacker, rolled + attack.factory.to_hit)
            self.resolve_action(reaction, target)
        if rolled + attack.factory.to_hit >= target.ac:  # Potentially missing this time
            dice = parse_dmg_dice(attack.factory.dmg_dice)
            dmg_dice_sum = roll_dice(dice)
            total_dmg = multiplier * dmg_dice_sum + attack.factory.dmg_bonus + attacker.ability_dmg_bonus
            logger.debug(
                f"The attack {'CRITS' if multiplier == 2 else 'hits'} {target} for {total_dmg} of which {attacker.ability_dmg_bonus} is ability dmg",
                extra={"team": self.teams.get_team(attacker)})
            target.receive_dmg(total_dmg, attack.get_dmg_type())
            if not target.is_alive():
                self.battle_map.remove_combatant(target)
            return ActionResult.DMG
        else:
            logger.debug(f"The attack misses {target}", extra={"team": self.teams.get_team(attacker)})
            return ActionResult.MISS

    def request_movement(self, moving_combatant, movement):
        if movement.incurs_aoo:
            aoo_candidates = self.battle_map.get_aoo_eligible_combatants(moving_combatant, movement.increment)
            if aoo_candidates:
                for candidate in aoo_candidates:
                    aoo = candidate.prompt_aoo(moving_combatant)
                    if aoo and moving_combatant.is_alive():
                        self.resolve_action(aoo, candidate)

            pam_candidates = self.battle_map.get_pam_eligible_combatants(moving_combatant, movement.increment)
            if pam_candidates:
                for candidate in pam_candidates:
                    pam_attack = candidate.prompt_pam(moving_combatant)
                    if pam_attack and moving_combatant.is_alive():
                        did_attack_hit = self.resolve_action(pam_attack, candidate)
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
        # TODO Rework this using the new Actoid concept
        if ActoidFlags.IS_ATTACK_LIKE in actoid.actoid_type:
            return self.resolve_attack(actoid, combatant)
        elif ActoidFlags.IS_MOVEMENT in actoid.actoid_type:
            if not self.request_movement(combatant, actoid):
                return ActionResult.UNFEASIBLE  # combatant didn't survive
        elif ActoidFlags.IS_SPELL in actoid.actoid_type:
            return self.resolve_spell(combatant, actoid)
        # elif ActoidFlags.IS_DODGE:
        #     combatant.is_dodging = True
        #     combatant.saving_throws[SavingThrow.DEX][1] = RollModifier.ADVANTAGE
        #     return ActionResult.FEASIBLE
        elif ActoidFlags.IS_DASH in actoid.actoid_type:
            combatant.movement += combatant.speed
            return ActionResult.FEASIBLE
        elif ActoidFlags.IS_TOGGLE_ABILITY in actoid.actoid_type:
            self.resolve_toggle_ability(combatant, actoid)
            return ActionResult.FEASIBLE
        else:
            logger.error("Unknown actoid type")
            return False

    # def resolve_action(self, action_type, args, combatant):
    #     """
    #     The core of action resolution
    #     @param action_type: action type
    #     @param args: packed arguments of the action, can take on different interpretations based on the action_type
    #     @param combatant: originator of the action
    #     @return: only relevant return here is DMG/MISS used for sentinel
    #     """
    #     if action_type is MetaAction.DONE:
    #         return ActionResult.NOP
    #     action = action_factory(combatant, self.effect_tracker, action_type, *args)
    #     feasible = check_feasibility(combatant, action, self.battle_map)
    #     if not feasible and combatant.has_action:
    #         action = Dodge(combatant)
    #         logger.debug(f"Action of type {action_type} by {combatant} is non-feasible. Dodging instead.")
    #     elif not feasible:
    #         logger.debug(f"Action of type {action_type} by {combatant} is non-feasible.")
    #         return ActionResult.UNFEASIBLE
    #     use_resources(combatant, action)
    #     return self.resolve_by_actoid_type(action, combatant)


    def resolve_action(self, action, combatant):
        """
        The core of action resolution
        @param action_type: action type
        @param args: packed arguments of the action, can take on different interpretations based on the action_type
        @param combatant: originator of the action
        @return: only relevant return here is DMG/MISS used for sentinel
        """
        if action is None:
            return None
        # action = action_factory(combatant, self.effect_tracker, action_type, *args)
        if not check_feasibility(combatant, action, self.battle_map):
            logger.error(f"Action {action} by {combatant} is not feasible. This should not happen!")
            return None
        # if not feasible and combatant.has_action:
        #     action = Dodge(combatant)
        #     logger.debug(f"Action of type {action_type} by {combatant} is non-feasible. Dodging instead.")
        # elif not feasible:
        #     logger.debug(f"Action of type {action_type} by {combatant} is non-feasible.")
        #     return ActionResult.UNFEASIBLE
        use_resources(combatant, action)
        return self.resolve_by_actoid_type(action, combatant)

    def resolve_action_train(self, action_type, args, combatant):
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
        action = action_factory(combatant, self.effect_tracker, action_type, *args)
        feasible = check_feasibility(combatant, action, self.battle_map)
        if not feasible and combatant.has_action:
            action = Dodge(combatant)
            logger.debug(f"Action of type {action_type} by {combatant} is non-feasible. Dodging instead.")
        elif not feasible:
            logger.debug(f"Action of type {action_type} by {combatant} is non-feasible.")
            return ActionResult.UNFEASIBLE
        use_resources(combatant, action)
        result = self.resolve_by_actoid_type(action, combatant)
        if not combatant.is_alive():
            # could have nuked itself with an AoE...
            return ActionResult.TRAINEE_DEAD
        return result if feasible else ActionResult.UNFEASIBLE

    def resolve_toggle_ability(self, combatant, ability):
        # match ability.__class__.__name__:
        #     case "TotemRage" | "Rage" | "RecklessAttack":
        ability.activate()
        self.effect_tracker.add(ability, combatant)
            # case _:
            #     logger.error("Unknown toggle ability")

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
