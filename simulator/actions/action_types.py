from enum import Enum, auto


class Action(Enum):
    NOP = auto()
    MELEE_ATTACK = auto()
    RANGED_ATTACK = auto()
    RECKLESS_ATTACK = auto()
    PRE_SWALLOW_BITE = auto()
    BITE_AND_SWALLOW = auto()
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
    FLAMING_SPHERE = auto()
    WEB = auto()
    HOLD_PERSON = auto()
    TWINNED_HOLD_PERSON = auto()
    SHOCKING_GRASP = auto()
    TWINNED_SHOCKING_GRASP = auto()
    MAGIC_MISSILE = auto()
    GRAPPLE = auto()
    GRAPPLE_ATTACK = auto()
    VAMPIRIC_BITE = auto()
    BLESS = auto()
    RAY_OF_ENFEEBLEMENT = auto()
    TWINNED_RAY_OF_ENFEEBLEMENT = auto()
    SLEEP = auto()
    SHAKE_ALLY_AWAKE = auto()
    THUNDERWAVE = auto()


class BonusAction(Enum):
    NOP = auto()
    BONUS_MELEE_ATTACK = auto()
    BONUS_RANGED_ATTACK = auto()
    PAM_BONUS_ATTACK = auto()
    RAGE = auto()
    TOTEM_RAGE = auto()
    MISTY_STEP = auto()
    CUNNING_DISENGAGE = auto()
    CUNNING_DASH = auto()
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
    QUICKENED_BLESS = auto()
    QUICKENED_FLAMING_SPHERE = auto()
    QUICKENED_HOLD_PERSON = auto()
    FLAMING_SPHERE_RAM = auto()
    MOON_WILDSHAPE = auto()
    QUICKENED_SHOCKING_GRASP = auto()
    QUICKENED_MAGIC_MISSILE = auto()
    QUICKENED_RAY_OF_ENFEEBLEMENT = auto()
    QUICKENED_SLEEP = auto()
    SECOND_WIND = auto()
    HEALING_WORD = auto()
    SHILLELAGH = auto()


class Reaction(Enum):
    REACTION_ATTACK = auto()
    SHIELD = auto()
    PRE_SWALLOW_BITE_REACTION = auto()
    UNCANNY_DODGE = auto()
    PARRY = auto()


class Movement(Enum):
    STANDARD = auto()
    DISENGAGED = auto()
    FORCED = auto()
    GET_UP_FROM_PRONE = auto()
    DASH = auto()


class MovementThreatType(Enum):
    STANDARD = auto()
    DISENGAGED = auto()
    DODGED = auto()
    MISTY_STEPPED = auto()


class HasteAction(Enum):
    HASTE_MELEE_ATTACK = auto()
    HASTE_RANGED_ATTACK = auto()
    HASTE_DASH = auto()
    HASTE_DISENGAGE = auto()
    HASTE_HIDE = auto()
    HASTE_PRE_SWALLOW_BITE = auto()
    HASTE_BITE_AND_SWALLOW = auto()
    HASTE_GRAPPLE_ATTACK = auto()
    HASTE_GRAPPLE = auto()
    HASTE_VAMPIRIC_BITE = auto()


class Passive(Enum):
    SPELLCASTING = auto()
    SENTINEL = auto()
    POLEARM_MASTER = auto()
    DANGER_SENSE = auto()
    METAMAGIC = auto()
    PACK_TACTICS = auto()
    FANATIC_ADVANTAGE = auto()
    WAR_CASTER = auto()
    ELDRITCH_MIND = auto()
    SNEAK_ATTACK = auto()
    CUNNING_ACTION = auto()
    ASSASSINATE = auto()
    REGENERATION = auto()
    EVASION = auto()
    HEART_OF_HRUGGEK = auto()
    DARK_DEVOTION = auto()
    BLINDSIGHT = auto()
    MAGIC_RESISTANCE = auto()
    CHARM_IMMUNITY = auto()
    GREAT_WEAPON_FIGHTING = auto()


class MetaAction(Enum):
    QUICKENED_SPELL = auto()
    TWINNED_SPELL = auto()
    EMPOWERED_SPELL = auto()


# TODO
class FreeAction(Enum):
    ACTION_SURGE = auto()
