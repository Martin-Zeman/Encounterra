from simulator.action_factory import *
from simulator.misc import Conditions
import logging

logger = logging.getLogger(__name__)


def check_feasibility(combatant, action, battle_map):
    if combatant.is_affected_by_any(Conditions.STUNNED, Conditions.PARALYZED, Conditions.PETRIFIED, Conditions.UNCONSCIOUS):
        return False
    action_type = action.action_type
    if isinstance(action_type, Action):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED):
            return False
        match action_type:
            case Action.FIREBALL | Action.HASTE:
                return combatant.has_action and combatant.spellslots.has_spellslots(
                    3) and not combatant.already_cast_leveled_spell_this_turn and battle_map.get_hop_distance(combatant,
                                                                                                              action.coord) <= action.range.value
            case Action.CHAOSBOLT:
                return combatant.has_action and combatant.spellslots.has_spellslots(
                    1) and not combatant.already_cast_leveled_spell_this_turn and battle_map.get_hop_distance(combatant, action.targets[
                        0]) <= action.range.value
            case Action.DASH:
                return combatant.has_action and not combatant.is_affected_by_any(Conditions.GRAPPLED,
                                                                              Conditions.RESTRAINED, Conditions.STUNNED, Conditions.PARALYZED)
        if combatant.has_action:
            return True
        elif action_type is Action.ATTACK:
            return combatant.curr_num_attacks and battle_map.get_hop_distance(combatant, action.target_combatant) <= action.range
    elif isinstance(action_type, BonusAction):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED):
            return False
        match action_type:
            case BonusAction.PAM_BONUS_ATTACK:
                # if already took the attack action
                return combatant.has_bonus_action and combatant.curr_num_attacks < combatant.num_attacks and battle_map.get_hop_distance(
                    combatant, action.target_combatant) <= action.range
            case BonusAction.RAGE | BonusAction.TOTEM_RAGE:
                return combatant.has_bonus_action and combatant.curr_rage_uses and not combatant.rage_active
            case BonusAction.MISTY_STEP:
                return combatant.spellslots.has_spellslots(
                    2) and not combatant.already_cast_leveled_spell_this_turn and battle_map.get_hop_distance(combatant,
                                                                                                              action.coord) <= action.range.value
        return combatant.has_bonus_action
    elif isinstance(action_type, Reaction):
        if combatant.is_affected_by_any(Conditions.INCAPACITATED):
            return False
        return combatant.has_reaction
    elif isinstance(action_type, Movement):
        return combatant.movement > 0 and battle_map.is_empty(battle_map.get_combatant_position(combatant) + action.increment) and not combatant.is_affected_by_any(Conditions.GRAPPLED,
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
