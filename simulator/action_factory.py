import numpy as np

from simulator.attack import Attack
from simulator.dodge import Dodge
from simulator.dash import Dash
from simulator.spells.fireball import Fireball
from simulator.spells.firebolt import Firebolt
from simulator.spells.chaosbolt import Chaosbolt
from simulator.spells.shield import Shield
from simulator.spells.misty_step import MistyStep
from simulator.spells.haste import Haste
from simulator.abilities.rage import Rage
from simulator.abilities.totem_rage import TotemRage
from simulator.abilities.reckless_attack import RecklessAttack
from simulator.movement import MovementIncrement
from simulator.actions import *
import logging

logger = logging.getLogger(__name__)


def action_factory(combatant, effect_tracker, action_type, *args):
    if isinstance(action_type, Action):
        match action_type:
            case Action.ATTACK:
                return Attack(action_type, *args)
            case Action.DODGE:
                return Dodge(combatant)
            case Action.DASH:
                return Dash()
            case Action.FIREBALL:
                return Fireball(action_type, *args, combatant.dc)
            case Action.FIREBOLT:
                return Firebolt(action_type, combatant.spell_to_hit, combatant.level, *args)
            case Action.CHAOSBOLT:
                return Chaosbolt(action_type, combatant.spell_to_hit, *args)
            case Action.HASTE:
                return Haste(action_type, *args, combatant, effect_tracker)
            case Action.TWINNED_FIREBOLT:
                logger.debug("Twinned Firebolt")
                return Firebolt(action_type, combatant.spell_to_hit, combatant.level, *args)
            case Action.TWINNED_CHAOSBOLT:
                logger.debug("Twinned Chaosbolt")
                return Chaosbolt(action_type, combatant.spell_to_hit, *args)
            case Action.TWINNED_HASTE:
                return Haste(action_type, *args, combatant, effect_tracker)
            case _:
                logger.error("Unknown action type")
                return None
    elif isinstance(action_type, BonusAction):
        match action_type:
            case BonusAction.BONUS_ATTACK | BonusAction.PAM_BONUS_ATTACK:
                return Attack(action_type, *args)
            case BonusAction.TOTEM_RAGE:
                return TotemRage(combatant)
            case BonusAction.RAGE:
                return Rage(combatant)
            case BonusAction.MISTY_STEP:
                return MistyStep(*args)
            case BonusAction.QUICKENED_CHAOSBOLT:
                logger.debug("Quickened Chaosbolt")
                return Chaosbolt(action_type, combatant.spell_to_hit, *args)
            case BonusAction.QUICKENED_FIREBALL:
                logger.debug("Quickened Fireball")
                return Fireball(action_type, *args, combatant.dc)
            case BonusAction.QUICKENED_FIREBOLT:
                logger.debug("Quickened Firebolt")
                return Firebolt(action_type, combatant.spell_to_hit, combatant.level, *args)
            case BonusAction.QUICKENED_HASTE:
                return Haste(action_type, *args, combatant, effect_tracker)
            case _:
                logger.error("Unknown bonus action type")
                return None
    elif isinstance(action_type, Reaction):
        match action_type:
            case Reaction.REACTION_ATTACK:
                return Attack(action_type, *args)
            case Reaction.SHIELD:
                return Shield()
            case _:
                logger.error("Unknown reaction type")
                return None
    elif isinstance(action_type, Movement):
        match action_type:
            case Movement.STANDARD:
                return MovementIncrement(*args, True)
            case _:
                logger.error("Unknown movement type")
                return None
    elif isinstance(action_type, HasteAction):
        match action_type:
            case HasteAction.HASTE_ATTACK:
                return Attack(action_type, *args)
            case HasteAction.HASTE_DASH:
                return Dash()
            case _:
                logger.error("Unknown haste action")
    elif isinstance(action_type, FreeAction):
        match action_type:
            case FreeAction.RECKLESS_ATTACK:
                return RecklessAttack(combatant)
            case _:
                logger.error("Unknown free action")
    else:
        logger.error("Unknown high level action class")
        return None
