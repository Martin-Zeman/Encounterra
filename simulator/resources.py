from simulator.action_factory import *
import logging

logger = logging.getLogger(__name__)


def use_resources(combatant, action):
    action_type = action.action_type
    if isinstance(action_type, Action):
        combatant.has_action = False
        match action_type:
            case Action.ATTACK:
                combatant.curr_num_attacks -= 1
            case Action.DODGE | Action.DASH | Action.FIREBOLT:
                pass  # sufficiently tracked by not having an action anymore
            case Action.FIREBALL:
                combatant.spellslots.use_spellslot(3)
                combatant.already_cast_leveled_spell_this_turn = True
            case Action.HASTE:
                combatant.spellslots.use_spellslot(3)
                combatant.already_cast_leveled_spell_this_turn = True
                combatant.is_concentrating = True
            case Action.TWINNED_HASTE:
                combatant.spellslots.use_spellslot(3)
                combatant.already_cast_leveled_spell_this_turn = True
                combatant.is_concentrating = True
                combatant.curr_sorcery_points -= 3
            case Action.CHAOSBOLT:
                combatant.spellslots.use_spellslot(1)
                combatant.already_cast_leveled_spell_this_turn = True
            case Action.TWINNED_CHAOSBOLT:
                combatant.spellslots.use_spellslot(1)
                combatant.already_cast_leveled_spell_this_turn = True
                combatant.curr_sorcery_points -= 1
            case Action.TWINNED_FIREBOLT:
                combatant.curr_sorcery_points -= 1
            case _:
                logger.error("Unknown action type")
    elif isinstance(action_type, BonusAction):
        combatant.has_bonus_action = False
        match action_type:
            case BonusAction.BONUS_ATTACK | BonusAction.PAM_BONUS_ATTACK:
                pass  # sufficiently tracked by not having a bonus action anymore
            case BonusAction.RAGE | BonusAction.TOTEM_RAGE:
                combatant.curr_rage_uses -= 1
            case BonusAction.MISTY_STEP:
                combatant.spellslots.use_spellslot(2)
                combatant.already_cast_leveled_spell_this_turn = True
            case BonusAction.QUICKENED_CHAOSBOLT:
                combatant.spellslots.use_spellslot(1)
                combatant.already_cast_leveled_spell_this_turn = True
                combatant.curr_sorcery_points -= 2
            case BonusAction.QUICKENED_HASTE:
                combatant.spellslots.use_spellslot(3)
                combatant.already_cast_leveled_spell_this_turn = True
                combatant.is_concentrating = True
                combatant.curr_sorcery_points -= 2
            case BonusAction.QUICKENED_FIREBALL:
                combatant.spellslots.use_spellslot(3)
                combatant.already_cast_leveled_spell_this_turn = True
                combatant.curr_sorcery_points -= 2
            case BonusAction.QUICKENED_FIREBOLT:
                combatant.curr_sorcery_points -= 2
            case _:
                logger.error("Unknown bonus action type")
    elif isinstance(action_type, Reaction):
        combatant.has_reaction = False
        match action_type:
            case Reaction.REACTION_ATTACK:
                pass  # sufficiently tracked by not having a reaction anymore
            case Reaction.SHIELD:
                combatant.spellslots.use_spellslot(1)
            case _:
                logger.error("Unknown reaction type")
    elif isinstance(action_type, Movement):
        combatant.movement -= 1
    elif isinstance(action_type, HasteAction):
        combatant.has_haste_action = False
    elif isinstance(action_type, FreeAction):
        pass  # no resources needed
    else:
        logger.error("Unknown high level action class")


def reset_resources(combatant):
    """
    First resets those resources that are common for all combatants which are reset by the Combatant parent class. Then it resets all the
    dynamically added resources
    :param combatant:
    :return: void
    """
    combatant.reset()
    # Currently no dynamic resources for actions
    # for action in combatant.actions:
    #     pass

    for bonus_action in combatant.bonus_actions:
        match bonus_action:
            case BonusAction.RAGE | BonusAction.TOTEM_RAGE:
                combatant.curr_rage_uses = combatant.max_rage_uses
                combatant.rage_active = False
            case _:
                pass

    if hasattr(combatant, "curr_sorcery_points"):
        combatant.curr_sorcery_points = combatant.max_sorcery_points


