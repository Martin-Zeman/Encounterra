import numpy as np

from simulator.effects.aoe_effect import AoeEffect
from simulator.geometry import get_square_center


class AoeSphericEffect(AoeEffect):

    def __init__(self, coord, radius):
        self.coord = coord
        self.radius = radius

    def get_affected_coords(self, battle_map):
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
