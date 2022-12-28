from simulator.attack import Attack
from simulator.dodge import Dodge
from simulator.spells.fireball import Fireball
from simulator.spells.firebolt import Firebolt
from simulator.spells.shield import Shield
from simulator.spells.misty_step import MistyStep
from simulator.abilities.rage import Rage
from simulator.abilities.totem_rage import TotemRage
from simulator.movement import MovementIncrement
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)


class Action(Enum):
    ATTACK = auto()
    DODGE = auto()
    DASH = auto()
    FIREBALL = auto()
    FIREBOLT = auto()


class BonusAction(Enum):
    BONUS_ATTACK = auto()
    PAM_BONUS_ATTACK = auto()
    RAGE = auto()
    TOTEM_RAGE = auto()
    MISTY_STEP = auto()
    CUNNING_DODGE = auto()


class Reaction(Enum):
    REACTION_ATTACK = auto()
    SHIELD = auto()


class Movement(Enum):
    STANDARD = auto()
    DISENGAGE = auto()
    CUNNING_DISENGAGE = auto()
    FORCED = auto()


class Passive(Enum):
    MULTIATTACK = auto()
    SENTINEL = auto()
    POLEARM_MASTER = auto()
    DANGER_SENSE = auto


def action_factory(combatant, action_type, *args):
    if isinstance(action_type, Action):
        match action_type:
            case Action.ATTACK:
                return Attack(*args)
            case Action.DODGE:
                return Dodge(combatant)
            case Action.DASH:
                return None
            case Action.FIREBALL:
                return Fireball(*args)
            case Action.FIREBOLT:
                return Firebolt(combatant.spell_to_hit, combatant.level, *args)
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
    else:
        logger.error("Unknown high level action class")
        return None
