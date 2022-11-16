class GridCell:
    def __init__(self):
        self.character = None
        self.difficult_terrain = False
        self.is_opaque = False
        self.is_accessible = True

    def set_character(self, character):
        self.character = character

    def get_character(self):
        return self.character

    def set_opaqueness(self, opaque):
        self.is_opaque = opaque

    def set_accessibility(self, access):
        self.is_accessible = access

    def is_empty(self):
        return self.character is None


class Map:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[GridCell() for _ in range(width)] for _ in range(height)]

    def get_character(self, x, y):
        return self.grid[x][y].get_character()

    def is_empty(self, x, y):
        return self.grid[x][y].is_empty()

    def can_see(self, x1, y1, x2, y2):
        return True

    def shortest_distance(self, x1, y1, x2, y2):
        return 1

    def set_character_coordinates(self, character, x, y):
        self.grid[x][y].set_character(character)

    def get_nearest_enemy_name(self, character):
        """ TODO, simplified"""
        for row in self.grid:
            for cell in row:
                if not cell.is_empty() and cell.get_character().get_team() != character.get_team():
                    return cell.get_character().get_name()

    def get_character_position(self, name):
        for row, i in enumerate(self.grid):
            for cell, j in enumerate(row):
                if cell.get_character().get_name() == name:
                    return i, j
        return None
