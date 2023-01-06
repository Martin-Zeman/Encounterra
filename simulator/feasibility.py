from simulator.action_factory import *
from simulator.misc import Conditions
import logging

logger = logging.getLogger(__name__)


def check_feasibility(combatant, action, battle_map):
    if combatant.is_affected_by_any(Conditions.STUNNED, Conditions.PARALYZED, Conditions.PETRIFIED,
                                    Conditions.UNCONSCIOUS):
        return False
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
                res &= battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                res &= action.targets[0].is_alive()
                res &= battle_map.teams.are_allies(combatant, action.targets[0])
                return res
            case Action.CHAOSBOLT:
                res = combatant.has_action
                res &= combatant.spellslots.get_spellslots(1) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                res &= action.targets[0].is_alive()
                return res
            case Action.TWINNED_CHAOSBOLT:
                res = combatant.has_action
                res &= combatant.spellslots.get_spellslots(1) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                res &= battle_map.teams.are_enemies(combatant, action.targets[1])
                res &= battle_map.get_cartesian_distance(combatant, action.targets[1]) <= action.range.value
                res &= combatant.curr_sorcery_points > 0
                res &= action.targets[0].is_alive()
                res &= action.targets[1].is_alive()
                return res
            case Action.TWINNED_FIREBOLT:
                res = combatant.has_action
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= battle_map.get_cartesian_distance(combatant, action.targets[1]) <= action.range.value
                res &= combatant.curr_sorcery_points > 0
                res &= action.targets[0].is_alive()
                res &= action.targets[1].is_alive()
                return res
            case Action.TWINNED_HASTE:
                res = combatant.has_action
                res &= combatant.spellslots.get_spellslots(3) > 0
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                res &= battle_map.get_cartesian_distance(combatant, action.targets[1]) <= action.range.value
                res &= battle_map.teams.are_allies(combatant, action.targets[0])
                res &= action.targets[0].is_alive()
                res &= battle_map.teams.are_allies(combatant, action.targets[0])
                res &= action.targets[1].is_alive()
                res &= combatant.curr_sorcery_points > 2
                return res
            case Action.DASH:
                return combatant.has_action and not combatant.is_affected_by_any(Conditions.GRAPPLED,
                                                                                 Conditions.RESTRAINED,
                                                                                 Conditions.STUNNED,
                                                                                 Conditions.PARALYZED)
        if combatant.has_action:
            return True
        elif action_type is Action.ATTACK:
            return combatant.curr_num_attacks and battle_map.get_hop_distance(combatant,
                                                                              action.target_combatant) <= action.range and battle_map.teams.are_enemies(
                combatant, action.target_combatant)
    elif isinstance(action_type, BonusAction):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED):
            return False
        match action_type:
            case BonusAction.PAM_BONUS_ATTACK:
                res = combatant.has_bonus_action
                res &= combatant.curr_num_attacks < combatant.num_attacks  # if already took the attack action
                res &= battle_map.get_hop_distance(combatant, action.target_combatant) <= action.range
                res &= battle_map.teams.are_enemies(combatant, action.target_combatant)
                return res
            case BonusAction.RAGE | BonusAction.TOTEM_RAGE:
                return combatant.has_bonus_action and combatant.curr_rage_uses and not combatant.rage_active
            case BonusAction.MISTY_STEP:
                res = combatant.has_bonus_action
                res &= combatant.spellslots.get_spellslots(2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.get_cartesian_distance(combatant, action.coord) <= action.range.value
                res &= battle_map.is_valid_coord(action.coord)
                return res
            case BonusAction.QUICKENED_CHAOSBOLT:
                res = combatant.has_bonus_action
                res &= combatant.spellslots.get_spellslots(1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                res &= combatant.curr_sorcery_points > 1
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                return res
            case BonusAction.QUICKENED_HASTE:
                res = combatant.has_bonus_action
                res &= combatant.spellslots.get_spellslots(3)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                res &= combatant.curr_sorcery_points > 1
                res &= battle_map.teams.are_allies(combatant, action.targets[0])
                return res
            case BonusAction.QUICKENED_FIREBALL:
                res = combatant.has_bonus_action
                res &= combatant.spellslots.get_spellslots(3)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.get_cartesian_distance(combatant, action.coord) <= action.range.value
                res &= combatant.curr_sorcery_points > 1
                res &= battle_map.is_valid_coord(action.coord)
                return res
            case BonusAction.QUICKENED_FIREBOLT:
                res = combatant.has_bonus_action
                res &= battle_map.get_cartesian_distance(combatant, action.targets[0]) <= action.range.value
                res &= combatant.curr_sorcery_points > 1
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                return res
                # TODO check sorcery points, checks if the spell even has casting time of an action, check if leveled spell has already been cast
        return combatant.has_bonus_action
    elif isinstance(action_type, Reaction):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED):
            return False
        return combatant.has_reaction
    elif isinstance(action_type, Movement):
        return combatant.movement > 0 and battle_map.is_empty(
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
