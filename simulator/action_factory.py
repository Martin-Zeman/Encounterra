from simulator.attack import Attack
from simulator.dodge import Dodge
from simulator.spells.fireball import Fireball
from simulator.spells.firebolt import Firebolt
from simulator.spells.shield import Shield
from simulator.spells.misty_step import MistyStep
from simulator.spells.haste import Haste
from simulator.abilities.rage import Rage
from simulator.abilities.totem_rage import TotemRage
from simulator.movement import MovementIncrement
from simulator.actions import *
import logging

logger = logging.getLogger(__name__)


def action_factory(combatant, effect_tracker, action_type, *args):
    if isinstance(action_type, Action):
        match action_type:
            case Action.ATTACK:
                return Attack(*args)
            case Action.DODGE:
                try:
                    dodge = Dodge(combatant)
                except TypeError:
                    logger.error("FIXME Dodge Action factory")
                return dodge
            case Action.DASH:
                combatant.movement += combatant.speed
                return None
            case Action.FIREBALL:
                return Fireball(*args)
            case Action.FIREBOLT:
                return Firebolt(combatant.spell_to_hit, combatant.level, *args)
            case Action.HASTE:
                return Haste(*args, combatant, effect_tracker)
            case _:
                logger.error("Unknown action type")
                return None
    elif isinstance(action_type, BonusAction):
        match action_type:
            case BonusAction.BONUS_ATTACK | BonusAction.PAM_BONUS_ATTACK:
                return Attack(*args)
            case BonusAction.TOTEM_RAGE:
                return TotemRage(combatant)
            case BonusAction.RAGE:
                return Rage(combatant)
            case BonusAction.MISTY_STEP:
                return MistyStep(*args)
            case _:
                logger.error("Unknown bonus action type")
                return None
    elif isinstance(action_type, Reaction):
        match action_type:
            case Reaction.REACTION_ATTACK:
                return Attack(*args)
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
                return Attack(*args)
            case HasteAction.HASTE_DASH:
                combatant.movement += combatant.speed
                return None
            case _:
                logger.error("Unknown haste action")
    else:
        logger.error("Unknown high level action class")
        return None
