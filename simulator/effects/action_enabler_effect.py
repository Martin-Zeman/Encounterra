from abc import abstractmethod

from simulator.effects.effect import Effect


class ActionEnablerEffect(Effect):
    """
    An effect that enables the combatant to perform new/different actions.
    """

    @abstractmethod
    def enable(self, battle_map):
        pass

    @abstractmethod
    def disable(self, battle_map):
        pass
