from enum import Enum, auto
from simulator.actions.attack import AttackFactory
from simulator.actions.dodge import DodgeFactory
from simulator.spells.haste import HasteFactory
from simulator.spells.bless import BlessFactory
from simulator.spells.shield import ShieldFactory
from simulator.spells.fireball import FireballFactory
from simulator.spells.misty_step import MistyStepFactory
from simulator.spells.firebolt import FireboltFactory
from simulator.spells.twinned_firebolt import TwinnedFireboltFactory
from simulator.spells.twinned_haste import TwinnedHasteFactory
from simulator.spells.chaosbolt import ChaosboltFactory
from simulator.abilities.totem_rage import TotemRageFactory
from simulator.abilities.rage import RageFactory


class Action(Enum):
    ATTACK = auto()
    DODGE = auto()
    DASH = auto()
    DISENGAGE = auto()
    FIREBALL = auto()
    FIREBOLT = auto()
    CHAOSBOLT = auto()
    HASTE = auto()
    HIDE = auto()
    TWINNED_FIREBOLT = auto()
    TWINNED_HASTE = auto()

class BonusAction(Enum):
    BONUS_ATTACK = auto()
    PAM_BONUS_ATTACK = auto()
    RAGE = auto()
    TOTEM_RAGE = auto()
    MISTY_STEP = auto()
    CUNNING_DODGE = auto()
    CUNNING_DISENGAGE = auto()
    CUNNING_HIDE = auto()
    QUICKENED_FIREBALL = auto()
    QUICKENED_FIREBOLT = auto()
    QUICKENED_CHAOSBOLT = auto()
    QUICKENED_HASTE = auto()


class Reaction(Enum):
    REACTION_ATTACK = auto()
    SHIELD = auto()


class Movement(Enum):
    STANDARD = auto()
    DISENGAGE = auto()
    CUNNING_DISENGAGE = auto()
    FORCED = auto()


class FreeAction(Enum):
    RECKLESS_ATTACK = auto()


class HasteAction(Enum):
    HASTE_ATTACK = auto()
    HASTE_DASH = auto()
    HASTE_DISENGAGE = auto()
    HASTE_HIDE = auto()


class Passive(Enum):
    MULTIATTACK = auto()
    SENTINEL = auto()
    POLEARM_MASTER = auto()
    DANGER_SENSE = auto()
    METAMAGIC = auto()

class MetaAction(Enum):
    DONE = auto()
    QUICKENED_SPELL = auto()
    TWINNED_SPELL = auto()
    EMPOWERED_SPELL = auto()

TO_FACTORY = {
    Action.ATTACK: AttackFactory,
    Action.DODGE: DodgeFactory,
    Action.DASH: None,
    Action.DISENGAGE: None,
    Action.FIREBALL: FireballFactory,
    Action.FIREBOLT: FireboltFactory,
    Action.CHAOSBOLT: ChaosboltFactory,
    Action.HASTE: HasteFactory,
    Action.HIDE: None,
    Action.TWINNED_FIREBOLT: TwinnedFireboltFactory,
    Action.TWINNED_HASTE: TwinnedHasteFactory,

    BonusAction.BONUS_ATTACK: AttackFactory,
    BonusAction.PAM_BONUS_ATTACK: AttackFactory,
    BonusAction.RAGE: RageFactory,
    BonusAction.TOTEM_RAGE: TotemRageFactory,
    BonusAction.MISTY_STEP: MistyStepFactory,
    BonusAction.CUNNING_DODGE: DodgeFactory,
    BonusAction.CUNNING_DISENGAGE: None,
    BonusAction.CUNNING_HIDE: None,
    BonusAction.QUICKENED_FIREBALL: FireballFactory,
    BonusAction.QUICKENED_FIREBOLT: FireboltFactory,
    BonusAction.QUICKENED_CHAOSBOLT: ChaosboltFactory,
    BonusAction.QUICKENED_HASTE: HasteFactory,
}
TO_QUICKENED = { Action.FIREBALL: BonusAction.QUICKENED_FIREBALL, Action.FIREBOLT: BonusAction.QUICKENED_FIREBOLT, Action.CHAOSBOLT: BonusAction.QUICKENED_CHAOSBOLT, Action.HASTE: BonusAction.QUICKENED_HASTE}
TO_TWINNED = {Action.FIREBOLT: Action.TWINNED_FIREBOLT, Action.HASTE: Action.TWINNED_HASTE}