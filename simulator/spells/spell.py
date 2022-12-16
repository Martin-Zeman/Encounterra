from enum import Enum
from simulator.actoid import Actoid


class Spell(Actoid):

    class CastingTime(Enum):
        ACTION = 1
        BONUS_ACTION = 2
        REACTION = 3
        ONE_MINUTE = 4

    class Target(Enum):
        SELF = 0
        ONE_CREATURE = 1
        THREE_CREATURES = 2
        RADIUS_10 = 3
        RADIUS_20 = 4
        RADIUS_30 = 5
        BOX = 6
        CONE_15 = 7
        CONE_30 = 8

    TRANSLATE_RADIUS = {Target.RADIUS_10: 2, Target.RADIUS_20: 4, Target.RADIUS_30: 6}

    class Range(Enum):
        SELF = 0
        TOUCH = 1
        SIGHT = 2
        FEET_10 = 10
        FEET_30 = 30
        FEET_60 = 60
        FEET_100 = 100
        FEET_120 = 120
        FEET_150 = 150
        FEET_300 = 300

    class Duration(Enum):
        UNLIMITED = -1  # for spell longer than 10 minutes
        INSTANTANEOUS = 0  # for spell longer than 10 minutes
        ROUND_ONE = 1
        MINUTE = 10  # in rounds
        TEN_MINUTES = 100  # in rounds


    class Type(Enum):
        HARMFUL = 1
        BUFF = 2



    def __init__(self, level, casting_time, range, target, duration, concentration, type, dc=None, dmg_type=None, orientation=None):
        Actoid.__init__(actoid_type=Actoid.IS_SPELL)
        self.level = level
        self.casting_time = casting_time
        self.range = range
        self.target = target
        self.duration = duration
        self.concentration = concentration
        self.type = type
        self.dc = dc
        self.dmg_type = dmg_type
        self.orientation = orientation  # like orientation of a cone
        self.additional_upcast_targets = None
        self.additional_upcast_dmg = None
        self.saving_throw = False
        self.coord = None
        self.dmg = None


    def is_cantrip(self):
        return self.level == 0
