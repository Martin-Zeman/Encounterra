import scipy.linalg as la
import numpy as np
import matplotlib.pyplot as plt
import math
import sys
import logging

logger = logging.getLogger(__name__)

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

    DIFFICULT_TERRAIN = 1
    INACCESSIBLE = 2

    def __init__(self, size, teams):
        self.size = size
        self.teams = teams
        self.grid = [[GridCell() for _ in range(size)] for _ in range(size)]
        self.base_adjacency_matrix = np.zeros((size, size))
        self.difficult_set = set()
        self.character_coordinate_cache = {}

    def place_circular_element(self, coords, element_type, diameter=1):
        N = self.size
        coords = (coords[0] - 1, coords[1] - 1) # convert to 1-based coordinates
        if diameter == 1:
            if element_type == self.INACCESSIBLE:
                self.grid[max(0, min(coords[0], N - 1))][max(0, min(coords[1], N - 1))].is_accessible = False
            elif element_type == self.DIFFICULT_TERRAIN:
                self.grid[max(0, min(coords[0], N - 1))][max(0, min(coords[1], N - 1))].difficult_terrain = True
                self.difficult_set.add((coords[0], coords[1]))
        elif diameter > 1:
            for x in range(-math.floor(diameter/2), math.floor(diameter/2) + 1):
                for y in range(-math.floor(diameter/2), math.floor(diameter/2) + 1):
                    try:
                        if element_type == self.INACCESSIBLE:
                            self.grid[coords[0] + x][coords[1] + y].is_accessible = False
                        elif element_type == self.DIFFICULT_TERRAIN:
                            self.grid[coords[0] + x][coords[1] + y].difficult_terrain = True
                            self.difficult_set.add((coords[0] + x, coords[1] + y))
                    except IndexError:
                        pass #out of grid


    def print(self):
        pass

    def build_adjacency_matrix(self):
        N = self.size
        Nsq = N**2
        adj = np.zeros((N, N, N, N))
        # Take adj to encode (x,y) coordinate to (x,y) coordinate edges
        # Let's now connect the nodes
        for i in range(N):
            for j in range(N):
                adj[i, j, max((i - 1), 0), max((j - 1), 0)] = 1
                adj[i, j, max((i - 1), 0), j] = 1
                adj[i, j, max((i - 1), 0), min(j + 1, N-1)] = 1

                adj[i, j, i, max((j - 1), 0)] = 1
                adj[i, j, i, j] = 1
                adj[i, j, i, min(j + 1, N-1)] = 1

                adj[i, j, min(i + 1, N-1), max((j - 1), 0)] = 1
                adj[i, j, min(i + 1, N-1), j] = 1
                adj[i, j, min(i + 1, N-1), min(j + 1, N-1)] = 1

                # max is used to avoid negative slicing, and +2 is used because
                # slicing does not include last element.
        adj = adj.reshape(Nsq, Nsq)  # Back to node-to-node shape
        # Remove self-connections (optional)
        adj -= np.eye(Nsq)
        for coord in self.difficult_set:
            adj[:, coord[0] * N + coord[1]] *= 2
        self.base_adjacency_matrix = adj

    def printSolution(self, dist, my_location, enemy_location, reconstructed_path):
        my_coord = my_location[0]*self.size + my_location[1]
        enemy_coord = enemy_location[0]*self.size + enemy_location[1]
        for x in range(self.size):
            row = ""
            for y in range(self.size):
                coord = x*self.size + y
                if coord == my_coord:
                    row += "\x1b[38;5;39m%d\x1b[0m\t" % dist[coord]
                elif coord == enemy_coord:
                    row += "\x1b[38;5;196m%d\x1b[0m\t" % dist[coord]
                elif (x, y) in reconstructed_path:
                    row += "\u001b[36m%d\x1b[0m\t" % dist[coord]
                else:
                    row += "%d\t" % dist[coord] if (x, y) not in self.difficult_set else "\x1b[38;5;226m%d\x1b[0m\t" % dist[coord]
            logger.debug(row)

    def minDistance(self, dist, sptSet):
        Nsq = self.size ** 2
        min = sys.maxsize

        for u in range(Nsq):
            if dist[u] < min and sptSet[u] is False:
                min = dist[u]
                min_index = u

        return min_index

    def dijkstra(self, src):
        src = np.array(src)
        N = self.size
        Nsq = self.size**2
        dist = [sys.maxsize] * Nsq
        dist[src[0] * self.size + src[1]] = 0
        sptSet = [False] * Nsq
        adj = self.base_adjacency_matrix
        shortest_paths = {}

        for _ in range(Nsq):
            x = self.minDistance(dist, sptSet)
            sptSet[x] = True
            for y in range(Nsq):
                if adj[x][y] > 0 and sptSet[y] is False:
                    coord_to = (y // N, y % N)
                    coord_to_np = np.array([coord_to[0], coord_to[1]])
                    coord_from = np.array([x // N, x % N])
                    if dist[y] > dist[x] + adj[x][y]:
                        dist[y] = dist[x] + adj[x][y]
                        shortest_paths[coord_to] = coord_from
                    elif dist[y] >= dist[x] + adj[x][y] and np.sum(np.abs(shortest_paths[coord_to] - coord_to_np)) > np.sum(np.abs(coord_to_np - coord_from)):
                        # prefer the path with the least coordinate diff, i.e. the less zig-zaggy path
                        shortest_paths[coord_to] = coord_from

        return dist, shortest_paths

    def convert_path_to_increments(self, path):
        increments = []
        for i in range(len(path) - 1):
            increments.append(path[i + 1] - path[i])
        logger.debug(increments)
        return increments

    def move_character(self, character, increment):
        old_coord = self.character_coordinate_cache[character]
        self.grid[old_coord[0]][old_coord[1]].set_character(None)
        new_coord = old_coord + increment
        try:
            self.grid[new_coord[0]][new_coord[1]].set_character(character)
        except IndexError as e:
            logger.error(e)
        self.character_coordinate_cache[character] = new_coord
        logger.debug(f"{character.get_name()} moved to {new_coord}", extra={"team": self.teams.get_team(character)})

    def would_incur_aoo(self, coord, increment):
        return False

    def get_aoo_illegible_characters(self, character, increment):
        return None

    def get_pam_illegible_characters(self, character, increment):
        return None

    def is_stepping_into_range(self, coord, increment):
        return False

    # def get_character(self, x, y):
    #     return self.grid[x][y].get_character()

    def is_empty(self, x, y):
        return self.grid[x][y].is_empty()

    def can_see(self, x1, y1, x2, y2):
        return True

    def shortest_distance(self, x1, y1, x2, y2):
        return 1

    def set_character_coordinates(self, character, coord):
        # TODO: redo this as np.array
        self.grid[coord[0]][coord[1]].set_character(character)
        self.character_coordinate_cache[character] = coord

    def get_nearest_enemy(self, character):
        min_dist = sys.float_info.max
        nearest_enemy = None
        self_position = self.character_coordinate_cache[character]
        for potential_target, target_coord in self.character_coordinate_cache.items():
            dist = np.linalg.norm(target_coord - self_position)
            if potential_target is not character and not self.teams.are_allies(potential_target, character) and dist < min_dist:
                min_dist = dist
                nearest_enemy = potential_target
        return nearest_enemy

    def are_in_range(self, character1, character2, range):
        char1_position = np.array(self.character_coordinate_cache[character1])
        char2_position = np.array(self.character_coordinate_cache[character2])
        return np.max(np.abs(char1_position - char2_position)) <= range

    def reconstruct_from_shortest_path(self, shortest_path, my_location, enemy_location):
        current_position = enemy_location
        path = {'tuples' : [], 'numpy': []}
        while not np.array_equal(current_position, my_location):
            path['numpy'].append(current_position)
            path['tuples'].append(tuple(current_position))
            # have to convert to tuple cause numpy array is non-hashable
            current_position = shortest_path[tuple(current_position)]
        else:
            path['numpy'].append(my_location)
            path['tuples'].append(tuple(my_location))
        path['numpy'].reverse()
        path['tuples'].reverse()
        return path

    def get_path_to_enemy(self, character, target):
        my_location = self.get_character_position(character.name)
        enemy_location = self.get_character_position(target.name)
        print(f"My location {my_location}")
        print(f"Enemy location {enemy_location}")
        dist, shortest_path = self.dijkstra(my_location)
        reconstructed_path = self.reconstruct_from_shortest_path(shortest_path, my_location, enemy_location)
        self.printSolution(dist, my_location, enemy_location, reconstructed_path['tuples'])
        return self.convert_path_to_increments(reconstructed_path['numpy'])

    def get_character_position(self, name):
        for i, row in enumerate(self.grid):
            for j, cell in enumerate(row):
                character = cell.get_character()
                if character and character.get_name() == name:
                    return np.array([i, j])
        return None

    def remove_character(self, character):
        old_coord = self.character_coordinate_cache[character]
        self.grid[old_coord[0]][old_coord[1]].set_character(None)
        del self.character_coordinate_cache[character]
