import logging
import copy
from enum import Enum, auto

from .misc import Class
from .resources import Resource, ResourceRefreshType

logger = logging.getLogger("Encounterra")


class SpellcastingType(Enum):
    FULL_CASTER = auto()
    HALF_CASTER = auto()
    QUARTER_CASTER = auto()


FULL_CASTER_TABLE = {
    1: {
        1: 2,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    2: {
        1: 3,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    3: {
        1: 4,
        2: 2,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    4: {
        1: 4,
        2: 3,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    5: {
        1: 4,
        2: 3,
        3: 2,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    6: {
        1: 4,
        2: 3,
        3: 3,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    7: {
        1: 4,
        2: 3,
        3: 3,
        4: 1,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    8: {
        1: 4,
        2: 3,
        3: 3,
        4: 2,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    9: {
        1: 4,
        2: 3,
        3: 3,
        4: 3,
        5: 1,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    10: {
        1: 4,
        2: 3,
        3: 3,
        4: 3,
        5: 2,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    11: {
        1: 4,
        2: 3,
        3: 3,
        4: 3,
        5: 2,
        6: 1,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    12: {
        1: 4,
        2: 3,
        3: 3,
        4: 3,
        5: 2,
        6: 1,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    13: {
        1: 4,
        2: 3,
        3: 3,
        4: 3,
        5: 2,
        6: 1,
        7: 1,
        8: 0,
        9: 0,
        None: 0
    },
    14: {
        1: 4,
        2: 3,
        3: 3,
        4: 3,
        5: 2,
        6: 1,
        7: 1,
        8: 0,
        9: 0,
        None: 0
    },
    15: {
        1: 4,
        2: 3,
        3: 3,
        4: 3,
        5: 2,
        6: 1,
        7: 1,
        8: 1,
        9: 0,
        None: 0
    },
    16: {
        1: 4,
        2: 3,
        3: 3,
        4: 3,
        5: 2,
        6: 1,
        7: 1,
        8: 1,
        9: 0,
        None: 0
    },
    17: {
        1: 4,
        2: 3,
        3: 3,
        4: 3,
        5: 2,
        6: 1,
        7: 1,
        8: 1,
        9: 1,
        None: 0
    },
    18: {
        1: 4,
        2: 3,
        3: 3,
        4: 3,
        5: 3,
        6: 1,
        7: 1,
        8: 1,
        9: 1,
        None: 0
    },
    19: {
        1: 4,
        2: 3,
        3: 3,
        4: 3,
        5: 3,
        6: 2,
        7: 1,
        8: 1,
        9: 1,
        None: 0
    },
    20: {
        1: 4,
        2: 3,
        3: 3,
        4: 3,
        5: 3,
        6: 2,
        7: 2,
        8: 1,
        9: 1,
        None: 0
    }
}

HALF_CASTER_TABLE = {
    1: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    2: {
        1: 2,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    3: {
        1: 3,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    4: {
        1: 3,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    5: {
        1: 4,
        2: 2,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    6: {
        1: 4,
        2: 2,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    7: {
        1: 4,
        2: 3,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    8: {
        1: 4,
        2: 3,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    9: {
        1: 4,
        2: 3,
        3: 2,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    10: {
        1: 4,
        2: 3,
        3: 2,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    11: {
        1: 4,
        2: 3,
        3: 3,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    12: {
        1: 4,
        2: 3,
        3: 3,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    13: {
        1: 4,
        2: 3,
        3: 3,
        4: 1,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    14: {
        1: 4,
        2: 3,
        3: 3,
        4: 1,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    15: {
        1: 4,
        2: 3,
        3: 3,
        4: 2,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    16: {
        1: 4,
        2: 3,
        3: 3,
        4: 2,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    17: {
        1: 4,
        2: 3,
        3: 3,
        4: 3,
        5: 1,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    18: {
        1: 4,
        2: 3,
        3: 3,
        4: 3,
        5: 1,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    19: {
        1: 4,
        2: 3,
        3: 3,
        4: 3,
        5: 2,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    20: {
        1: 4,
        2: 3,
        3: 3,
        4: 3,
        5: 2,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    }
}

QUARTER_CASTER_TABLE = {
    1: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    2: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    3: {
        1: 2,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    4: {
        1: 3,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    5: {
        1: 3,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    6: {
        1: 3,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    7: {
        1: 4,
        2: 2,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    8: {
        1: 4,
        2: 2,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    9: {
        1: 4,
        2: 2,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    10: {
        1: 4,
        2: 3,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    11: {
        1: 4,
        2: 3,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    12: {
        1: 4,
        2: 3,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    13: {
        1: 4,
        2: 3,
        3: 2,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    14: {
        1: 4,
        2: 3,
        3: 2,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    15: {
        1: 4,
        2: 3,
        3: 2,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    16: {
        1: 4,
        2: 3,
        3: 3,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    17: {
        1: 4,
        2: 3,
        3: 3,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    18: {
        1: 4,
        2: 3,
        3: 3,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    19: {
        1: 4,
        2: 3,
        3: 3,
        4: 1,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    20: {
        1: 4,
        2: 3,
        3: 3,
        4: 1,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    }
}

WARLOCK_TABLE = {
    1: {
        1: 1,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    2: {
        1: 2,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    3: {
        1: 0,
        2: 2,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    4: {
        1: 0,
        2: 2,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    5: {
        1: 0,
        2: 0,
        3: 2,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    6: {
        1: 0,
        2: 0,
        3: 2,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    7: {
        1: 0,
        2: 0,
        3: 0,
        4: 2,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    8: {
        1: 0,
        2: 0,
        3: 0,
        4: 2,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    9: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 2,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    10: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 2,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    11: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 3,
        6: 1,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    12: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 3,
        6: 1,
        7: 0,
        8: 0,
        9: 0,
        None: 0
    },
    13: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 3,
        6: 1,
        7: 1,
        8: 0,
        9: 0,
        None: 0
    },
    14: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 3,
        6: 1,
        7: 1,
        8: 0,
        9: 0,
        None: 0
    },
    15: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 3,
        6: 1,
        7: 1,
        8: 1,
        9: 0,
        None: 0
    },
    16: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 3,
        6: 1,
        7: 1,
        8: 1,
        9: 0,
        None: 0
    },
    17: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 4,
        6: 1,
        7: 1,
        8: 1,
        9: 1,
        None: 0
    },
    18: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 4,
        6: 1,
        7: 1,
        8: 1,
        9: 1,
        None: 0
    },
    19: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 4,
        6: 1,
        7: 1,
        8: 1,
        9: 1,
        None: 0
    },
    20: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 4,
        6: 1,
        7: 1,
        8: 1,
        9: 1,
        None: 0
    }
}


def spellslot_factory(class_name, class_level):
    match class_name:
        case Class.BARD():
            return Spellslots(FULL_CASTER_TABLE[class_level])
        case Class.CLERIC():
            return Spellslots(FULL_CASTER_TABLE[class_level])
        case Class.DRUID():
            return Spellslots(FULL_CASTER_TABLE[class_level])
        case Class.FIGHTER():
            return Spellslots(QUARTER_CASTER_TABLE[class_level]) if class_name is Class.FIGHTER.ELDRITCH_KNIGHT else None
        case Class.PALADIN():
            return Spellslots(HALF_CASTER_TABLE[class_level])
        case Class.RANGER():
            return Spellslots(HALF_CASTER_TABLE[class_level])
        case Class.ROGUE():
            return Spellslots(QUARTER_CASTER_TABLE[class_level]) if class_name is Class.ROGUE.ARCANE_TRICKSTER else None
        case Class.SORCERER():
            return Spellslots(FULL_CASTER_TABLE[class_level])
        case Class.WARLOCK():
            return Spellslots(WARLOCK_TABLE[class_level])
        case Class.WIZARD():
            return Spellslots(FULL_CASTER_TABLE[class_level])
        case Class.ARTIFICER():
            return Spellslots(HALF_CASTER_TABLE[class_level])
        case _:
            return None


class Spellslots(Resource):
    def __init__(self, spellslot_table):
        Resource.__init__(self, ResourceRefreshType.LONG_REST)
        self.max_spellslots = copy.deepcopy(spellslot_table)
        self.curr_spellslots = copy.deepcopy(spellslot_table)

    def has_resource(self, **kwargs):
        level = kwargs.get("level", None)
        return self.curr_spellslots[level]

    def use_resource(self, **kwargs):
        try:
            level = kwargs["level"]
            self.curr_spellslots[level] -= 1
        except KeyError:
            logger.error("Level of use_resource for Spellslots not specified!")

    def reset(self):
        self.curr_spellslots = copy.copy(self.max_spellslots)

    def export_resource(self):
        return copy.deepcopy(self.curr_spellslots)

    def import_resource(self, **kwargs):
        try:
            spellslots = kwargs["spellslots"]
            self.curr_spellslots = copy.deepcopy(spellslots)
        except KeyError:
            logger.error("Invalid Spellslots import resource!")
