import numpy as np

from simulator.effects.aoe_effect import AoeEffect


class AoeSquareEffect(AoeEffect):

    def __init__(self, origin, length):
        self.origin = origin
        self.length = length

    def get_affected_coords(self, battle_map):
        """
        Gets coordinates of grid squares affected by a square effect originating at bottom left corner of a square at origin coordinates.
        :param battle_map:
        :return: affected coordinates as a np.array of nx2 where n is the number of coordinates returned
        """
        return battle_map.get_coords_affected_by_square_aoe(self.origin, self.length)

    def is_affecting(self, combatant, battle_map):
        return False  # TODO
