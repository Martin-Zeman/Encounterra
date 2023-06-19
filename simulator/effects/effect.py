from enum import Enum, auto
from abc import ABC, abstractmethod

# This class is an optimization which makes the matching of the type faster
class EffectType(Enum):
    POST_HASTE_LETHARGY = auto()
    WILDSHAPE = auto()
    RAGE = auto()
    TOTEM_RAGE = auto()
    HASTE = auto()
    TWINNED_HASTE = auto()
    DODGE = auto()
    DISENGAGE = auto()
    RECKLESS_ATTACK = auto()
    FLAMING_SPHERE = auto()
    SPIKE_GROWTH = auto()
    CLOUD_OF_DAGGERS = auto()
    HUNGER_OF_HADAR = auto()
    HOLD_PERSON = auto()


class Effect(ABC):

    @abstractmethod
    def get_effect_type(self):
        pass

    @abstractmethod
    def activate(self, battle_map):
        pass

    @abstractmethod
    def deactivate(self, battle_map):
        pass

    @abstractmethod
    def is_affecting(self, combatant, battle_map):
        return False
