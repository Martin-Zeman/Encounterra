from enum import Enum
import logging

logger = logging.getLogger(__name__)

class Spellslots:
    class Class(Enum):
        BARD = 1
        CLERIC = 2
        DRUID = 3
        ELDRIDGE_KNIGHT = 4
        PALADIN = 5
        RANGER = 6
        ARCANE_TRICKSTER = 7
        SORCERER = 8
        WARLOCK = 9
        WIZARD = 10
        ARTIFICER = 11

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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 1
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
            9: 1
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
            9: 1
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
            9: 1
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 0
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
            9: 1
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
            9: 1
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
            9: 1
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
            9: 1
        }
    }

    def __init__(self, class_name, class_level):
        self.max_spellslots = {}
        self.curr_spellslots = {}
        self.class_level = class_level
        self.class_name = class_name
        match class_name:
            case self.Class.BARD:
                self.max_spellslots = self.FULL_CASTER_TABLE
                self.curr_spellslots = self.FULL_CASTER_TABLE
                return
            case self.Class.CLERIC:
                self.max_spellslots = self.FULL_CASTER_TABLE
                self.curr_spellslots = self.FULL_CASTER_TABLE
                return
            case self.Class.DRUID:
                self.max_spellslots = self.FULL_CASTER_TABLE
                self.curr_spellslots = self.FULL_CASTER_TABLE
                return
            case self.Class.ELDRIDGE_KNIGHT:
                self.max_spellslots = self.QUARTER_CASTER_TABLE
                self.curr_spellslots = self.QUARTER_CASTER_TABLE
                return
            case self.Class.PALADIN:
                self.max_spellslots = self.HALF_CASTER_TABLE
                self.curr_spellslots = self.HALF_CASTER_TABLE
                return
            case self.Class.RANGER:
                self.max_spellslots = self.HALF_CASTER_TABLE
                self.curr_spellslots = self.HALF_CASTER_TABLE
                return
            case self.Class.ARCANE_TRICKSTER:
                self.max_spellslots = self.QUARTER_CASTER_TABLE
                self.curr_spellslots = self.QUARTER_CASTER_TABLE
                return
            case self.Class.SORCERER:
                self.max_spellslots = self.FULL_CASTER_TABLE
                self.curr_spellslots = self.FULL_CASTER_TABLE
                return
            case self.Class.WARLOCK:
                self.max_spellslots = self.WARLOCK_TABLE
                self.curr_spellslots = self.WARLOCK_TABLE
                return
            case self.Class.WIZARD:
                self.max_spellslots = self.FULL_CASTER_TABLE
                self.curr_spellslots = self.FULL_CASTER_TABLE
                return
            case self.Class.ARTIFICER:
                self.max_spellslots = self.HALF_CASTER_TABLE
                self.curr_spellslots = self.HALF_CASTER_TABLE
                return

    def add_spellslots(self, class_name, level):
        pass

    def add_spellslot(self, class_name, level):
        pass

    def restore_spellslot(self, class_name, level):
        pass

    def has_spellslots(self, level):
        return self.curr_spellslots[self.class_level][level]

    def use_spellslot(self, level):
        try:
            self.curr_spellslots[self.class_level][level] -= 1
        except:
            logger.error("Something gone wrong with spellslots!")
