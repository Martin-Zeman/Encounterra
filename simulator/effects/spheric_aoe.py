import numpy as np

from ..battle_map import Map
from ..effects.aoe_effect import AoeEffect
from ..geometry import get_square_center


class SphericAoe:

    def __init__(self, coord, radius):
        self.origin = coord
        self.radius = radius
        self.affected_coords = self._get_affected_coords()

    def _get_affected_coords(self):
        battle_map = Map.get()
        grid_size = battle_map.size
        coords = []
        origin_center = get_square_center(self.origin)
        for x, y in [(self.origin[0] + i, self.origin[1] + j) for i in range(-self.radius, self.radius + 1) for j in range(-self.radius, self.radius + 1)]:
            if x < 0 or x >= grid_size or y < 0 or y >= grid_size:
                continue
            curr_coord_center = get_square_center(np.array([x, y]))
            if np.linalg.norm(origin_center - curr_coord_center) <= self.radius:
                coords.append(np.array([x, y]))
        return np.stack([c for c in coords])

    def get_affected_coords(self):
        return self.affected_coords
