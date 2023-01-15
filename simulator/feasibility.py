from simulator.action_factory import *
from simulator.misc import Conditions
import logging
import numpy as np

logger = logging.getLogger(__name__)


def check_feasibility(combatant, action, battle_map):
    action_type = action.action_type
    if isinstance(action_type, Action):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED):
            return False
        match action_type:
            case Action.FIREBALL:
                res = combatant.has_action
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.is_valid_coord(action.coord)
                res &= battle_map.get_cartesian_distance(combatant, action.coord) <= action.range.value
                return res
            case Action.HASTE:
                res = combatant.has_action
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                res &= battle_map.teams.are_allies(combatant, action.targets[0])
                return res
            case Action.CHAOSBOLT:
                res = combatant.has_action
                res &= combatant.spellslots.get_spellslots(1) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                return res
            case Action.FIREBOLT:
                res = combatant.has_action
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                return res
            case Action.TWINNED_CHAOSBOLT:
                res = combatant.has_action
                res &= combatant.spellslots.get_spellslots(1) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                res &= battle_map.teams.are_enemies(combatant, action.targets[1])
                res &= action.targets[1].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[1]) <= action.range.value
                res &= combatant.curr_sorcery_points > 0
                return res
            case Action.TWINNED_FIREBOLT:
                res = combatant.has_action
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= action.targets[1].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[1]) <= action.range.value
                res &= combatant.curr_sorcery_points > 0
                return res
            case Action.TWINNED_HASTE:
                res = combatant.has_action
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                res &= action.targets[1].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[1]) <= action.range.value
                res &= battle_map.teams.are_allies(combatant, action.targets[0])
                res &= battle_map.teams.are_allies(combatant, action.targets[0])
                res &= combatant.curr_sorcery_points > 2
                return res
            case Action.ATTACK:
                res = combatant.curr_num_attacks > 0
                res &= action.target_combatant.is_alive() and battle_map.get_hop_distance(combatant, action.target_combatant) <= action.range
                res &= battle_map.teams.are_enemies(combatant, action.target_combatant)
                return res
            case Action.DASH | Action.DODGE:
                return combatant.has_action and not combatant.is_affected_by_any(Conditions.GRAPPLED,
                                                                                 Conditions.RESTRAINED,
                                                                                 Conditions.STUNNED,
                                                                                 Conditions.PARALYZED)
            case _:
                logger.error("Unknown action type")
                return False
    elif isinstance(action_type, BonusAction):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED):
            return False
        res = combatant.has_bonus_action
        match action_type:
            case BonusAction.PAM_BONUS_ATTACK:
                res &= combatant.curr_num_attacks < combatant.num_attacks  # if already took the attack action
                res &= action.target_combatant.is_alive() and battle_map.get_hop_distance(combatant, action.target_combatant) <= action.range
                res &= battle_map.teams.are_enemies(combatant, action.target_combatant)
                return res
            case BonusAction.RAGE | BonusAction.TOTEM_RAGE:
                return res and combatant.curr_rage_uses and not combatant.rage_active
            case BonusAction.MISTY_STEP:
                res &= combatant.spellslots.get_spellslots(2) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.get_cartesian_distance(combatant, action.coord) <= action.range.value
                res &= battle_map.is_valid_coord(action.coord) and battle_map.is_empty(action.coord)
                return res
            case BonusAction.QUICKENED_CHAOSBOLT:
                res &= combatant.spellslots.get_spellslots(1) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                res &= combatant.curr_sorcery_points > 1
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                return res
            case BonusAction.QUICKENED_HASTE:
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                res &= combatant.curr_sorcery_points > 1
                res &= battle_map.teams.are_allies(combatant, action.targets[0])
                return res
            case BonusAction.QUICKENED_FIREBALL:
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.get_cartesian_distance(combatant, action.coord) <= action.range.value
                res &= combatant.curr_sorcery_points > 1
                res &= battle_map.is_valid_coord(action.coord)
                return res
            case BonusAction.QUICKENED_FIREBOLT:
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                res &= combatant.curr_sorcery_points > 1
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                return res
                # TODO check sorcery points, checks if the spell even has casting time of an action, check if leveled spell has already been cast
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
        return combatant.movement > 0 and np.max(np.abs(action.increment)) < 2 and not np.array_equal(action.increment, np.array([0, 0])) and battle_map.is_empty(
            battle_map.get_combatant_position(combatant) + action.increment) and not combatant.is_affected_by_any(
            Conditions.GRAPPLED,
            Conditions.RESTRAINED)
    elif isinstance(action_type, HasteAction):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED):
            return False
        return combatant.has_haste_action
    elif isinstance(action_type, FreeAction):
        match action_type:
            case FreeAction.RECKLESS_ATTACK:
                return combatant.curr_num_attacks == combatant.num_attacks and not combatant.reckless_attack_active  # not attacked yet
            case _:
                logger.error("Unknown free action")
                return False
    else:
        logger.error("Unknown action type")
        return False


def check_feasibility_light(combatant, action, battle_map):
    action_type = action.action_type
    if isinstance(action_type, Action):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED):
            return False
        match action_type:
            case Action.FIREBALL | Action.HASTE:
                res = combatant.has_action
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                return res
            case Action.CHAOSBOLT:
                res = combatant.has_action
                res &= combatant.spellslots.get_spellslots(1) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                return res
            case Action.FIREBOLT:
                return combatant.has_action
            case Action.TWINNED_CHAOSBOLT:
                res = combatant.has_action
                res &= combatant.spellslots.get_spellslots(1) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= combatant.curr_sorcery_points > 0
                return res
            case Action.TWINNED_FIREBOLT:
                return combatant.has_action and combatant.curr_sorcery_points > 0
            case Action.TWINNED_HASTE:
                res = combatant.has_action
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= combatant.curr_sorcery_points > 2
                return res
            case Action.ATTACK:
                return combatant.curr_num_attacks > 0
            case Action.DASH | Action.DODGE:
                return combatant.has_action and not combatant.is_affected_by_any(Conditions.GRAPPLED,
                                                                                 Conditions.RESTRAINED,
                                                                                 Conditions.STUNNED,
                                                                                 Conditions.PARALYZED)
            case _:
                logger.error("Unknown action type")
                return False
    elif isinstance(action_type, BonusAction):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED):
            return False
        res = combatant.has_bonus_action
        match action_type:
            case BonusAction.PAM_BONUS_ATTACK:
                return res and combatant.curr_num_attacks < combatant.num_attacks  # if already took the attack action
            case BonusAction.RAGE | BonusAction.TOTEM_RAGE:
                return res and combatant.curr_rage_uses and not combatant.rage_active
            case BonusAction.MISTY_STEP:
                res &= combatant.spellslots.get_spellslots(2) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                return res
            case BonusAction.QUICKENED_CHAOSBOLT:
                res &= combatant.spellslots.get_spellslots(1) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= combatant.curr_sorcery_points > 1
                return res
            case BonusAction.QUICKENED_HASTE | BonusAction.QUICKENED_FIREBALL:
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= combatant.curr_sorcery_points > 1
                return res
            case BonusAction.QUICKENED_FIREBOLT:
                return res and combatant.curr_sorcery_points > 1
                # TODO check sorcery points, checks if the spell even has casting time of an action, check if leveled spell has already been cast
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
    elif isinstance(action_type, HasteAction):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED):
            return False
        return combatant.has_haste_action
    elif isinstance(action_type, FreeAction):
        match action_type:
            case FreeAction.RECKLESS_ATTACK:
                return combatant.curr_num_attacks == combatant.num_attacks and not combatant.reckless_attack_active  # not attacked yet
            case _:
                logger.error("Unknown free action")
                return False
    else:
        logger.error("Unknown action type")
        return False


def get_feasible_actions(actions, combatant, battle_map):
    return [a for a in actions if check_feasibility_light(combatant, a, battle_map)]
