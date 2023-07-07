import math

from simulator.abilities.reckless_attack import RecklessAttack
from simulator.actions.action_types import BonusAction, Action, Reaction, Passive, Movement, HasteAction
from simulator.actions.dodge import DodgeFactory
from simulator.actions.flaming_sphere_ram import FlamingSphereRamFactory
from simulator.battle_map import Map
from simulator.effects.effect import EffectType
from simulator.misc import *
from simulator.misc import SavingThrow
from simulator.feasibility import check_feasibility
from simulator.resources import use_resources
from enum import Enum, auto

from simulator.spells.chaosbolt import ChaosboltFactory
from simulator.spells.faerie_fire import FaerieFire
from simulator.spells.magic_missile import MagicMissileFactory

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
    if RollType.ADVANTAGE in target.saving_throws_roll_type_mod[ability.factory.saving_throw]:
        return True
    if ability.factory.saving_throw is SavingThrow.DEX and target.has_passive(
            Passive.DANGER_SENSE) and not target.is_affected_by_any(Conditions.INCAPACITATED,
                                                                              Conditions.BLINDED,
                                                                              Conditions.DEAFENED):
        return RollType.ADVANTAGE
    if ability.factory.saving_throw is SavingThrow.DEX and target.is_dodging:
        return RollType.ADVANTAGE
    return RollType.STRAIGHT

def has_disadvantage_saving_throw(ability, target):
    if RollType.DISADVANTAGE in target.saving_throws_roll_type_mod[ability.factory.saving_throw]:
        return True
    if ability.factory.saving_throw is SavingThrow.DEX and target.is_affected_by_any(Conditions.RESTRAINED):
        return True
    return False


def resolve_dmg_saving_throw(ability, dmg, target_combatant, half_on_success=True):
    # TODO prompt reaction
    # TODO Conditions
    bonus = target_combatant.saving_throws[ability.factory.saving_throw]
    types = {has_advantage_saving_throw(ability, target_combatant), has_disadvantage_saving_throw(ability, target_combatant)}
    final_modifier = reconcile_roll_types(types)

    if final_modifier is RollType.STRAIGHT:
        rolled = random.randint(1, 20)
    elif final_modifier is RollType.ADVANTAGE:
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
        logger.info(f"{ability.shorthand_str()} deals {dmg} to {target_combatant}")
        target_combatant.receive_dmg(dmg, ability.factory.dmg_type)
    elif half_on_success:
        logger.info(f"{ability.shorthand_str()} deals {dmg // 2} to {target_combatant}")
        target_combatant.receive_dmg(dmg // 2, ability.factory.dmg_type)


def resolve_on_hit_dmg_saving_throw(ability, dmg, target_combatant, half_on_success=True):
    # TODO prompt reaction
    # TODO Conditions
    bonus = target_combatant.saving_throws[ability.st]
    types = {has_advantage_saving_throw(ability, target_combatant), has_disadvantage_saving_throw(ability, target_combatant)}
    final_modifier = reconcile_roll_types(types)

    if final_modifier is RollType.STRAIGHT:
        rolled = random.randint(1, 20)
    elif final_modifier is RollType.ADVANTAGE:
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

    def __init__(self, combatants, teams, effect_tracker):
        self.combatants = combatants
        self.teams = teams
        self.effect_tracker = effect_tracker

    def has_advantage_ranged(self, attack, attacker, target):
        if attack.roll_type is RollType.ADVANTAGE:
            return RollType.ADVANTAGE
        if Map.get().effect_tracker.is_affecting_combatant(target, RecklessAttack):
            logger.info(f"{attacker} gains advantage since {target} attacked recklessly")
            return RollType.ADVANTAGE
        if target.is_affected_by_any(Conditions.RESTRAINED, Conditions.STUNNED, Conditions.PARALYZED, Conditions.BLINDED, Conditions.PETRIFIED):
            return RollType.ADVANTAGE
        if self.effect_tracker.is_affecting_combatant(target, FaerieFire):
            return RollType.ADVANTAGE
        if attacker.is_affected_by(Conditions.INVISIBLE):
            return RollType.ADVANTAGE
        return RollType.STRAIGHT

    def has_advantage_melee(self, attack, attacker, target):
        battle_map = Map.get()
        if attack.roll_type is RollType.ADVANTAGE:
            return RollType.ADVANTAGE
        if attacker.has_pack_tactics and battle_map.is_ally_adjacent_to_target(attacker, target):
            return RollType.ADVANTAGE
        if battle_map.effect_tracker.is_affecting_combatant(attacker, RecklessAttack):
            return RollType.ADVANTAGE
        if battle_map.effect_tracker.is_affecting_combatant(target, RecklessAttack):
            logger.info(f"{attacker} gains advantage since {target} attacked recklessly")
            return RollType.ADVANTAGE
        if target.is_affected_by(Conditions.PRONE) and battle_map.get_hop_distance(attacker, target) == 1:
            return RollType.ADVANTAGE
        if self.effect_tracker.is_affecting_combatant(target, FaerieFire):
            return RollType.ADVANTAGE
        if target.is_affected_by_any(Conditions.RESTRAINED, Conditions.STUNNED, Conditions.PARALYZED, Conditions.BLINDED, Conditions.PETRIFIED):
            return RollType.ADVANTAGE
        if attacker.is_affected_by(Conditions.INVISIBLE):
            return RollType.ADVANTAGE
        if target.wears_metal and (attack.factory.action_type is Action.SHOCKING_GRASP or attack.factory.action_type is BonusAction.QUICKENED_SHOCKING_GRASP or attack.factory.action_type is Action.TWINNED_SHOCKING_GRASP):
            return RollType.ADVANTAGE
        return RollType.STRAIGHT

    def has_disadvantage_spell_ranged(self, attack, attacker, target):
        battle_map = Map.get()
        if attack.roll_type is RollType.DISADVANTAGE:
            return RollType.DISADVANTAGE
        if target.disadvantage_on_incoming_attacks:
            return RollType.DISADVANTAGE
        if target.is_dodging:
            return RollType.DISADVANTAGE
        if battle_map.is_enemy_adjacent(attacker):
            return RollType.DISADVANTAGE
        if target.is_affected_by(Conditions.PRONE) and battle_map.get_hop_distance(attacker, target) > 1:
            return RollType.DISADVANTAGE
        if target.is_affected_by(Conditions.INVISIBLE):
            return RollType.DISADVANTAGE
        if attacker.is_affected_by_any(Conditions.PRONE, Conditions.POISONED, Conditions.BLINDED, Conditions.RESTRAINED):
            return RollType.DISADVANTAGE
        return RollType.STRAIGHT

    def has_disadvantage_ranged(self, attack, attacker, target):
        battle_map = Map.get()
        if attack.roll_type is RollType.DISADVANTAGE:
            return RollType.DISADVANTAGE
        if target.disadvantage_on_incoming_attacks:
            return RollType.DISADVANTAGE
        if target.is_dodging:
            return RollType.DISADVANTAGE
        if battle_map.get_cartesian_distance(attacker, target) > attack.factory.short_range:
            return RollType.DISADVANTAGE
        if battle_map.is_enemy_adjacent(attacker):
            return RollType.DISADVANTAGE
        if target.is_affected_by(Conditions.PRONE) and battle_map.get_hop_distance(attacker, target) > 1:
            return RollType.DISADVANTAGE
        if target.is_affected_by(Conditions.INVISIBLE):
            return RollType.DISADVANTAGE
        if attacker.is_affected_by_any(Conditions.PRONE, Conditions.POISONED, Conditions.BLINDED, Conditions.RESTRAINED):
            return RollType.DISADVANTAGE
        return RollType.STRAIGHT

    def has_disadvantage_melee(self, attack, attacker, target):
        if attack.roll_type is RollType.DISADVANTAGE:
            return RollType.DISADVANTAGE
        if target.disadvantage_on_incoming_attacks:
            return RollType.DISADVANTAGE
        if target.is_dodging:
            return RollType.DISADVANTAGE
        if attacker.is_affected_by_any(Conditions.PRONE, Conditions.POISONED):
            return RollType.DISADVANTAGE
        if target.is_affected_by(Conditions.PRONE) and Map.get().get_hop_distance(attacker, target) > 1:
            return RollType.DISADVANTAGE
        if target.is_affected_by(Conditions.INVISIBLE):
            return RollType.DISADVANTAGE
        return RollType.STRAIGHT

    def resolve_chaos_bolt(self, caster, spell):
        # TODO Conditions
        battle_map = Map.get()
        jump = True
        curr_target = spell.target
        potential_targets = self.teams.get_allies(curr_target)
        while jump:
            jump = False
            types = {self.has_advantage_ranged(spell, caster, curr_target), self.has_disadvantage_spell_ranged(spell, caster, curr_target)}
            final_modifier = reconcile_roll_types(types)

            if final_modifier is RollType.STRAIGHT:
                logger.info(f"{caster} rolls for {spell}", extra={"team": self.teams.get_team(caster)})
                rolled = random.randint(1, 20)
            elif final_modifier is RollType.ADVANTAGE:
                logger.info(f"{caster} rolls for {spell} at advantage", extra={"team": self.teams.get_team(caster)})
                rolled = max(random.randint(1, 20), random.randint(1, 20))
            else:
                logger.info(f"{caster} rolls for {spell} at disadvantage", extra={"team": self.teams.get_team(caster)})
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
                battle_map.remove_combatant_if_dead(curr_target)  # could be a wildshaped druid
                if rolled_numbers[0] == rolled_numbers[1]:
                    for i, potential_target in enumerate(potential_targets):
                        if not potential_target.is_alive():
                            continue
                        dist = battle_map.get_cartesian_distance(curr_target, potential_target)
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
        types = {self.has_advantage_ranged(spell, caster, target), self.has_disadvantage_spell_ranged(spell, caster, target)}
        final_modifier = reconcile_roll_types(types)

        if final_modifier is RollType.STRAIGHT:
            logger.info(f"{caster} rolls for {spell}", extra={"team": self.teams.get_team(caster)})
            rolled = random.randint(1, 20)
        elif final_modifier is final_modifier.ADVANTAGE:
            logger.info(f"{caster} rolls for {spell} at advantage", extra={"team": self.teams.get_team(caster)})
            rolled = max(random.randint(1, 20), random.randint(1, 20))
        else:
            logger.info(f"{caster} rolls for {spell} at disadvantage", extra={"team": self.teams.get_team(caster)})
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
            Map.get().remove_combatant_if_dead(target)  # could be a wildshaped druid
            return ActionResult.DMG
        else:
            logger.info(f"{spell} misses {target}", extra={"team": self.teams.get_team(caster)})
            return ActionResult.MISS


    def resolve_attack(self, attack, attacker):  # TODO remove combatant from attack and have it as a separate parameter
        """

        :param attack:
        :return: True is hits, false if misses or is not attack
        """
        # TODO Conditions
        target = attack.target_combatant
        assert target
        types = {self.has_advantage_melee(attack, attacker, target), self.has_disadvantage_melee(attack, attacker, target)}

        final_modifier = reconcile_roll_types(types)
        if final_modifier is RollType.STRAIGHT:
            logger.info(f"{attacker} attacks {target} with {attack.shorthand_str()}", extra={"team": self.teams.get_team(attacker)})
            rolled = random.randint(1, 20)
        elif final_modifier is RollType.ADVANTAGE:
            logger.info(f"{attacker} attacks {target} with {attack.shorthand_str()} at advantage", extra={"team": self.teams.get_team(attacker)})
            rolled = max(random.randint(1, 20), random.randint(1, 20))
        else:
            logger.info(f"{attacker} attacks {target} with {attack.shorthand_str()} at disadvantage", extra={"team": self.teams.get_team(attacker)})
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
            # logger.info(f"Rolled {dmg_dice_sum} on the dmg dice", extra={"team": self.teams.get_team(attacker)})
            extra_dmg = [(multiplier * roll_dice(parse_dmg_dice(e[0])), e[1]) for e in attack.factory.extra_dmg]
            # logger.info(f"and {extra_dmg} on the extra dmg dice", extra={"team": self.teams.get_team(attacker)})
            base_dmg = multiplier * dmg_dice_sum + attack.factory.dmg_bonus + attacker.ability_dmg_bonus
            if attacker.has_passive(Passive.FANATIC_ADVANTAGE) and final_modifier is RollType.ADVANTAGE and not attacker.already_used_fanatic_advantage:
                logger.info(f"{attacker} activates Fanatic Advantage", extra={"team": self.teams.get_team(attacker)})
                attacker.already_used_fanatic_advantage = True
                base_dmg += roll_dice([(2, 6)])
            logger.info(
                f"The attack {'CRITS' if multiplier == 2 else 'hits'} {target} for {base_dmg + reduce(lambda acc, extra: acc + extra[0], extra_dmg, 0)} damage", extra={"team": self.teams.get_team(attacker)})
            total_compound_dmg = [(base_dmg, attack.get_dmg_type())] + extra_dmg
            target.receive_compound_dmg(total_compound_dmg)
            target = Map.get().remove_combatant_if_dead(target)  # could be a wildshaped druid, reverting to original form
            if target and attack.factory.on_hit is not None:
                attack.factory.on_hit.hit(attacker, attack, target)

            return ActionResult.DMG
        else:
            logger.info(f"The attack misses {target}", extra={"team": self.teams.get_team(attacker)})
            return ActionResult.MISS

    def request_movement(self, moving_combatant, movement):
        battle_map = Map.get()
        if movement.incurs_aoo:
            aoo_candidates = battle_map.get_aoo_eligible_combatants(moving_combatant, movement.increment)
            if aoo_candidates:
                for candidate in aoo_candidates:
                    aoo = candidate.prompt_aoo(moving_combatant)
                    if aoo and moving_combatant.is_alive():
                        self.resolve_action(aoo, candidate)

            pam_candidates = battle_map.get_pam_eligible_combatants(moving_combatant, movement.increment)
            if pam_candidates:
                for candidate in pam_candidates:
                    pam_attack = candidate.prompt_pam(moving_combatant)
                    if pam_attack and moving_combatant.is_alive():
                        did_attack_hit = self.resolve_action(pam_attack, candidate)
                        if did_attack_hit and candidate.has_passive(Passive.SENTINEL):
                            moving_combatant.movement = 0
                            logger.info(f"Combatant {moving_combatant} was stopped by sentinel")

        if moving_combatant.is_alive():
            battle_map.move_combatant_by_increment(moving_combatant, movement.increment)
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
        logger.info(f"MY DEBUG resolve_by_actoid_flags {combatant} uses {actoid}")
        battle_map = Map.get()
        assert actoid is not None
        match actoid.factory.action_type:
            case BonusAction.TOTEM_RAGE | BonusAction.RAGE | Action.DISENGAGE | BonusAction.CUNNING_DISENGAGE | Action.DODGE | HasteAction.HASTE_DISENGAGE:
                actoid.activate()
                # self.effect_tracker.add(actoid, combatant)
                return False
            case Action.RECKLESS_ATTACK:
                if not self.effect_tracker.is_affecting_combatant(combatant, RecklessAttack):
                    # don't need to add it again in case of a multi-attack
                    actoid.activate()
                    # self.effect_tracker.add(actoid, combatant)
                    return self.resolve_attack(actoid, combatant)
            case Action.WILDSHAPE | BonusAction.MOON_WILDSHAPE:
                actoid.activate()
                # self.effect_tracker.add(actoid, combatant)
                return False
            case Action.FIREBALL | BonusAction.QUICKENED_FIREBALL:
                logger.info(f"{combatant} casts {actoid}")
                affected = battle_map.get_combatants_affected_by_aoe(combatant, actoid.factory.target, actoid.factory.type, actoid.coord)
                dmg = roll_spell_dmg(actoid.factory.dmg_dice)
                for combatant in affected:
                    resolve_dmg_saving_throw(actoid, dmg, combatant)
                    battle_map.remove_combatant_if_dead(combatant)  # could be a wildshaped druid
                return ActionResult.DMG
            case Action.HASTE | Action.TWINNED_HASTE | BonusAction.QUICKENED_HASTE | Action.FAERIE_FIRE | BonusAction.QUICKENED_FAERIE_FIRE\
                 | Action.FLAMING_SPHERE | Action.HOLD_PERSON | BonusAction.QUICKENED_HOLD_PERSON | Action.SPIKE_GROWTH | BonusAction.QUICKENED_SPIKE_GROWTH:
                logger.info(f"{combatant} casts {actoid}")
                actoid.activate()
                # self.effect_tracker.add(actoid, combatant)
                return ActionResult.NOP
            case Action.FIREBOLT | BonusAction.QUICKENED_FIREBOLT:
                logger.info(f"{combatant} casts {actoid}")
                return self.resolve_ranged_spell_attack(combatant, actoid, actoid.target)
            case Action.TWINNED_FIREBOLT:
                logger.info(f"{combatant} casts {actoid}")
                ret = (self.resolve_ranged_spell_attack(combatant, actoid, actoid.targets[0]),
                       self.resolve_ranged_spell_attack(combatant, actoid, actoid.targets[1]))
                return ActionResult.DMG if any([True if r is ActionResult.DMG else False for r in ret]) else ActionResult.MISS
            case Action.SHOCKING_GRASP | BonusAction.QUICKENED_SHOCKING_GRASP:
                logger.info(f"{combatant} casts {actoid}")
                result = self.resolve_attack(actoid, combatant)
                if result is ActionResult.DMG:
                    actoid.target.has_reaction = False
                return result
            case Action.TWINNED_SHOCKING_GRASP:
                logger.info(f"{combatant} casts {actoid}")
                result = (self.resolve_attack(actoid, combatant),
                       self.resolve_attack(actoid, combatant))
                if result[0] is ActionResult.DMG:
                    actoid.targets[0].has_reaction = False
                if result[1] is ActionResult.DMG:
                    actoid.targets[1].has_reaction = False
                return ActionResult.DMG if any([True if r is ActionResult.DMG else False for r in result]) else ActionResult.MISS
            case BonusAction.MISTY_STEP:
                logger.info(f"{combatant} casts {actoid}")
                battle_map.move_combatant(combatant, actoid.coord)
                return ActionResult.FEASIBLE
            case Action.CHAOSBOLT | BonusAction.QUICKENED_CHAOSBOLT:
                logger.info(f"{combatant} casts {actoid}")
                return self.resolve_chaos_bolt(combatant, actoid)
            case Action.SCORCHING_RAY | BonusAction.QUICKENED_SCORCHING_RAY:
                logger.info(f"{combatant} casts {actoid}")
                ret1 = self.resolve_ranged_spell_attack(combatant, actoid, actoid.targets[0])
                ret2 = self.resolve_ranged_spell_attack(combatant, actoid, actoid.targets[1]) if actoid.targets[1].is_alive() else ActionResult.NOP
                ret3 = self.resolve_ranged_spell_attack(combatant, actoid, actoid.targets[2]) if actoid.targets[2].is_alive() else ActionResult.NOP
                return ActionResult.DMG if any([True if r is ActionResult.DMG else False for r in (ret1, ret2, ret3)]) else ActionResult.MISS
            case Reaction.SHIELD:
                assert not combatant.shield_spell_active
                combatant.shield_spell_active = True
                combatant.ac += 5
                return ActionResult.FEASIBLE
            case Action.MELEE_ATTACK | Action.RANGED_ATTACK | BonusAction.BONUS_RANGED_ATTACK | BonusAction.BONUS_MELEE_ATTACK |\
                 HasteAction.HASTE_MELEE_ATTACK | HasteAction.HASTE_RANGED_ATTACK | BonusAction.PAM_BONUS_ATTACK | Reaction.REACTION_ATTACK\
                | Action.BITE_AND_SWALLOW:
                return self.resolve_attack(actoid, combatant)
            case Movement.STANDARD | Movement.DISENGAGE | Movement.CUNNING_DISENGAGE:
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
                logger.info(f"{combatant} is trying to constrict {actoid.target_combatant}")
                result = self.resolve_attack(actoid.factory.attack, combatant)
                if result is ActionResult.DMG:
                    combatant.constricted_target = True
                    return True
            case Action.BREAK_GRAPPLE:
                logger.info(f"{combatant} is trying to break out of grapple")
                grapple = actoid.factory.grapple_condition
                broken_out = roll_ability_check(max(combatant.athletics, combatant.acrobatics), grapple.dc, RollType.STRAIGHT)
                if broken_out and getattr(grapple.initiator, "constricted_target", None):  # TODO this is a simplification
                    logger.info(f"{combatant} is has broken out of grapple")
                    grapple.initiator.constricted_target = None
                    combatant.break_out_of_grapple()
                else:
                    logger.info(f"{combatant} remains grappled")
            case BonusAction.FLAMING_SPHERE_RAM:
                adj = battle_map.build_flaming_sphere_adjacency_matrix()
                _, shortest_paths = battle_map.dijkstra(actoid.factory.action_enabler_effect.origin, adj)
                path = battle_map.get_effect_path_to_coord(actoid.factory.action_enabler_effect.origin, actoid.coord, shortest_paths)
                if path and len(path) <= FlamingSphereRamFactory.RANGE + 1:
                    dmg = roll_spell_dmg(actoid.factory.dmg_dice)
                    logger.info(f"{ actoid.target_combatant} is rammed by Flaming Sphere")
                    resolve_dmg_saving_throw(actoid, dmg, actoid.target_combatant)
                    battle_map.remove_combatant_if_dead(actoid.target_combatant)   # TODO revisit if this is really needed
                path = path['tuples'][:FlamingSphereRamFactory.RANGE + 1]
                actoid.move_effect(path[-1])  # TODO consider putting this into effect tracker
                return ActionResult.DMG
            case Action.MAGIC_MISSILE | BonusAction.QUICKENED_MAGIC_MISSILE:
                dice = parse_dmg_dice(actoid.factory.dmg_dice)
                dmg_dice_sum = roll_dice(dice) + actoid.factory.dmg_bonus
                actoid.targets[0].receive_damage(dmg_dice_sum, MagicMissileFactory.dmg_type)
                if actoid.targets[1].is_alive():
                    actoid.targets[1].receive_damage(dmg_dice_sum, MagicMissileFactory.dmg_type)
                if actoid.targets[2].is_alive():
                    actoid.targets[2].receive_damage(dmg_dice_sum, MagicMissileFactory.dmg_type)
                return ActionResult.DMG
            case Action.POUNCE:
                # TODO
                return False
            case Action.WEB:
                # TODO
                return False
            case Action.PRE_SWALLOW_BITE:
                result = self.resolve_attack(actoid, combatant)  # TODO
                if result is ActionResult.DMG:
                    combatant.constricted_target = actoid.target_combatant if actoid.target_combatant.is_alive() else None
                return result
            case _:
                logger.error(f"Unknown actoid type! {actoid.factory.action_type}")

        return False

    def handle_error_case(self, action, combatant):
        if action.factory.action_type is Movement.STANDARD:
            logger.error(f"{combatant} doesn't have enough movement to enter difficult terrain")
            combatant.movement = 0  # This can be caused by difficult terrain which is ok, but we must avoid endless looping
            return None
        elif combatant.has_action:
            logger.error(f"Action {action} by {combatant} is not feasible. This should not happen!")
            df = DodgeFactory(combatant)
            return df.create()
        logger.error(f"Action {action} by {combatant} is not feasible. This should not happen!")
        return None


    def resolve_action(self, action, combatant):
        """
        The core of action resolution
        @param action_type: action type
        @param args: packed arguments of the action, can take on different interpretations based on the action_type
        @param combatant: initiator of the action
        @return: only relevant return here is DMG/MISS used for sentinel
        """
        combatant = combatant.get_current_form()  # Takes care of possible wildshape
        if action is None:
            return None
        if not check_feasibility(combatant, action):
            action = self.handle_error_case(action, combatant)
            if action is None:
                return None
        use_resources(combatant, action)
        return self.resolve_by_actoid_flags(action, combatant)


    def resolve_effects(self, effects, combatant):
        """
        Applies the aspect of effects that need to be reapplied at the beginning of a turn or would otherwise be reset by the new turn
        :param effects:
        :param combatant:
        :return:
        """
        for effect in effects:
            match effect.get_effect_type():
                case EffectType.HASTE | EffectType.TWINNED_HASTE:
                    # resolves the part of the haste spell which needs to be applied every turn
                    combatant.movement = combatant.speed * 2
                    combatant.has_haste_action = True
                case EffectType.POST_HASTE_LETHARGY:
                    combatant.movement = 0
                    combatant.has_action = False
                    combatant.has_bonus_action = False
                    combatant.has_reaction = False
                case EffectType.RAGE | EffectType.TOTEM_RAGE | EffectType.WILDSHAPE | EffectType.DODGE | EffectType.DISENGAGE |\
                     EffectType.RECKLESS_ATTACK | EffectType.FLAMING_SPHERE | EffectType.SPIKE_GROWTH | EffectType.CLOUD_OF_DAGGERS |\
                    EffectType.HUNGER_OF_HADAR:
                    pass  # TODO track if the barbarian attacked or received dmg
                case _:
                    logger.error("Unknown effect")


def check_concentration(combatant, dmg):
    """
    Calculates a concentration check for a combatant after receiving damage. It assumes the damage has already been taken.
    @param combatant: The combatant object representing the character.
    @param dmg: The amount of damage taken by the combatant.
    @return: True if concentration maintained, False otherwise
    """
    combatant = combatant.get_original_form().get_current_form()  # The dmg received could have knocked combatant out of wildshape
    if not combatant.concentration_effect:
        return False
    if not combatant.is_alive():
        logger.info(f"Concentration on {combatant.concentration_effect} is broken as {combatant} is dead")
        Map.get().effect_tracker.remove(combatant.concentration_effect)  # This will in turn call the deactivate which removes sets the concentration_effect to None
        return False
    dc = max(10, math.floor(dmg / 2))
    roll_type = RollType.STRAIGHT if not (combatant.has_passive(Passive.WAR_CASTER) or combatant.has_passive(Passive.ELDRITCH_MIND)) else RollType.ADVANTAGE
    saved = roll_saving_throw(combatant.saving_throws[SavingThrow.CON], dc, roll_type)
    if not saved:
        logger.info(f"{combatant} loses concentration on {combatant.concentration_effect}")
        Map.get().effect_tracker.remove(combatant.concentration_effect)  # This will in turn call the deactivate which removes sets the concentration_effect to None
    else:
        logger.info(f"{combatant} maintains concentration on {combatant.concentration_effect}")
    return saved
