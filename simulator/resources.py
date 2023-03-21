from simulator.action_factory import *
import logging
from simulator.misc import Conditions

logger = logging.getLogger(__name__)




def use_resources(combatant, action, battle_map):
    try:
        action_type = action.factory.action_type
    except AttributeError:
        # This is here because during construction of FSMs we pass the action_type directly instead of the action instance
        action_type = action
    if isinstance(action_type, Action):
        combatant.has_action = False
        match action_type:
            case Action.MELEE_ATTACK | Action.RANGED_ATTACK | Action.RECKLESS_ATTACK:
                combatant.curr_num_attacks -= 1
                combatant.ammo[action.factory.name] -= 1
                combatant.attack_mapping[action.factory][1](combatant.action_fsm)  # trigger event on the FSM, done this way to avoid multiprocessing pickling error
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
            case Action.TWINNED_FIREBOLT:
                combatant.curr_sorcery_points -= 1
            case _:
                logger.error("Unknown action type")
    elif isinstance(action_type, BonusAction):
        combatant.has_bonus_action = False
        match action_type:
            case BonusAction.BONUS_MELEE_ATTACK | BonusAction.BONUS_RANGED_ATTACK | BonusAction.PAM_BONUS_ATTACK:
                combatant.ammo[action.factory.name] -= 1
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
            case BonusAction.CUNNING_DISENGAGE:
                pass  # sufficiently tracked by not having a bonus action anymore
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
        match action_type:
            case Movement.STANDARD:
                target_position = battle_map.get_combatant_position(combatant) + action.increment
                decrement = 1
                if combatant.is_affected_by(Conditions.PRONE):
                    decrement += 1
                if battle_map.is_difficult_terrain_at(target_position):
                    decrement += 1
                combatant.movement -= decrement
            case Movement.GET_UP_FROM_PRONE:
                combatant.movement -= combatant.speed / 2
            case _:
                logger.error("Unknown movement type")
    elif isinstance(action_type, HasteAction):
        combatant.has_haste_action = False
    # elif isinstance(action_type, FreeAction):
    #     pass  # no resources needed
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

    for bonus_action in combatant.bonus_action_factories:
        match bonus_action[0]:
            case BonusAction.RAGE | BonusAction.TOTEM_RAGE:
                combatant.curr_rage_uses = combatant.max_rage_uses
            case _:
                pass

    if hasattr(combatant, "curr_sorcery_points"):
        combatant.curr_sorcery_points = combatant.max_sorcery_points


