from enum import Enum, auto, Flag


class Actoid:
    # TODO get rid of this class
    class Type(Enum):
        IS_ATTACK_LIKE_ACTION = auto()
        IS_MOVEMENT = auto()
        IS_SPELL = auto()
        IS_DASH = auto()
        IS_TOGGLE_ABILITY = auto()

    def __init__(self, actoid_type, is_direct_dmg_dealing=False):
        self.actoid_type = actoid_type
        self.action_type = None
        self.is_direct_dmg_dealing = is_direct_dmg_dealing

class FactoryFlags(Flag):
    DEFAULT = auto()
    IS_ATTACK_LIKE = auto()
    IS_DIRECT_THREAT = auto()

