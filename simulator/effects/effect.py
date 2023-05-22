from enum import Enum, auto
from abc import ABC, abstractmethod


class Effect(ABC):

    @abstractmethod
    def activate(self, battle_map):
        pass

    @abstractmethod
    def deactivate(self, battle_map):
        pass

    @abstractmethod
    def is_affecting(self, combatant, battle_map):
        return False
