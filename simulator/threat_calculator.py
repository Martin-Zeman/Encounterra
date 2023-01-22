from enum import Enum, auto
from abc import ABC, abstractmethod

class DirectThreat(ABC):
    """
    Direct dmg causing ability, directly healing ability or an ability that directly prevents dmg
    """

    @abstractmethod
    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        return 0


class ThreatModifier(ABC):
    """
    Ability that modifies threat of other abilities
    """
    # @abstractmethod
    # @staticmethod
    # def calculate_threat_mod_approx(combatant, battle_map, actions, *args, **kwargs):
    #     return 0

    @abstractmethod
    def calculate_threat_mod(self, combatant, battle_map, *args, **kwargs):
        return 0

class ReactionToThreat(ABC):
    """
    An ability that has the potential to mitigate an incoming threat
    """
    # TODO Do I really need this?

    @abstractmethod
    def calculate_threat_mod(self, combatant, battle_map, incoming_action, actor, *args, **kwargs):
        return 0


class FactoryThreat(ABC):
    """
    Threat calculation for factories. They compute an estimation of the threat potential based on its stats.
    It also mandates that a factory be able to compute a threat increment based on a dictionary of modified stats
    """
    @abstractmethod
    def calculate_threat_approx(self, battle_map, *args, **kwargs):
        return 0

    @abstractmethod
    def calculate_threat_approx_mod(self, battle_map, modified_stats, *args, **kwargs):
        return 0

