import scipy.linalg as la
import numpy as np
import matplotlib.pyplot as plt
import math
import sys


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
        self.__teams = teams
        self.grid = [[GridCell() for _ in range(size)] for _ in range(size)]
        self.base_adjacency_matrix = np.zeros((size, size))
        self.difficult_set = set()

    def place_circular_element(self, coords, type, diameter=1):
        N = self.size
        coords = (coords[0] - 1, coords[1] - 1) # convert to 1-based coordinates
        if (diameter == 1):
            if type == self.INACCESSIBLE:
                self.grid[max(0, min(coords[0], N - 1))][max(0, min(coords[1], N - 1))].is_accessible = False
            elif type == self.DIFFICULT_TERRAIN:
                self.grid[max(0, min(coords[0], N - 1))][max(0, min(coords[1], N - 1))].difficult_terrain = True
                self.difficult_set.add((coords[0], coords[1]))
        elif diameter > 1:
            for x in range(-math.floor(diameter/2), math.floor(diameter/2) + 1):
                for y in range(-math.floor(diameter/2), math.floor(diameter/2) + 1):
                    try:
                        if type == self.INACCESSIBLE:
                            self.grid[max(0, min(coords[0] + x, N - 1))][max(0, min(coords[1] + y, N - 1))].is_accessible = False
                        elif type == self.DIFFICULT_TERRAIN:
                            self.grid[max(0, min(coords[0] + x, N - 1))][max(0, min(coords[1] + y, N - 1))].difficult_terrain = True
                            self.difficult_set.add((max(0, min(coords[0] + x, N - 1)), max(0, min(coords[1] + y, N - 1))))
                    except:
                        pass #out of grid


    def print(self):
        pass

    def build_adjacency_matrix(self):
        N = self.size
        Nsq = N**2
        adj = np.zeros((N, N, N, N))
        # adj2 = np.zeros((N, N, N, N))
        # print(adj)
        # Take adj to encode (x,y) coordinate to (x,y) coordinate edges
        # Let's now connect the nodes
        for i in range(N):
            for j in range(N):
                # Connect x=i, y=j, to x-1 and x+1, y-1 and y+1
                # adj2[i, j, max((i - 1), 0):(i + 2), max((j - 1), 0):(j + 2)] = 1
                # print(f" i={i} j={j}")
                # print(f"from {max((j - 1), 0)} to {(j + 2)}")
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
        # adj2 = adj2.reshape(Nsq, Nsq)  # Back to node-to-node shape
        # Remove self-connections (optional)
        adj -= np.eye(Nsq)
        # print(adj)
        for coord in self.difficult_set:
            adj[:, coord[0] * N + coord[1]] *= 2
        self.base_adjacency_matrix = adj
        # plt.matshow(adj)
        # plt.show()

    def printSolution(self, dist, my_location, enemy_location):
        print("Vertex \tDistance from Source")
        my_coord = my_location[0]*self.size + my_location[1]
        enemy_coord = enemy_location[0]*self.size + enemy_location[1]
        for x in range(self.size):
            row = ""
            for y in range(self.size):
                coord = x*self.size + y
                if coord == my_coord:
                    row += "\x1b[38;5;39m%d  \x1b[0m" % dist[x * self.size + y]
                elif coord == enemy_coord:
                    row += "\x1b[38;5;196m%d  \x1b[0m" % dist[x * self.size + y]
                else:
                    row += "%d  " % dist[x*self.size + y]
            print(row)

    def minDistance(self, dist, sptSet):
        Nsq = self.size ** 2
        min = sys.maxsize

        for u in range(Nsq):
            if dist[u] < min and sptSet[u] == False:
                min = dist[u]
                min_index = u

        return min_index

    def dijkstra(self, src):
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
                if adj[x][y] > 0 and sptSet[y] is False and dist[y] > dist[x] + adj[x][y]:
                    dist[y] = dist[x] + adj[x][y]
                    shortest_paths[(y // N, y % N)] = (x // N, x % N)

        return dist, shortest_paths


    def convert_path_to_increments(self, path):
        increments = []
        for i in range(len(path) - 1):
            increments.append(path[i + 1] - path[i])
        print(increments)

    def move_character(self, coord_increments):
        pass

    def would_incur_aoo(self, coord, increment):
        return False

    def is_stepping_into_range(self, coord, increment):
        return False

    def get_character(self, x, y):
        return self.grid[x][y].get_character()

    def is_empty(self, x, y):
        return self.grid[x][y].is_empty()

    def can_see(self, x1, y1, x2, y2):
        return True

    def shortest_distance(self, x1, y1, x2, y2):
        return 1

    def set_character_coordinates(self, character, x, y):
        self.grid[x-1][y-1].set_character(character)

    def get_nearest_enemy_name(self, character):
        """ TODO, simplified"""
        for row in self.grid:
            for cell in row:
                if not cell.is_empty() and not self.__teams.are_allies(cell.get_character(), character):
                    return cell.get_character().get_name()

    def get_path_to_enemy(self, character, target):
        my_location = self.get_character_position(character.name)
        enemy_location = self.get_character_position(target.name)
        print(f"My location {my_location}")
        print(f"Enemy location {enemy_location}")
        dist, shortest_path = self.dijkstra(my_location)
        # self.printSolution(dist, my_location, enemy_location)
        current_position = enemy_location
        path = []
        while not np.array_equal(current_position, my_location):
            path.append(current_position)
            # have to convert to tuple cause numpy array is non-hashable
            current_position = shortest_path[tuple(current_position)]
        else:
            path.append(my_location)
        path.reverse()
        return self.convert_path_to_increments(path)

    def get_character_position(self, name):
        for i, row in enumerate(self.grid):
            for j, cell in enumerate(row):
                character = cell.get_character()
                if character and character.get_name() == name:
                    return np.array([i, j])
        return None
