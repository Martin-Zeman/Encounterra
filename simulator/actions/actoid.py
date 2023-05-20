from enum import auto, Flag, Enum

class ActoidFlags(Flag):
    IS_ATTACK_LIKE = auto()
    IS_DIRECT_THREAT = auto()
    IS_ATTACK_MODIFIER = auto()
    IS_MOVEMENT = auto()
    IS_SPELL = auto()
    IS_DASH = auto()
    IS_TOGGLE_ABILITY = auto()
    IS_GET_UP_FROM_PRONE = auto()
    IS_POSITIONING_INDEPENDENT = auto()

class Actoid:
    """
    Proto-action base class. It doesn't map onto an 'action' directly as an Actoid can represent even a partial action such as one attack
    which is part of a multiattack or a movement increment.
    """
    def __init__(self, actoid_flags):
        self.actoid_flags = actoid_flags

class FactoryFlags(Flag):
    # TODO Consider merging actoid flags and factory flags
    DEFAULT = auto()
    IS_ATTACK_LIKE = auto()
    IS_HASTE_ELIGIBLE_ATTACK = auto()
    IS_MELEE = auto()
    IS_RANGED = auto()
    IS_DIRECT_THREAT = auto()
    IS_ATTACK_MODIFIER = auto()
    DEX_SAVE_APPLIES = auto()
    HAS_AMMO = auto()
    TARGETS_COORDS = auto()
    TARGETS_SELF = auto()
    USES_CALCULATE_THREAT_IN_MOD = auto()  # This is a very technical one which helps prevent endless recursion
