from enum import Enum, auto


class Action(Enum):
    MELEE_ATTACK = auto()
    RANGED_ATTACK = auto()
    RECKLESS_ATTACK = auto()
    BITE_WITH_SWALLOW = auto()
    DODGE = auto()
    DASH = auto()
    DISENGAGE = auto()
    FIREBALL = auto()
    FIREBOLT = auto()
    CHAOSBOLT = auto()
    HASTE = auto()
    HUNGER_OF_HADAR = auto()
    SPIKE_GROWTH = auto()
    CLOUD_OF_DAGGERS = auto()
    HIDE = auto()
    TWINNED_FIREBOLT = auto()
    TWINNED_HASTE = auto()
    SCORCHING_RAY = auto()
    FAERIE_FIRE = auto()
    WILDSHAPE = auto()
    POUNCE = auto()
    CONSTRICT = auto()
    BREAK_GRAPPLE = auto()


class BonusAction(Enum):
    BONUS_MELEE_ATTACK = auto()
    BONUS_RANGED_ATTACK = auto()
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
    QUICKENED_HUNGER_OF_HADAR = auto()
    QUICKENED_SPIKE_GROWTH = auto()
    QUICKENED_CLOUD_OF_DAGGERS = auto()
    QUICKENED_SCORCHING_RAY = auto()
    QUICKENED_FAERIE_FIRE = auto()
    MOON_WILDSHAPE = auto()
    WEB = auto()


class Reaction(Enum):
    REACTION_ATTACK = auto()
    SHIELD = auto()
    BITE_WITH_SWALLOW_REACTION = auto()


class Movement(Enum):
    STANDARD = auto()
    DISENGAGE = auto()
    CUNNING_DISENGAGE = auto()
    FORCED = auto()
    GET_UP_FROM_PRONE = auto()


class HasteAction(Enum):
    HASTE_MELEE_ATTACK = auto()
    HASTE_RANGED_ATTACK = auto()
    HASTE_DASH = auto()
    HASTE_DISENGAGE = auto()
    HASTE_HIDE = auto()
    HASTE_BITE_WITH_SWALLOW = auto()


class Passive(Enum):
    SENTINEL = auto()
    POLEARM_MASTER = auto()
    DANGER_SENSE = auto()
    METAMAGIC = auto()
    PACK_TACTICS = auto()
    FANATIC_ADVANTAGE = auto()


class MetaAction(Enum):
    DONE = auto()
    QUICKENED_SPELL = auto()
    TWINNED_SPELL = auto()
    EMPOWERED_SPELL = auto()