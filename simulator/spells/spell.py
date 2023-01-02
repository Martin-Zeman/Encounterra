from enum import Enum
from simulator.actoid import Actoid


class Spell(Actoid):

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
        CONE_60 = 9
        CONE_90 = 10

    TRANSLATE_RADIUS = {Target.RADIUS_10: 2, Target.RADIUS_20: 4, Target.RADIUS_30: 6}
    TRANSLATE_CONE = {Target.CONE_15: 3, Target.CONE_30: 6, Target.CONE_60: 12, Target.CONE_90: 18}

    class Range(Enum):
        SELF = -1
        TOUCH = 0
        SIGHT = 1
        FEET_10 = 2
        FEET_30 = 6
        FEET_60 = 12
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



    def __init__(self, level, spell_range, target, duration, concentration, type, to_hit=None, dc=None, dmg_type=None, orientation=None):
        Actoid.__init__(self, type=Actoid.Type.IS_SPELL)
        self.level = level
        self.range = spell_range
        self.target = target
        self.duration = duration
        self.concentration = concentration
        self.type = type
        self.to_hit = to_hit
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
