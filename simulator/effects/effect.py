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
    HIDE = auto()
    RECKLESS_ATTACK = auto()
    FLAMING_SPHERE = auto()
    SPIKE_GROWTH = auto()
    CLOUD_OF_DAGGERS = auto()
    HUNGER_OF_HADAR = auto()
    HOLD_PERSON = auto()
    FAERIE_FIRE = auto()
    DIGESTION = auto()


class Effect(ABC):

    def __init__(self, initiator):
        self.initiator = initiator

    @abstractmethod
    def get_effect_type(self):
        pass

    @abstractmethod
    def activate(self):
        pass

    @abstractmethod
    def deactivate(self):
        pass

    @abstractmethod
    def is_affecting(self, combatant):
        return False

    def end_of_turn(self):
        return True

    def start_of_turn(self):
        return True

    def new_turn(self):
        return True
