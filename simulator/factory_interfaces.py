import logging
from abc import ABC, abstractmethod

from .actions.actoid import FactoryFlags
from .misc import roll_dice
from .threat_interfaces import Threat

logger = logging.getLogger("Encounterra")

class Factory:
    def __init__(self):
        self.flags = FactoryFlags.DEFAULT

    @abstractmethod
    def create_all(self, previous_action_in_dag=None):
        return []

    @abstractmethod
    def create(self, target):
        return None


class DirectThreatFactory(ABC, Factory):

    def __init__(self):
        Factory.__init__(self)
        self.flags |= FactoryFlags.IS_DIRECT_THREAT

    """
    Threat calculation for factories. They compute an estimation of the threat potential based on its stats.
    It also mandates that a factory be able to compute a threat increment based on a dictionary of modified stats
    """
    @abstractmethod
    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates the threat the factory is capable of dealing to a specific target.
        This is useful for calculating threat_in from the abilities of enemies
        """
        return 0

    @abstractmethod
    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications.
        This is useful calculating the potential reduction of threat_in caused by abilities of enemies, e.g. advantage on saving throw
        against fireball or bane on attack rolls etc.
        """
        return 0

    @abstractmethod
    def calculate_max_threat(self):
        """
        The theoretical maximum threat the factory is able to generate.
        """
        return 0


class RechargeFactory(ABC, Factory):

    def __init__(self, recharge_value):
        Factory.__init__(self)
        self.recharge_value = recharge_value
        self.flags |= FactoryFlags.IS_RECHARGE

    def roll_for_recharge(self):
        roll = roll_dice([(1, 6)])
        resource = self.combatant.resources[self.action_type]
        if not resource.has_resource() and roll >= self.recharge_value:
            logger.info(f"{self.combatant}'s {self.get_ability_name()} recharges")
            self.combatant.resources[self.action_type].reset()


class TransformerFactory(Threat, Factory):
    """
    A factory that modifies the user and the factories they have at their disposal
    """
    pass


class ThreatModifierFactory(ABC, Factory):
    """
    Threat calculation for factories that modify threat of other abilities (buffs and debuffs). This kind of factory doesn't support
    the calculation of modification by other ThreatModifierFactory to avoid endless loops.
    """

    @abstractmethod
    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates the threat the factory is capable of dealing to a specific target by modifying other factories.
        This is useful for calculating threat_in from the abilities of enemies
        """
        return 0