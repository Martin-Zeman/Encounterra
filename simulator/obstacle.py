from numba import int32, int64
from numba.experimental import jitclass

# Define the spec for the Numba class
spec = [
    ('coord', int64[:]),  # coord is a tuple of two integers
    ('radius', int32)               # radius is an integer
]


@jitclass(spec)
class Obstacle:
    """
    Represents a piece of impassable terrain on the battle map
    """
    def __init__(self, coord, radius=0):
        """
        Initializes the obstacle
        :param coord: the center coord of the obstacle
        :param radius: the radius of the obstacle (0 = one 1x1, 1 = 3x3, 2 = 5x5 etc.)
        :return: None
        """
        self.coord = coord
        self.radius = radius

    def get_corners(self):
        return [(self.coord[0] - self.radius, self.coord[1] - self.radius),
                (self.coord[0] + self.radius + 1, self.coord[1] - self.radius),
                (self.coord[0] - self.radius, self.coord[1] + self.radius + 1),
                (self.coord[0] + self.radius + 1, self.coord[1] + self.radius + 1)]

    def get_center(self):
        return self.coord[0] + 0.5, self.coord[1] + 0.5
