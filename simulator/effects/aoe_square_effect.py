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
        grid_size = battle_map.size
        coords = []
        for x, y in [(self.origin[0] + i, self.origin[1] + j) for i in range(1, self.length + 1) for j in range(1, self.length + 1)]:
            if x < 0 or x >= grid_size or y < 0 or y >= grid_size:
                continue
            coords.append(np.array([x, y]))
        return np.stack([c for c in coords])

    def is_affecting(self, combatant):
        return False  # TODO
