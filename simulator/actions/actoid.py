from enum import auto, Flag, Enum


class ActoidFlags(Flag):
    DEFAULT = auto()
    IS_ATTACK_LIKE = auto()
    IS_ATTACK_MODIFIER = auto()
    IS_MOVEMENT = auto()
    IS_SPELL = auto()
    IS_DASH = auto()
    IS_HIDE = auto()
    IS_GET_UP_FROM_PRONE = auto()
    IS_BREAK_GRAPPLE = auto()
    IS_ACTION_ENABLER = auto()


class Actoid:
    """
    Proto-action base class. It doesn't map onto an 'action' directly as an Actoid can represent even a partial action such as one attack
    which is part of a multiattack or a movement increment.
    """
    def __init__(self, actoid_flags=ActoidFlags.DEFAULT):
        self.actoid_flags = actoid_flags


class FactoryFlags(Flag):
    DEFAULT = auto()
    IS_ATTACK_LIKE = auto()
    IS_HASTE_ELIGIBLE_ATTACK = auto()
    IS_MELEE = auto()
    USES_DEX = auto()  # We're not calling it FINESSE because of Ray of Enfeeblement and the fact that ranged attacks can also use STR
    IS_RANGED = auto()
    IS_DIRECT_THREAT = auto()
    IS_ATTACK_MODIFIER = auto()
    IS_RECHARGE = auto()
    DEX_SAVE_APPLIES = auto()
    HAS_AMMO = auto()
    TARGETS_COORDS = auto()
    TARGETS_SELF = auto()
    PREVENT_ENDLESS_RECURSION = auto()  # This is a very technical one which helps prevent endless recursion
    TRANSITIONS_TO_WILDSHAPE = auto()
    TWO_HANDED = auto()
    IS_PRECISION = auto()
