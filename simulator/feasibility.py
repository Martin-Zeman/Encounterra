from simulator.abilities.rage import Rage
from simulator.abilities.reckless_attack import RecklessAttack
from simulator.abilities.totem_rage import TotemRage
from simulator.actions.action_types import Action, BonusAction, HasteAction, Movement, Reaction
from simulator.battle_map import Map
from simulator.combatant_coords import CombatantCoords
from simulator.misc import Conditions, Size
import logging
import numpy as np

logger = logging.getLogger("EncounTroll")


def check_feasibility(combatant, action):
    battle_map = Map.get()
    action_type = action.factory.action_type
    if isinstance(action_type, Action) or isinstance(action_type, HasteAction):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED, Conditions.STUNNED, Conditions.PARALYZED):
            return False
        if isinstance(action_type, Action):
            res = combatant.has_action
        else:
            res = combatant.has_haste_action
            if not res:
                return False
        match action_type:
            case Action.FIREBALL:
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.are_valid_coords(action.coord)
                res &= battle_map.get_cartesian_distance(combatant, np.array([action.coord])) <= action.factory.range
                return res
            case Action.HASTE:
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= action.target.is_alive() and battle_map.get_cartesian_distance(combatant, action.target) <= action.factory.range
                res &= battle_map.teams.are_allies(combatant, action.target)
                return res
            case Action.CHAOSBOLT:
                res &= combatant.spellslots.get_spellslots(1) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.factory.range
                return res
            case Action.SCORCHING_RAY:
                res &= combatant.spellslots.get_spellslots(2) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= battle_map.teams.are_enemies(combatant, action.targets[1])
                res &= battle_map.teams.are_enemies(combatant, action.targets[2])
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.factory.range
                res &= action.targets[1].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[1]) <= action.factory.range
                res &= action.targets[2].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[2]) <= action.factory.range
                return res
            case Action.FIREBOLT:
                res &= battle_map.teams.are_enemies(combatant, action.target)
                res &= action.target.is_alive() and battle_map.get_cartesian_distance(combatant, action.target) <= action.factory.range
                return res
            case Action.TWINNED_FIREBOLT:
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.targets[1])
                res &= action.targets[1].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[1]) <= action.factory.range
                res &= combatant.curr_sorcery_points > 0
                return res
            case Action.TWINNED_HASTE:
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.factory.range
                res &= action.targets[1].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[1]) <= action.factory.range
                res &= battle_map.teams.are_allies(combatant, action.targets[0])
                res &= battle_map.teams.are_allies(combatant, action.targets[0])
                res &= combatant.curr_sorcery_points > 2
                return res
            case Action.MELEE_ATTACK | HasteAction.HASTE_MELEE_ATTACK:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, RecklessAttack)
                res &= combatant.ammo[action.factory.name] > 0
                res &= action.target_combatant.is_alive() and battle_map.get_hop_distance(combatant, action.target_combatant) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target_combatant)
                return res
            case Action.RANGED_ATTACK | HasteAction.HASTE_RANGED_ATTACK:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, RecklessAttack)
                res &= combatant.ammo[action.factory.name] > 0
                res &= action.target_combatant.is_alive() and battle_map.get_cartesian_distance(combatant, action.target_combatant) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target_combatant)
                return res
            case Action.RECKLESS_ATTACK:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= combatant.ammo[action.factory.name] > 0
                res &= action.target_combatant.is_alive() and battle_map.get_hop_distance(combatant, action.target_combatant) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target_combatant)
                return res
            case Action.DASH | Action.DISENGAGE | HasteAction.HASTE_DISENGAGE | HasteAction.HASTE_DASH:
                # Technically, those actions are possible but make no sense
                return res and not combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.RESTRAINED)
            case Action.DODGE | Action.POUNCE:
                return res
            case Action.BREAK_GRAPPLE:
                return res and combatant.is_affected_by_any(Conditions.GRAPPLED)
            case Action.CONSTRICT:
                return res and (action.target_combatant is combatant.constricted_target) if combatant.constricted_target else True
            case Action.WILDSHAPE:
                return res and combatant.curr_wildshape_uses > 0
            case Action.PRE_SWALLOW_BITE:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, RecklessAttack)
                res &= combatant.ammo[action.factory.name] > 0
                res &= action.target_combatant.is_alive() and battle_map.get_hop_distance(combatant, action.target_combatant) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target_combatant)
                res &= (action.target_combatant is combatant.constricted_target) if combatant.constricted_target else True
                return res
            case Action.BITE_AND_SWALLOW:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, RecklessAttack)
                res &= combatant.ammo[action.factory.name] > 0
                res &= action.target_combatant.is_alive() and battle_map.get_hop_distance(combatant, action.target_combatant) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target_combatant)
                res &= not combatant.swallowed_target
                res &= action.target_combatant is combatant.constricted_target
                return res
            case Action.FLAMING_SPHERE:
                res &= combatant.spellslots.get_spellslots(2) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.is_concentrating
                res &= battle_map.are_valid_coords(np.array([action.origin]))
                res &= battle_map.get_cartesian_distance(combatant, np.array([action.origin])) <= action.factory.range
                return res
            case HasteAction.HASTE_BITE_AND_SWALLOW:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, RecklessAttack)
                res &= combatant.ammo[action.factory.name] > 0
                res &= action.target_combatant.is_alive() and battle_map.get_hop_distance(combatant, action.target_combatant) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target_combatant)
                res &= not combatant.swallowed_target
                res &= action.target_combatant is combatant.constricted_target
                return res
            case HasteAction.HASTE_PRE_SWALLOW_BITE:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, RecklessAttack)
                res &= combatant.ammo[action.factory.name] > 0
                res &= action.target_combatant.is_alive() and battle_map.get_hop_distance(combatant, action.target_combatant) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target_combatant)
                res &= (action.target_combatant is combatant.constricted_target) if combatant.constricted_target else True
                return res
            case _:
                logger.error("check_feasibility: Unknown action type")
                return False
    elif isinstance(action_type, BonusAction):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED, Conditions.STUNNED, Conditions.PARALYZED):
            return False
        res = combatant.has_bonus_action
        match action_type:
            case BonusAction.PAM_BONUS_ATTACK:
                res &= action.target_combatant.is_alive() and battle_map.get_hop_distance(combatant, action.target_combatant) <= action.range
                res &= battle_map.teams.are_enemies(combatant, action.target_combatant)
                return res
            case BonusAction.RAGE:
                return res and combatant.curr_rage_uses and not battle_map.effect_tracker.is_affecting_combatant(combatant, Rage)
            case BonusAction.TOTEM_RAGE:
                return res and combatant.curr_rage_uses and not battle_map.effect_tracker.is_affecting_combatant(combatant, TotemRage)
            case BonusAction.MISTY_STEP:
                res &= combatant.spellslots.get_spellslots(2) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.get_cartesian_distance(combatant, np.array([action.coord])) <= action.factory.range
                res &= battle_map.are_valid_coords(action.coord) and battle_map.are_empty_or_self(CombatantCoords(action.coord, combatant), combatant)
                return res
            case BonusAction.QUICKENED_CHAOSBOLT:
                res &= combatant.spellslots.get_spellslots(1) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.factory.range
                res &= combatant.curr_sorcery_points > 1
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                return res
            case BonusAction.QUICKENED_SCORCHING_RAY:
                res &= combatant.spellslots.get_spellslots(2) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.factory.range
                res &= action.targets[1].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[1]) <= action.factory.range
                res &= action.targets[2].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[2]) <= action.factory.range
                res &= combatant.curr_sorcery_points > 1
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= battle_map.teams.are_enemies(combatant, action.targets[1])
                res &= battle_map.teams.are_enemies(combatant, action.targets[2])
                return res
            case BonusAction.QUICKENED_HASTE:
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.get_cartesian_distance(combatant, action.target) <= action.factory.range
                res &= combatant.curr_sorcery_points > 1
                res &= battle_map.teams.are_allies(combatant, action.target)
                return res
            case BonusAction.QUICKENED_FIREBALL:
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.get_cartesian_distance(combatant, np.array([action.coord])) <= action.factory.range
                res &= combatant.curr_sorcery_points > 1
                res &= battle_map.are_valid_coords(action.coord)
                return res
            case BonusAction.QUICKENED_FIREBOLT:
                res &= action.target.is_alive() and battle_map.get_cartesian_distance(combatant, action.target) <= action.factory.range
                res &= combatant.curr_sorcery_points > 1
                res &= battle_map.teams.are_enemies(combatant, action.target)
                return res
                # TODO check sorcery points, checks if the spell even has casting time of an action, check if leveled spell has already been cast
            case BonusAction.CUNNING_DISENGAGE:
                return res
            case BonusAction.MOON_WILDSHAPE:
                return res and combatant.curr_wildshape_uses > 0
            case BonusAction.FLAMING_SPHERE_RAM:
                return res  # TODO add more conditions
            case _:
                logger.error("Unknown bonus action")
                return False
    elif isinstance(action_type, Reaction):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED, Conditions.STUNNED, Conditions.PARALYZED):
            return False
        match action_type:
            case Reaction.SHIELD:
                return combatant.has_reaction and combatant.spellslots.get_spellslots(1) > 0
            case Reaction.REACTION_ATTACK:
                return combatant.has_reaction
            case Reaction.PRE_SWALLOW_BITE_REACTION:
                return combatant.has_reaction and not combatant.constricted_target
            case _:
                logger.error("Unknown reaction")
        return combatant.has_reaction
    elif isinstance(action_type, Movement):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED, Conditions.STUNNED, Conditions.PARALYZED):
            return False
        match action_type:
            case Movement.STANDARD | Movement.DISENGAGE | Movement.CUNNING_DISENGAGE:
                target_position = battle_map.get_combatant_position(combatant) + action.increment
                movement_needed = 1 if not battle_map.is_difficult_terrain_at(target_position) else 2
                res = combatant.movement >= movement_needed and battle_map.are_valid_coords(target_position.get()) and battle_map.are_empty_or_self(target_position, combatant)
                res &= not combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.RESTRAINED)
                return res
            case Movement.GET_UP_FROM_PRONE:
                return combatant.movement >= (combatant.speed / 2)
            case _:
                logger.error("Unknown movement")
    # elif isinstance(action_type, FreeAction):
    #     match action_type:
    #         case _:
    #             logger.error("Unknown free action")
    #             return False
    else:
        logger.error("check_feasibility: Unknown action type")
        return False


def check_feasibility_light(combatant, action):
    """
    Checks feasibility in terms of resources and combat rules. Doesn't check arguments of actions.
    :param combatant: initiator of the action
    :param action: action to be considered in form of a tuple (action_type, action_factory)
    :return: True if feasible, false otherwise
    """
    battle_map = Map.get()
    action_type = action[0]
    if isinstance(action_type, Action) or isinstance(action_type, HasteAction):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED, Conditions.STUNNED, Conditions.PARALYZED):
            return False
        if isinstance(action_type, Action):
            res = combatant.has_action
        else:
            res = combatant.has_haste_action
            if not res:
                return False
        match action_type:
            case Action.FIREBALL:
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                return res
            case Action.HASTE:
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.is_concentrating
                # res &= (len(battle_map.teams.get_allies(combatant)) > 0)
                return res
            case Action.CHAOSBOLT:
                res &= combatant.spellslots.get_spellslots(1) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                return res
            case Action.SCORCHING_RAY:
                res &= combatant.spellslots.get_spellslots(2) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                return res
            case Action.FIREBOLT:
                return res
            case Action.TWINNED_FIREBOLT:
                return res and combatant.curr_sorcery_points > 0
            case Action.TWINNED_HASTE:
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.is_concentrating
                res &= combatant.curr_sorcery_points > 2
                res &= (len(battle_map.teams.get_allies(combatant)) > 0)
                return res
            case Action.MELEE_ATTACK | Action.RANGED_ATTACK | HasteAction.HASTE_MELEE_ATTACK | HasteAction.HASTE_RANGED_ATTACK:
                res |= not combatant.attack_fsm.is_0() and str(action[1]) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, RecklessAttack)
                res &= combatant.ammo[action[1].name] > 0
                return res
            case Action.RECKLESS_ATTACK:
                res |= not combatant.attack_fsm.is_0() and str(action[1]) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= combatant.ammo[action[1].name] > 0
                return res
            case Action.DASH | Action.DISENGAGE | HasteAction.HASTE_DASH | HasteAction.HASTE_DISENGAGE:
                return res and not combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.RESTRAINED)
            case Action.DODGE | Action.POUNCE:
                return res
            case Action.CONSTRICT:
                return res  # and not combatant.is_constricting
            case Action.WILDSHAPE:
                return res and combatant.curr_wildshape_uses > 0
            case Action.PRE_SWALLOW_BITE:
                res |= not combatant.attack_fsm.is_0() and str(action[1]) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, RecklessAttack)
                res &= combatant.ammo[action[1].name] > 0
                return res
            case Action.BITE_AND_SWALLOW:
                res |= not combatant.attack_fsm.is_0() and str(action[1]) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, RecklessAttack)
                res &= combatant.ammo[action[1].name] > 0
                res &= not combatant.swallowed_target
                res &= combatant.constricted_target is not None and combatant.constricted_target.size.value <= Size.MEDIUM.value
                return res
            case Action.FLAMING_SPHERE:
                res &= combatant.spellslots.get_spellslots(2) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.is_concentrating
                return res
            case HasteAction.HASTE_BITE_AND_SWALLOW:
                res |= not combatant.attack_fsm.is_0() and str(action[1]) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, RecklessAttack)
                res &= combatant.ammo[action[1].name] > 0
                res &= not combatant.swallowed_target
                res &= combatant.constricted_target is not None and combatant.constricted_target.size.value <= Size.MEDIUM.value
                return res
            case HasteAction.HASTE_PRE_SWALLOW_BITE:
                res |= not combatant.attack_fsm.is_0() and str(action[1]) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, RecklessAttack)
                res &= combatant.ammo[action[1].name] > 0
                return res
            case _:
                logger.error("check_feasibility_light: Unknown action type")
                return False
    elif isinstance(action_type, BonusAction):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED, Conditions.STUNNED, Conditions.PARALYZED):
            return False
        res = combatant.has_bonus_action
        match action_type:
            case BonusAction.PAM_BONUS_ATTACK:  # TODO Remove this
                return res
            case BonusAction.RAGE:
                return res and combatant.curr_rage_uses and not battle_map.effect_tracker.is_affecting_combatant(combatant, Rage)
            case BonusAction.TOTEM_RAGE:
                return res and combatant.curr_rage_uses and not battle_map.effect_tracker.is_affecting_combatant(combatant, TotemRage)
            case BonusAction.MISTY_STEP:
                res &= combatant.spellslots.get_spellslots(2) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                return res
            case BonusAction.QUICKENED_CHAOSBOLT:
                res &= combatant.spellslots.get_spellslots(1) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= combatant.curr_sorcery_points > 1
                return res
            case BonusAction.QUICKENED_SCORCHING_RAY:
                res &= combatant.spellslots.get_spellslots(2) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= combatant.curr_sorcery_points > 1
                return res
            case BonusAction.QUICKENED_HASTE:
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.is_concentrating
                res &= combatant.curr_sorcery_points > 1
                return res
            case BonusAction.QUICKENED_FIREBALL:
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= combatant.curr_sorcery_points > 1
                return res
            case BonusAction.QUICKENED_FIREBOLT:
                return res and combatant.curr_sorcery_points > 1
                # TODO check sorcery points, checks if the spell even has casting time of an action, check if leveled spell has already been cast
            case BonusAction.CUNNING_DISENGAGE | BonusAction.FLAMING_SPHERE_RAM:
                return res
            case BonusAction.MOON_WILDSHAPE:
                return res and combatant.curr_wildshape_uses > 0
            case _:
                logger.error("Unknown bonus action")
                return False
    elif isinstance(action_type, Reaction):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED):
            return False
        match action_type:
            case Reaction.SHIELD:
                return combatant.has_reaction and combatant.spellslots.get_spellslots(1) > 0
            case _:
                logger.error("Unknown reaction")
        return combatant.has_reaction
    elif isinstance(action_type, Movement):
        return combatant.movement > 0 and not combatant.is_affected_by_any(
            Conditions.GRAPPLED,
            Conditions.RESTRAINED)
    else:
        logger.error("check_feasibility_light: Unknown action type")
        return False


def get_feasible_factories(actions, combatant):
    return [a for a in actions if check_feasibility_light(combatant, a)]
