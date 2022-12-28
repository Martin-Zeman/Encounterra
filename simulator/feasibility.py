from simulator.action_factory import *
import logging

logger = logging.getLogger(__name__)


def check_feasibility(combatant, action_type):
    if isinstance(action_type, Action):
        if combatant.has_action:
            return True
        elif action_type is Action.ATTACK and combatant.curr_num_attacks:
            return True
    elif isinstance(action_type, BonusAction):
        if action_type is BonusAction.PAM_BONUS_ATTACK:
            return combatant.curr_num_attacks < combatant.num_attacks  # if already took the attack action
        return combatant.has_bonus_action
    elif isinstance(action_type, Reaction):
        return combatant.has_reaction
    elif isinstance(action_type, Movement):
        return combatant.movement > 0
    else:
        logger.error("Unknown action type")
        return False
