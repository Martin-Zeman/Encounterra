from enum import Enum, auto


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
    TWINNED_CHAOSBOLT = auto()
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
    QUICKENED_SPELL = auto()
    TWINNED_SPELL = auto()
    EMPOWERED_SPELL = auto()