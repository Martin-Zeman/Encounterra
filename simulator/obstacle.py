import numpy as np

class Obstacle:
    """
    Represents a piece of impassable terrain on the battle map
    """
    def __init__(self, coord: np.array, radius=0):
        """
        Initializes the obstacle
        :param coord: the center coord of the obstacle
        :param radius: the radius of the obstacle (0 = one 1x1, 1 = 3x3, 2 = 5x5 etc.)
        :return: None
        """
        self.coord = coord
        self.radius = radius


    def get_corners(self):
        return [self.coord - (self.radius, self.radius), self.coord + (self.radius + 1, - self.radius), self.coord +
                (-self.radius, self.radius + 1), self.coord + (self.radius + 1, self.radius + 1)]

    def get_center(self):
        return self.coord + (0.5, 0.5)
