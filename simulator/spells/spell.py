from enum import Enum, auto


class SpellStats:

    class Target(Enum):
        SELF = auto()
        ONE_CREATURE = auto()
        TWO_CREATURES = auto()
        THREE_CREATURES = auto()
        RADIUS_10 = auto()
        RADIUS_20 = auto()
        RADIUS_30 = auto()
        BOX_5 = auto()
        BOX_15 = auto()
        BOX_20 = auto()
        CONE_15 = auto()
        CONE_30 = auto()
        CONE_60 = auto()
        CONE_90 = auto()

    TRANSLATE_RADIUS = {Target.RADIUS_10: 2, Target.RADIUS_20: 4, Target.RADIUS_30: 6}
    TRANSLATE_CONE = {Target.CONE_15: 3, Target.CONE_30: 6, Target.CONE_60: 12, Target.CONE_90: 18}
    TRANSLATE_BOX = {Target.BOX_5: 1, Target.BOX_15: 3, Target.BOX_20: 4}

    class Range(Enum):
        """
        The range values translate directly into hops of 5ft
        """
        SELF = -1
        SIGHT = 0
        TOUCH = 1
        FEET_10 = 2
        FEET_30 = 6
        FEET_60 = 12
        FEET_90 = 18
        FEET_100 = 20
        FEET_120 = 24
        FEET_150 = 30
        FEET_300 = 60

    class Duration(Enum):
        UNLIMITED = -1  # for spell longer than 10 minutes
        INSTANTANEOUS = 0  # for spell longer than 10 minutes
        ROUND_ONE = 1
        MINUTE = 10  # in rounds
        TEN_MINUTES = 100  # in rounds

    class Type(Enum):
        HARMFUL = 1
        BUFF = 2
        OTHER = 3
