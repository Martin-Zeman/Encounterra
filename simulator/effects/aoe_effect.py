from abc import abstractmethod
from simulator.effects.effect import Effect

class AoeEffect(Effect):

    @abstractmethod
    def get_affected_coords(self, battle_map):
        pass

    @abstractmethod
    def on_enter(self, combatant):
        pass

    @abstractmethod
    def on_start_of_turn(self, combatant):
        pass

    @abstractmethod
    def on_end_of_turn(self, combatant):
        pass