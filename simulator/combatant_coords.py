# import numpy as np
# import logging
# from .misc import Size
#
# logger = logging.getLogger("Encounterra")
#
#
# class Coords:
#     """
#     Represents a set of coordinates taken up by a combatant
#     """
#     def __init__(self, coord: np.array, size: Size=Size.MEDIUM):
#         """
#         Initializes the combatant coords with a root coordinate
#         :param coord: the root coord of the combatant, it gets turned into n x 2 matrix where one row represents one coordinate
#         :return: None
#         """
#         self.size = size
#         match self.size:
#             case Size.TINY | Size.SMALL | Size.MEDIUM:
#                 self.coords = np.array([coord])
#             case Size.LARGE:
#                 self.coords = np.array([coord, coord + (0, 1),
#                                         coord + (1, 0), coord + 1])
#             case Size.HUGE:
#                 self.coords = np.array([coord, coord + (0, 1), coord + (0, 2),
#                                        coord + (1, 0), coord + (1, 1), coord + (1, 2),
#                                        coord + (2, 0), coord + (2, 1), coord + (2, 2)])
#             case Size.GARGANTUAN:
#                 self.coords = np.array([coord, coord + (0, 1), coord + (0, 2), coord + (0, 3),
#                                         coord + (1, 0), coord + (1, 1), coord + (1, 2), coord + (1, 3),
#                                         coord + (2, 0), coord + (2, 1), coord + (2, 2), coord + (2, 3),
#                                         coord + (3, 0), coord + (3, 1), coord + (3, 2), coord + (3, 3)])
#             case _:
#                 logger.error("Unknown combatant size")
#
#     def get(self):
#         return self.coords
#
#     def get_tuples(self):
#         return {tuple(coord) for coord in self.coords}
#
#     def set(self, coords):
#         self.coords = coords
#
#     def get_corners(self):
#         size = max(0, self.size.value)
#         return [self.coords[0], self.coords[0] + (size + 1, 0), self.coords[0] + (0, size + 1), self.coords[0] + (size + 1, size + 1)]
#
#     def get_center(self):
#         size = max(0, self.size.value)
#         return self.coords[0] + (np.array((size + 1, size + 1)) / 2)
#
#     def __add__(self, other):
#         return Coords(self.coords[0] + other, self.size)


import numpy as np
from numba import int64, int32
from numba import types
from numba.experimental import jitclass

from simulator.misc import Size


TINY = Size.TINY.value
SMALL = Size.SMALL.value
MEDIUM = Size.MEDIUM.value
LARGE = Size.LARGE.value
HUGE = Size.HUGE.value
GARGANTUAN = Size.GARGANTUAN.value

# Define the spec for the Numba class
spec = [
    ('size', int32),          # Size as an integer
    ('coords', types.Array(int64, 2, layout='C'))  # coords as a 2D array of int64
]


@jitclass(spec)
class Coords:
    """
    Represents a set of coordinates taken up by a combatant
    """
    def __init__(self, coord, size=MEDIUM):
        """
        Initializes the combatant coords with a root coordinate
        :param coord: the root coord of the combatant
        :param size: the size of the combatant (0 = Size.MEDIUM, 1 = Size.LARGE, etc.)
        :return: None
        """
        self.size = size
        if self.size <= MEDIUM:
            self.coords = np.zeros((1, 2), dtype=np.int64)
            self.coords[0] = coord
        elif self.size == LARGE:
            self.coords = np.zeros((4, 2), dtype=np.int64)
            self.coords[0] = coord
            self.coords[1] = coord + np.array((0, 1), dtype=np.int64)
            self.coords[2] = coord + np.array((1, 0), dtype=np.int64)
            self.coords[3] = coord + np.array((1, 1), dtype=np.int64)
        elif self.size == HUGE:
            self.coords = np.zeros((9, 2), dtype=np.int64)
            for i in range(3):
                for j in range(3):
                    self.coords[i * 3 + j] = coord + np.array((i, j), dtype=np.int64)
        elif self.size == GARGANTUAN:
            self.coords = np.zeros((16, 2), dtype=np.int64)
            for i in range(4):
                for j in range(4):
                    self.coords[i * 4 + j] = coord + np.array((i, j), dtype=np.int64)
        else:
            self.coords = np.zeros((1, 2), dtype=np.int64)
            self.coords[0] = coord

    def get(self):
        return self.coords

    # def get_tuples(self):
    #     return {tuple(coord) for coord in self.coords}

    def set(self, coords):
        self.coords = coords

    def get_corners(self):
        size = max(0, self.size)
        corners = np.empty((4, 2), dtype=np.int64)
        corners[0] = self.coords[0]
        corners[1] = self.coords[0] + np.array((size + 1, 0), dtype=np.int64)
        corners[2] = self.coords[0] + np.array((0, size + 1), dtype=np.int64)
        corners[3] = self.coords[0] + np.array((size + 1, size + 1), dtype=np.int64)
        return corners

    def get_center(self):
        size = max(0, self.size)
        return self.coords[0] + np.array((size + 1, size + 1), dtype=np.float64) / 2.0

    def __add__(self, other):
        return Coords(self.coords[0] + other, self.size)
