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
    REGENERATION = auto()
    BLESS = auto()
    RAY_OF_ENFEEBLEMENT = auto()
    SLEEP = auto()
    SHILLELAGH = auto()
    MENACING_ATTACK_FRIGHTENED = auto()


class Effect(ABC):

    def __init__(self, initiator):
        self.initiator = initiator

    @abstractmethod
    def get_effect_type(self):
        pass

    @abstractmethod
    def activate(self, **kwargs):
        pass

    @abstractmethod
    def deactivate(self):
        """
        Deactivate either the entire effect. This happens either when the effect expires or when the initiating
        combatant loses concentration (by dmg, dying or falling unconscious)
        """
        pass

    @abstractmethod
    def deactivate_for_combatant(self, combatant):
        """
        Deactivate either the entire effect or its instance for a given combatant.
        :return: True if the Effect is still up (e.g. at least for one combatant), False otherwise
        """
        pass

    @abstractmethod
    def is_affecting(self, combatant):
        return False

    def combatant_saved_at_end_of_turn(self, combatant):
        """
        :return: True by default for abilities that cannot be saved against.
        """
        return True

    def start_of_turn_for_combatant(self, combatant):
        """
        AFAIK, there are no abilities that can be saved against at the start of a turn but there are effects that could
        potentially kill a combatant.
        :return: True by default for all abilities.
        """
        return True

    def new_turn(self):
        return True
