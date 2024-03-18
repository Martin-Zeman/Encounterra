from ..battle_map import Map


class SquareAoe:

    def __init__(self, origin, length):
        self.origin = origin
        self.length = length
        self.affected_coords = Map.get().get_coords_affected_by_square_aoe(self.origin, self.length)

    def get_affected_coords(self):
        """
        Gets coordinates of grid squares affected by a square effect originating at bottom left corner of a square at origin coordinates.
        :return: affected coordinates as a np.array of nx2 where n is the number of coordinates returned
        """
        return self.affected_coords
