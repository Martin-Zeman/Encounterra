from enum import Enum, auto
from abc import ABC, abstractmethod


class Actoid(ABC):
    class Type(Enum):
        IS_ATTACK_LIKE_ACTION = auto()
        IS_MOVEMENT = auto()
        IS_SPELL = auto()
        IS_DODGE = auto()
        IS_DASH = auto()
        IS_TOGGLE_ABILITY = auto()

    def __init__(self, actoid_type):
        self.actoid_type = actoid_type
        self.action_type = None

    @abstractmethod
    @staticmethod
    def calculate_threat_approx(combatant, battle_map, *args, **kwargs):
        return 0

    @abstractmethod
    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        return 0
