from abc import abstractmethod

from ..battle_map import Map
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

    def is_affecting(self, combatant):
        battle_map = Map.get()
        coords = self.get_affected_coords()
        return battle_map.get_hop_distance_coords(battle_map.get_combatant_position(combatant).get(), coords) == 0
