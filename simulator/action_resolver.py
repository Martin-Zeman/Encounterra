from simulator.abilities.reckless_attack import RecklessAttack
from simulator.actions.action_types import BonusAction, Action, Reaction, Passive, Movement, HasteAction
from simulator.actions.flaming_sphere_ram import FlamingSphereRamFactory
from simulator.misc import *
from simulator.misc import SavingThrow
from simulator.feasibility import check_feasibility
from simulator.resources import use_resources
from simulator.actions.actoid import ActoidFlags
from enum import Enum, auto

from simulator.spells.chaosbolt import ChaosboltFactory
from simulator.spells.faerie_fire import FaerieFire

logger = logging.getLogger("EncounTroll")

class ActionResult(Enum):
    # TODO get rid of this
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
    if RollModifier.ADVANTAGE in target.saving_throws_roll_mod[ability.factory.saving_throw]:
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
    if RollModifier.DISADVANTAGE in target.saving_throws_roll_mod[ability.factory.saving_throw]:
        return True
    if ability.factory.saving_throw is SavingThrow.DEX and target.is_affected_by_any(Conditions.RESTRAINED):
        return True
    return False


def resolve_dmg_saving_throw(ability, dmg, target_combatant, half_on_success=True):
    # TODO prompt reaction
    # TODO Conditions
    bonus = target_combatant.saving_throws[ability.factory.saving_throw]
    modifiers = {has_advantage_saving_throw(ability, target_combatant), has_disadvantage_saving_throw(ability, target_combatant)}
    final_modifier = reconcile_roll_modifiers(modifiers)

    if final_modifier is RollModifier.STRAIGHT:
        rolled = random.randint(1, 20)
    elif final_modifier is RollModifier.ADVANTAGE:
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
    if not saved:
        target_combatant.receive_dmg(dmg, ability.factory.dmg_type)
        logger.info(f"{type(ability).__name__} deals {dmg} to {target_combatant}")
    elif half_on_success:
        target_combatant.receive_dmg(dmg // 2, ability.factory.dmg_type)
        logger.info(f"{type(ability).__name__} deals {dmg // 2} to {target_combatant}")


def resolve_on_hit_dmg_saving_throw(ability, dmg, target_combatant, half_on_success=True):
    # TODO prompt reaction
    # TODO Conditions
    bonus = target_combatant.saving_throws[ability.st]
    modifiers = {has_advantage_saving_throw(ability, target_combatant), has_disadvantage_saving_throw(ability, target_combatant)}
    final_modifier = reconcile_roll_modifiers(modifiers)

    if final_modifier is RollModifier.STRAIGHT:
        rolled = random.randint(1, 20)
    elif final_modifier is RollModifier.ADVANTAGE:
        rolled = max(random.randint(1, 20), random.randint(1, 20))
    else:
        rolled = min(random.randint(1, 20), random.randint(1, 20))

    if rolled == 1:
        saved = False
    elif rolled == 20:
        saved = True
    elif rolled + bonus >= ability.dc:
        saved = True
    else:
        saved = False
    if not saved:
        target_combatant.receive_dmg(dmg, ability.dmg_type)
        logger.info(f"{ability.name} deals extra {dmg} to {target_combatant}")
    elif half_on_success:
        target_combatant.receive_dmg(dmg // 2, ability.dmg_type)
        logger.info(f"{ability.name} deals extra {dmg // 2} to {target_combatant}")

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
            logger.info(f"{attacker} gains advantage since {target} attacked recklessly")
            return RollModifier.ADVANTAGE
        if self.effect_tracker.is_affecting_combatant(target, FaerieFire):
            return RollModifier.ADVANTAGE
        return RollModifier.STRAIGHT

    def has_disadvantage_spell_ranged(self, attack, attacker, target):
        if attack.roll_modifier is RollModifier.DISADVANTAGE:
            return RollModifier.DISADVANTAGE
        if target.disadvantage_on_incoming_attacks:
            return RollModifier.DISADVANTAGE
        if target.is_dodging:
            return RollModifier.DISADVANTAGE
        if self.battle_map.is_enemy_adjacent(attacker):
            return RollModifier.DISADVANTAGE
        return RollModifier.STRAIGHT

    def has_disadvantage_ranged(self, attack, attacker, target):
        if attack.roll_modifier is RollModifier.DISADVANTAGE:
            return RollModifier.DISADVANTAGE
        if target.disadvantage_on_incoming_attacks:
            return RollModifier.DISADVANTAGE
        if target.is_dodging:
            return RollModifier.DISADVANTAGE
        if self.battle_map.get_cartesian_distance(attacker, target) > attack.factory.short_range:
            return RollModifier.DISADVANTAGE
        if self.battle_map.is_enemy_adjacent(attacker):
            return RollModifier.DISADVANTAGE
        return RollModifier.STRAIGHT

    def resolve_chaos_bolt(self, caster, spell):
        # TODO Conditions
        jump = True
        curr_target = spell.target
        potential_targets = self.teams.get_allies(curr_target)
        while jump:
            jump = False
            modifiers = {self.has_advantage_ranged(spell, caster, curr_target), self.has_disadvantage_spell_ranged(spell, caster, curr_target)}
            final_modifier = reconcile_roll_modifiers(modifiers)

            if final_modifier is RollModifier.STRAIGHT:
                rolled = random.randint(1, 20)
            elif final_modifier is RollModifier.ADVANTAGE:
                rolled = max(random.randint(1, 20), random.randint(1, 20))
            else:
                rolled = min(random.randint(1, 20), random.randint(1, 20))

            multiplier = 1
            if rolled == 1:
                logger.info("Natural 1 rolled!", extra={"team": self.teams.get_team(caster)})
                return ActionResult.MISS
            elif rolled == 20:
                multiplier = 2

            if rolled + spell.to_hit >= curr_target.ac:
                bolt_dmg, rolled_numbers = roll_chaos_bolt_dmg(spell.factory.dmg_dice, spell.additional_dmg_dice)
                dmg_type = ChaosboltFactory.DMG_TYPE[rolled_numbers[random.randint(0, 1)] - 1]  # take one of the two numbers randomly
                dmg = multiplier * bolt_dmg
                logger.info(f"Chaosbolt {'CRITS' if multiplier == 2 else 'hits'} {curr_target} for {dmg} damage",
                             extra={"team": self.teams.get_team(caster)})
                curr_target.receive_dmg(dmg, dmg_type)
                if not curr_target.is_alive():
                    self.battle_map.remove_dead_combatant(curr_target)
                if rolled_numbers[0] == rolled_numbers[1]:
                    for i, potential_target in enumerate(potential_targets):
                        if not potential_target.is_alive():
                            continue
                        dist = self.battle_map.get_cartesian_distance(curr_target, potential_target)
                        if dist and dist <= 6:
                            curr_target = potential_target
                            logger.info(f"Chaos bolt jumping to {potential_target}!", extra={"team": self.teams.get_team(caster)})
                            jump = True
                            del potential_targets[i]
                            break
                return ActionResult.DMG
            else:
                logger.info(f"Chaosbolt misses {curr_target}", extra={"team": self.teams.get_team(caster)})
                return ActionResult.MISS

    def resolve_ranged_spell_attack(self, caster, spell, target):
        # TODO Conditions
        modifiers = {self.has_advantage_ranged(spell, caster, target), self.has_disadvantage_spell_ranged(spell, caster, target)}
        final_modifier = reconcile_roll_modifiers(modifiers)

        if final_modifier is RollModifier.STRAIGHT:
            rolled = random.randint(1, 20)
        elif final_modifier is final_modifier.ADVANTAGE:
            logger.info(f"{caster} rolls for {spell} with advantage", extra={"team": self.teams.get_team(caster)})
            rolled = max(random.randint(1, 20), random.randint(1, 20))
        else:
            logger.info(f"{caster} rolls for {spell} with disadvantage", extra={"team": self.teams.get_team(caster)})
            rolled = min(random.randint(1, 20), random.randint(1, 20))

        multiplier = 1
        if rolled == 1:
            logger.info("Natural 1 rolled!", extra={"team": self.teams.get_team(caster)})
            return ActionResult.MISS
        elif rolled == 20:
            multiplier = 2

        if rolled + spell.factory.to_hit >= target.ac:
            dmg = multiplier * roll_spell_dmg(spell.factory.dmg_dice)
            logger.info(f"{spell} {'CRITS' if multiplier == 2 else 'hits'} {target} for {dmg} damage",
                         extra={"team": self.teams.get_team(caster)})
            target.receive_dmg(dmg, spell.factory.dmg_type)
            if not target.is_alive():
                self.battle_map.remove_dead_combatant(target)
            return ActionResult.DMG
        else:
            logger.info(f"{spell} misses {target}", extra={"team": self.teams.get_team(caster)})
            return ActionResult.MISS

    def resolve_spell(self, caster, spell):
        logger.info(f"{caster} casts {spell}", extra={"team": caster.team_color})
        match spell.factory.action_type:
            case Action.FIREBALL | BonusAction.QUICKENED_FIREBALL:
                affected = self.battle_map.get_combatants_affected_by_aoe(caster, spell.factory.target, spell.factory.type, spell.coord)
                dmg = roll_spell_dmg(spell.factory.dmg_dice)
                for combatant in affected:
                    logger.info(f"{combatant} is hit by Fireball")
                    resolve_dmg_saving_throw(spell, dmg, combatant)
                    if not combatant.is_alive():
                        # TODO revisit if this is really needed
                        self.battle_map.remove_dead_combatant(combatant)
                return ActionResult.DMG
            case Action.HASTE | Action.TWINNED_HASTE | BonusAction.QUICKENED_HASTE:
                spell.activate(None)
                self.effect_tracker.add(spell, caster)
                return ActionResult.MEDIUM_BUFF
            case Action.FAERIE_FIRE | BonusAction.QUICKENED_FAERIE_FIRE:
                spell.activate(self.battle_map)
                self.effect_tracker.add(spell, caster)
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
            case Action.SCORCHING_RAY | BonusAction.QUICKENED_SCORCHING_RAY:
                ret = (self.resolve_ranged_spell_attack(caster, spell, spell.targets[0]),
                       self.resolve_ranged_spell_attack(caster, spell, spell.targets[1]),
                       self.resolve_ranged_spell_attack(caster, spell, spell.targets[2]))
                return ActionResult.DMG if any([True if r is ActionResult.DMG else False for r in ret]) else ActionResult.MISS
            case Reaction.SHIELD:
                assert not caster.shield_spell_active
                caster.shield_spell_active = True
                caster.ac += 5
                return ActionResult.FEASIBLE
            case Action.FLAMING_SPHERE:
                spell.activate(None)
                self.effect_tracker.add(spell, caster)
                return ActionResult.FEASIBLE
            case _:
                logger.error("Unknown spell")
                return ActionResult.UNFEASIBLE

    def has_advantage_melee(self, attack, attacker, target):
        if attack.roll_modifier is RollModifier.ADVANTAGE:
            return RollModifier.ADVANTAGE
        if attacker.has_pack_tactics and self.battle_map.is_ally_adjacent_to_target(attacker, target):
            return RollModifier.ADVANTAGE
        if hasattr(attacker, "reckless_attack_active") and attacker.reckless_attack_active:
            # TODO Consider moving this to the attack factory
            return RollModifier.ADVANTAGE
        if hasattr(target, "reckless_attack_active") and target.reckless_attack_active:
            logger.info(f"{attacker} gains advantage since {target} attacked recklessly")
            return RollModifier.ADVANTAGE
        if target.is_affected_by(Conditions.PRONE) and self.battle_map.get_hop_distance(attacker, target) == 1:
            return RollModifier.ADVANTAGE
        if self.effect_tracker.is_affecting_combatant(target, FaerieFire):
            return RollModifier.ADVANTAGE
        return RollModifier.STRAIGHT

    def has_disadvantage_melee(self, attack, attacker, target):
        if attack.roll_modifier is RollModifier.DISADVANTAGE:
            return RollModifier.DISADVANTAGE
        if target.disadvantage_on_incoming_attacks:
            return RollModifier.DISADVANTAGE
        if target.is_dodging:
            return RollModifier.DISADVANTAGE
        if attacker.is_affected_by(Conditions.PRONE):
            return RollModifier.DISADVANTAGE
        if target.is_affected_by(Conditions.PRONE) and self.battle_map.get_hop_distance(attacker, target) > 1:
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
        if FactoryFlags.IS_MELEE in attack.factory.flags:
            modifiers = {self.has_advantage_melee(attack, attacker, target), self.has_disadvantage_melee(attack, attacker, target)}
        else:
            modifiers = {self.has_advantage_ranged(attack, attacker, target), self.has_disadvantage_ranged(attack, attacker, target)}

        final_modifier = reconcile_roll_modifiers(modifiers)
        logger.info(f"{attacker} attacks {target} with {attack.shorthand_str()}" + (f" at {final_modifier.name}" if final_modifier is not RollModifier.STRAIGHT else ""), extra={"team": self.teams.get_team(attacker)})
        if final_modifier is RollModifier.STRAIGHT:
            rolled = random.randint(1, 20)
        elif final_modifier is RollModifier.ADVANTAGE:
            logger.info(f"{attacker} rolls for {attack} with advantage", extra={"team": self.teams.get_team(attacker)})
            rolled = max(random.randint(1, 20), random.randint(1, 20))
        else:
            logger.info(f"{attacker} rolls for {attack} with disadvantage", extra={"team": self.teams.get_team(attacker)})
            rolled = min(random.randint(1, 20), random.randint(1, 20))

        multiplier = 1
        if rolled == 1:
            logger.info("Natural 1 rolled!", extra={"team": self.teams.get_team(attacker)})
            return ActionResult.MISS
        elif rolled >= 21 - attack.factory.crit_range:
            multiplier = 2
        if rolled + attack.factory.to_hit >= target.ac:
            reaction = target.prompt_after_hit_reaction(attacker, rolled + attack.factory.to_hit)
            self.resolve_action(reaction, target)
        if rolled + attack.factory.to_hit >= target.ac:  # Potentially missing this time
            dice = parse_dmg_dice(attack.factory.dmg_dice)
            dmg_dice_sum = roll_dice(dice)
            total_dmg = multiplier * dmg_dice_sum + attack.factory.dmg_bonus + attacker.ability_dmg_bonus
            if attacker.has_passive(Passive.FANATIC_ADVANTAGE) and final_modifier is RollModifier.ADVANTAGE and not attacker.already_used_fanatic_advantage:
                logger.info(f"{attacker} activates Fanatic Advantage", extra={"team": self.teams.get_team(attacker)})
                attacker.already_used_fanatic_advantage = True
                total_dmg += roll_dice([(2, 6)])
            logger.info(
                f"The attack {'CRITS' if multiplier == 2 else 'hits'} {target} for {total_dmg} of which {attacker.ability_dmg_bonus} is ability dmg",
                extra={"team": self.teams.get_team(attacker)})
            target.receive_dmg(total_dmg, attack.get_dmg_type())
            if not target.is_alive():
                self.battle_map.remove_dead_combatant(target)
            elif attack.factory.on_hit is not None:
                attack.factory.on_hit.hit(attacker, attack, target, self.effect_tracker)

            return ActionResult.DMG
        else:
            logger.info(f"The attack misses {target}", extra={"team": self.teams.get_team(attacker)})
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
                            logger.info(f"Combatant {moving_combatant} was stopped by sentinel")

        if moving_combatant.is_alive():
            self.battle_map.move_combatant_by_increment(moving_combatant, movement.increment)
            return True
        return False

    def resolve_by_actoid_flags(self, actoid, combatant):
        """
        Resolves an action by its actoid type
        :param actoid: actoid to be resolved
        :param combatant: acting combatant
        :return: in case of an attack returns True if the attack hit, false otherwise. Dodge always returns True, unknown parameters false.
        Other cases return None.
        """
        assert actoid is not None
        match actoid.factory.action_type:
            case BonusAction.TOTEM_RAGE | BonusAction.RAGE | Action.DISENGAGE | Action.DODGE:
                actoid.activate(None)
                self.effect_tracker.add(actoid, combatant)
                return False
            case Action.RECKLESS_ATTACK:
                if not self.effect_tracker.is_affecting_combatant(combatant, RecklessAttack):
                    # don't need to add it again in case of a multi-attack
                    actoid.activate(None)
                    self.effect_tracker.add(actoid, combatant)
                    return self.resolve_attack(actoid, combatant)
            case Action.WILDSHAPE | BonusAction.MOON_WILDSHAPE:
                actoid.activate(self.battle_map)
                self.effect_tracker.add(actoid, combatant)
                return False
            case Action.FIREBALL | BonusAction.QUICKENED_FIREBALL:
                affected = self.battle_map.get_combatants_affected_by_aoe(combatant, actoid.factory.target, actoid.factory.type, actoid.coord)
                dmg = roll_spell_dmg(actoid.factory.dmg_dice)
                for combatant in affected:
                    logger.info(f"{combatant} is hit by Fireball")
                    resolve_dmg_saving_throw(actoid, dmg, combatant)
                    if not combatant.is_alive():
                        # TODO revisit if this is really needed
                        self.battle_map.remove_dead_combatant(combatant)
                return ActionResult.DMG
            case Action.HASTE | Action.TWINNED_HASTE | BonusAction.QUICKENED_HASTE:
                actoid.activate(None)
                self.effect_tracker.add(actoid, combatant)
                return ActionResult.MEDIUM_BUFF
            case Action.FAERIE_FIRE | BonusAction.QUICKENED_FAERIE_FIRE:
                actoid.activate(self.battle_map)
                self.effect_tracker.add(actoid, combatant)
            case Action.FIREBOLT | BonusAction.QUICKENED_FIREBOLT:
                return self.resolve_ranged_spell_attack(combatant, actoid, actoid.target)
            case Action.TWINNED_FIREBOLT:
                ret = (self.resolve_ranged_spell_attack(combatant, actoid, actoid.targets[0]),
                       self.resolve_ranged_spell_attack(combatant, actoid, actoid.targets[1]))
                return ActionResult.DMG if any([True if r is ActionResult.DMG else False for r in ret]) else ActionResult.MISS
            case BonusAction.MISTY_STEP:
                self.battle_map.move_combatant(combatant, actoid.coord)
                return ActionResult.FEASIBLE
            case Action.CHAOSBOLT | BonusAction.QUICKENED_CHAOSBOLT:
                return self.resolve_chaos_bolt(combatant, actoid)
            case Action.SCORCHING_RAY | BonusAction.QUICKENED_SCORCHING_RAY:
                ret = (self.resolve_ranged_spell_attack(combatant, actoid, actoid.targets[0]),
                       self.resolve_ranged_spell_attack(combatant, actoid, actoid.targets[1]),
                       self.resolve_ranged_spell_attack(combatant, actoid, actoid.targets[2]))
                return ActionResult.DMG if any([True if r is ActionResult.DMG else False for r in ret]) else ActionResult.MISS
            case Reaction.SHIELD:
                assert not combatant.shield_spell_active
                combatant.shield_spell_active = True
                combatant.ac += 5
                return ActionResult.FEASIBLE
            case Action.FLAMING_SPHERE:
                actoid.activate(None)
                self.effect_tracker.add(actoid, combatant)
                return ActionResult.FEASIBLE
            case Action.MELEE_ATTACK | Action.RANGED_ATTACK | BonusAction.BONUS_RANGED_ATTACK | BonusAction.BONUS_MELEE_ATTACK |\
                 HasteAction.HASTE_MELEE_ATTACK | HasteAction.HASTE_RANGED_ATTACK | BonusAction.PAM_BONUS_ATTACK:
                return self.resolve_attack(actoid, combatant)
            case Movement.STANDARD:
                if not self.request_movement(combatant, actoid):
                    return False
            case Movement.DASH:
                combatant.movement += combatant.speed
                return False
            case Movement.GET_UP_FROM_PRONE:
                logger.info(f"{combatant} gets up from being prone")
                combatant.remove_condition(Conditions.PRONE)  # resources already taken
                return False
            case Action.CONSTRICT:
                result = self.resolve_attack(actoid.factory.attack, combatant)
                if result is ActionResult.DMG:
                    combatant.is_constricting = True
                    return True
            case Action.BREAK_GRAPPLE:
                logger.info(f"{combatant} is trying to break out of grapple")
                grapple = actoid.factory.grapple_condition
                broken_out = roll_ability_check(max(combatant.athletics, combatant.acrobatics), grapple.dc)
                if broken_out and getattr(grapple.attacker, "is_constricting", False):  # TODO this is a simplification
                    logger.info(f"{combatant} is has broken out of grapple")
                    grapple.attacker.is_constricting = False
            case BonusAction.FLAMING_SPHERE_RAM:
                adj = self.battle_map.build_flaming_sphere_adjacency_matrix()
                _, shortest_paths = self.battle_map.dijkstra(actoid.factory.action_enabler_effect.coord, adj)
                path = self.battle_map.get_effect_path_to_coord(actoid.factory.action_enabler_effect.coord, actoid.coord)
                if len(path) <= FlamingSphereRamFactory.RANGE + 1:
                    pass  # TODO do the dmg
                path = path[:FlamingSphereRamFactory.RANGE + 1]
                actoid.move_effect(path[-1])  # TODO consider putting this into effect tracker
            case Action.POUNCE:
                # TODO
                return False
            case Action.WEB:
                # TODO
                return False
            case _:
                logger.error(f"Unknown actoid type! {actoid.factory.action_type}")

        return False


    def resolve_action(self, action, combatant):
        """
        The core of action resolution
        @param action_type: action type
        @param args: packed arguments of the action, can take on different interpretations based on the action_type
        @param combatant: originator of the action
        @return: only relevant return here is DMG/MISS used for sentinel
        """
        combatant = combatant.get_current_form()  # Takes care of possible wildshape
        if action is None:
            return None
        if not check_feasibility(combatant, action, self.battle_map):
            if action.factory.action_type is Movement.STANDARD:
                combatant.movement = 0  # This can be caused by difficult terrain which is ok but we must avoid endless looping
            else:
                logger.error(f"Action {action} by {combatant} is not feasible. This should not happen!")
            return None
        use_resources(combatant, action, self.battle_map)
        return self.resolve_by_actoid_flags(action, combatant)


    def resolve_effects(self, effects, combatant):
        """
        Applies the aspect of effects that need to be reapplied at the beginning of a turn or would otherwise be reset by the new turn
        :param effects:
        :param combatant:
        :return:
        """
        for effect in effects:
            match effect.__class__.__name__:
                case "Haste" | "TwinnedHaste":
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
