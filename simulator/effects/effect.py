from enum import Enum, auto
from abc import ABC, abstractmethod


class Effect(ABC):
    # class TargetType(Enum):
    #     SPHERE = auto()
    #     AURA_SPHERE = auto()
    #     SQUARE = auto()
    #     CYLINDER = auto()
    #     COMBATANTS = auto()

    # def __del__(self):
    #     self.deactivate()

    @abstractmethod
    def activate(self):
        pass

    @abstractmethod
    def deactivate(self):
        pass

    @abstractmethod
    def is_affecting(self, combatant):
        return False
