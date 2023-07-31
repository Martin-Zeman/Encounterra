import numpy as np
import logging
from simulator.misc import Size

logger = logging.getLogger("Encounterra")

class Coords:
    """
    Represents a set of coordinates taken up by a combatant
    """
    def __init__(self, coord: np.array, size: Size=Size.MEDIUM):
        """
        Initializes the combatant coords with a root coordinate
        :param coord: the root coord of the combatant, it gets turned into n x 2 matrix where one row represents one coordinate
        :return: None
        """
        self.size = size
        match self.size:
            case Size.TINY | Size.SMALL | Size.MEDIUM:
                self.coords = np.array([coord])
            case Size.LARGE:
                self.coords = np.array([coord, coord + (0, 1),
                                        coord + (1, 0), coord + 1])
            case Size.HUGE:
                self.coords = np.array([coord, coord + (0, 1), coord + (0, 2),
                                       coord + (1, 0), coord + (1, 1), coord + (1, 2),
                                       coord + (2, 0), coord + (2, 1), coord + (2, 2)])
            case Size.GARGANTUAN:
                self.coords = np.array([coord, coord + (0, 1), coord + (0, 2), coord + (0, 3),
                                        coord + (1, 0), coord + (1, 1), coord + (1, 2), coord + (1, 3),
                                        coord + (2, 0), coord + (2, 1), coord + (2, 2), coord + (2, 3),
                                        coord + (3, 0), coord + (3, 1), coord + (3, 2), coord + (3, 3)])
            case _:
                logger.error("Unknown combatant size")

    def get(self):
        return self.coords

    def set(self, coords):
        self.coords = coords

    def get_corners(self):
        size = max(0, self.size.value)
        return [self.coords[0], self.coords[0] + (size + 1, 0), self.coords[0] + (0, size + 1), self.coords[0] + (size + 1, size + 1)]

    def get_center(self):
        size = max(0, self.size.value)
        return self.coords[0] + (np.array((size + 1, size + 1)) / 2)

    def __add__(self, other):
        return Coords(self.coords[0] + other, self.size)
