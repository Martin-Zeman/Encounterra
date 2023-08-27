from abc import abstractmethod
from ..effects.effect import Effect

class AoeEffect(Effect):

    @abstractmethod
    def get_affected_coords(self):
        pass

    @abstractmethod
    def on_enter(self, combatant):
        pass

    @abstractmethod
    def on_move_within(self, combatant):
        pass

    @abstractmethod
    def on_exit(self, combatant):
        pass

    @abstractmethod
    def on_start_of_turn(self, combatant):
        pass

    @abstractmethod
    def on_end_of_turn(self, combatant):
        pass