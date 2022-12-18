from enum import Enum


class Actoid:
    class Type(Enum):
        IS_TARGETED_COMBAT_ACTION = 1
        IS_MOVEMENT = 2
        IS_SPELL = 3
        IS_DODGE = 4

    def __init__(self, type):
        self.actoid_type = type
