from enum import Enum, auto
from abc import ABC, abstractmethod


class Effect(ABC):

    @abstractmethod
    def activate(self):
        pass

    @abstractmethod
    def deactivate(self):
        pass

    @abstractmethod
    def is_affecting(self, combatant):
        return False
