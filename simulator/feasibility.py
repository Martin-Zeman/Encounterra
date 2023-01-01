from simulator.action_factory import *
import logging

logger = logging.getLogger(__name__)


def check_feasibility(combatant, action_type):
    if isinstance(action_type, Action):
        match action_type:
            case Action.FIREBALL | Action.HASTE:
                return combatant.spellslots.has_spellslots(3) and not combatant.already_cast_leveled_spell_this_turn
        if combatant.has_action:
            return True
        elif action_type is Action.ATTACK and combatant.curr_num_attacks:
            return True
    elif isinstance(action_type, BonusAction):
        match action_type:
            case BonusAction.PAM_BONUS_ATTACK:
                return combatant.has_bonus_action and combatant.curr_num_attacks < combatant.num_attacks  # if already took the attack action
            case BonusAction.RAGE | BonusAction.TOTEM_RAGE:
                return combatant.has_bonus_action and combatant.curr_rage_uses and not combatant.rage_active
            case BonusAction.MISTY_STEP:
                return combatant.spellslots.has_spellslots(2) and not combatant.already_cast_leveled_spell_this_turn
        return combatant.has_bonus_action
    elif isinstance(action_type, Reaction):
        return combatant.has_reaction
    elif isinstance(action_type, Movement):
        return combatant.movement > 0
    elif isinstance(action_type, HasteAction):
        return combatant.has_haste_action
    elif isinstance(action_type, FreeAction):
        match action_type:
            case FreeAction.RECKLESS_ATTACK:
                return combatant.curr_num_attacks == combatant.num_attacks and not combatant.reckless_attack_active # not attacked yet
            case _:
                logger.error("Unknown free action")
                return False
    else:
        logger.error("Unknown action type")
        return False
