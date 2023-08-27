from abc import abstractmethod

from ..effects.effect import Effect


class ActionEnablerEffect(Effect):
    """
    An effect that enables the combatant to perform new/different actions.
    """

    @abstractmethod
    def enable(self):
        """
        This function makes modifications to the affected to allow them to perform new actions
        """
        pass

    @abstractmethod
    def disable(self):
        """
        This function returns the affected to the previous state
        """
        pass
