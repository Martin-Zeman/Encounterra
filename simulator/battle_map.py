import copy
from functools import cache

import numpy as np
import sys

from cachetools import cached
from cachetools.keys import hashkey

import logging
from .actions.action_types import Passive
from .combatant_coords import Coords
from .obstacle import Obstacle
from .proto_combatant import ProtoCombatant
from .spells.spell import SpellStats
from .misc import Conditions, Size, Visibility, THREE_QUARTERS_COVER_ERROR_THRESHOLD, HALF_COVER_ERROR_THRESHOLD, \
    FULL_VISIBILITY_ERROR_THRESHOLD
from .geometry import get_affected_by_cone, get_bounding_box, find_fov_vectors, angle_between_vectors
from .misc import Side, DistanceMetric
from contextlib import contextmanager
from scipy.spatial import distance_matrix
from scipy.spatial.distance import euclidean
import heapq
from enum import Enum


logger = logging.getLogger("Encounterra")

SQRT_OF_TWO = 1.41421

def reconstruct_from_shortest_path(shortest_path, source, target):
    """
    Works backwards using the shortest paths produced by Dijkstra to obtain a sequence of coordinates from source to
    target.
    :param shortest_path: shortest path dict (output of Dijkstra)
    :param source: source coordinates
    :param target: target coordinates
    :return: path from source to target as a sequence of coordinates
    """
    current_position = target
    # The square of the enemy itself is inaccessible, have to take the closest free adjacent one
    path = {'tuples': [], 'numpy': []}
    while not np.array_equal(current_position, source):
        path['numpy'].append(current_position)
        path['tuples'].append(tuple(current_position))
        # have to convert to tuple cause numpy array is non-hashable
        try:
            current_position = shortest_path[tuple(current_position)]
        except KeyError as e:
            # logger.error(e)  # TODO remove this once fixed
            return None
    else:
        path['numpy'].append(source)
        path['tuples'].append(tuple(source))
    path['numpy'].reverse()
    path['tuples'].reverse()
    return path



def convert_path_to_increments(path):
    """
    Converts a sequence of coordinates to a sequence of coordinate increments
    target.
    :param path: path as a sequence of coordinates
    :return: sequence of increments
    """
    increments = []
    for i in range(len(path) - 1):
        increments.append(tuple(path[i + 1] - path[i]))
    logger.debug(increments)
    return increments


class Terrain(Enum):
    NORMAL_TERRAIN = 0
    DIFFICULT_TERRAIN = 1
    IMPASSABLE_TERRAIN = 2


class Occupancy(Enum):
    FREE = 1
    OCCUPIED_BY_COMBATANT = 2

class GridSquare:
    def __init__(self, dummy):
        """
        GridSquare constructor
        :param dummy: dummy arguments only needed for the vectorized construction of grid
        :return: None
        """
        self.combatant = None
        self.terrain = Terrain.NORMAL_TERRAIN
        self.is_opaque = False
        self.occupancy = Occupancy.FREE

    def set_combatant(self, combatant):
        try:
            assert (self.occupancy is Occupancy.FREE or self.combatant is combatant) and self.terrain is not Terrain.IMPASSABLE_TERRAIN
        except AssertionError:
            print("FIXME")
        self.combatant = combatant
        self.occupancy = Occupancy.OCCUPIED_BY_COMBATANT

    def remove_combatant(self):
        self.combatant = None
        self.occupancy = Occupancy.FREE

    def reset_terrain(self):
        self.terrain = Terrain.NORMAL_TERRAIN

    def set_occupancy(self, occupancy):
        self.occupancy = occupancy

    def is_empty(self):
        return self.occupancy is Occupancy.FREE and self.terrain is not Terrain.IMPASSABLE_TERRAIN

    def is_impassable(self):
        return self.terrain is Terrain.IMPASSABLE_TERRAIN

    def is_empty_or_self(self, combatant):
        return ((self.occupancy is Occupancy.FREE) or (self.combatant is combatant)) and self.terrain is not Terrain.IMPASSABLE_TERRAIN

    def is_difficult_terrain(self):
        return self.terrain is Terrain.DIFFICULT_TERRAIN

# def toggled_cache(func):
#     cached_func = cache(func)
#     def call_func(*args, **kwargs):
#         if args[0].cache_enabled:
#             return cached_func(*args, **kwargs)
#         else:
#             return func(*args, **kwargs)
#     return call_func


# def map_toggled_cache(func):
#     """
#     A custom cache decorator which is governed by the caching state of the Map.
#
#     When applied to a method, this decorator allows caching of the method's results based on the value of `cache_enabled`
#     of the Map singleton. If `cache_enabled` is True, the decorator caches the results of the method calls. If `cache_enabled`
#     is False, caching is bypassed, and the method is executed normally without caching.
#     """
#     cached_func = cache(func)
#     def call_func(*args, **kwargs):
#         if Map.get().cache_enabled:
#             return cached_func(*args, **kwargs)
#         else:
#             return func(*args, **kwargs)
#
#     call_func.cache_clear = cached_func.cache_clear
#     return call_func


def map_position_toggled_cache(func):
    """
    A custom cache decorator designed to be used on a method of an object instance that has the `cache_enabled` property and uses the
    current combatant position as a hashkey.

    When applied to a method, this decorator allows caching of the method's results based on the value of `cache_enabled`
    for the object instance. If `cache_enabled` is True, the decorator caches the results of the method calls. If `cache_enabled`
    is False, caching is bypassed, and the method is executed normally without caching.
    """
    cached_func = cache(func)
    def call_func(*args, **kwargs):
        battle_map = Map.get()
        if battle_map.cache_enabled:
            return cached_func(*args, **kwargs, position_hash=tuple(battle_map.get_combatant_position(args[0].factory.combatant).get()[0]))
        else:
            return func(*args, **kwargs)

    call_func.cache_clear = cached_func.cache_clear
    return call_func

def map_toggled_cache_with_key(key):
    """
    A custom cache decorator designed to be used on a method of an object instance that has the `cache_enabled` property and uses the
    current combatant position as a hashkey.

    When applied to a method, this decorator allows caching of the method's results based on the value of `cache_enabled`
    for the object instance. If `cache_enabled` is True, the decorator caches the results of the method calls. If `cache_enabled`
    is False, caching is bypassed, and the method is executed normally without caching.
    """
    parametrized_cache = cached(cache={}, key=key)
    def _map_toggled_cache_with_key(func):
        cached_func = parametrized_cache(func)
        def call_func(*args, **kwargs):
            battle_map = Map.get()
            if battle_map.cache_enabled:
                return cached_func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        call_func.cache_clear = cached_func.cache_clear
        return call_func
    return _map_toggled_cache_with_key


def toggled_cache(key):
    """
    A custom cache decorator designed to be used on a method of an object instance that has the `cache_enabled` property.

    When applied to a method, this decorator allows caching of the method's results based on the value of `cache_enabled`
    for the object instance. If `cache_enabled` is True, the decorator caches the results of the method calls. If `cache_enabled`
    is False, caching is bypassed, and the method is executed normally without caching.
    """
    parametrized_cache = cached(cache={}, key=key)
    def _toggled_cache(func):
        cached_func = parametrized_cache(func)
        def call_func(*args, **kwargs):
            if args[0].cache_enabled:
                return cached_func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        call_func.cache_clear = cached_func.cache_clear
        return call_func

    return _toggled_cache

class Map:
    _instance = None

    def __new__(cls, size, teams):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.size = size
            cls._instance.teams = teams
            vGridSquare = np.vectorize(GridSquare)
            init_grid = np.arange(size ** 2).reshape((size, size))
            cls._instance.grid = np.empty((size, size), dtype=object)
            cls._instance.grid[:, :] = vGridSquare(init_grid)
            cls._instance.base_adjacency_matrix = np.zeros((size, size))
            cls._instance.difficult_set = set()
            cls._instance.impassable_set = set()
            cls._instance.obstacles = []  # Same as impassable_set but using a different data type
            cls._instance.combatant_coordinate_cache = dict()  # Maps combatant -> coordinate
            cls._instance.effect_tracker = None
            cls._instance.cache_enabled = True
            cls._instance.combat_round = 0
        return cls._instance

    @classmethod
    def reset_singleton(cls):
        cls._instance = None

    @classmethod
    def get(cls):
        return cls._instance

    @classmethod
    def serialize_data(cls):
        if cls._instance is None:
            return None
        data = {
            'size': cls._instance.size,
            'teams': cls._instance.teams,
            'grid': cls._instance.grid,
            'base_adjacency_matrix': cls._instance.base_adjacency_matrix,
            'difficult_set': list(cls._instance.difficult_set),  # Sets need to be converted to lists
            'impassable_set': list(cls._instance.impassable_set),
            'obstacles': cls._instance.obstacles,
            'combatant_coordinate_cache': cls._instance.combatant_coordinate_cache,
            'effect_tracker': cls._instance.effect_tracker,
            'cache_enabled': cls._instance.cache_enabled,
            'combat_round': cls._instance.combat_round,
        }
        return data

    @classmethod
    def deserialize_data(cls, data):
        if data is not None:
            cls.__new__(cls, data['size'], data['teams'])
            cls._instance.grid = data['grid']
            cls._instance.base_adjacency_matrix = data['base_adjacency_matrix']
            cls._instance.difficult_set = set(data['difficult_set'])
            cls._instance.impassable_set = set(data['impassable_set'])
            cls._instance.obstacles = data['obstacles']
            cls._instance.combatant_coordinate_cache = data['combatant_coordinate_cache']
            cls._instance.effect_tracker = data['effect_tracker']
            cls._instance.cache_enabled = data['cache_enabled']
            cls._instance.combat_round = data['combat_round']


    def __str__(self):
        string_repr = ""
        for y in range(self.size - 1, -1, -1):
            row_text = ""
            for x in range(self.size):
                square = self.grid[x, y]
                combatant = square.combatant
                if combatant and not combatant.is_swallowed[1]:
                    # row_text += self.teams.get_team_color_code(combatant) + str(combatant)[0] + str(combatant)[-1] + "\x1b[0m\t"
                    row_text += str(combatant)[0] + str(combatant)[-1] + "\t"
                elif square.terrain is Terrain.DIFFICULT_TERRAIN:
                    row_text += "**\t"
                elif square.terrain is Terrain.IMPASSABLE_TERRAIN:
                    row_text += "XX\t"
                else:
                    row_text += "00\t"
            string_repr += row_text + "\n"
        return string_repr

    @contextmanager
    def as_if_combatant_position(self, combatant, coords: np.array):
        """
        Replaces the combatant's position with the given position
        :param combatant:
        :param coords: new coordinates for the combatant
        :return: the original coordiantes if new given coordiantes are valid, None otherwise
        """
        if coords is not None:
            original_coords = self.get_combatant_position(combatant)
            original_logger_level = logger.level
            try:
                logger.setLevel(logging.WARNING)
                # self.cache_enabled = False
                self.move_combatant(combatant, coords)
                yield original_coords.get()[0]
            finally:
                self.move_combatant(combatant, original_coords.get()[0])
                # self.cache_enabled = True
                logger.setLevel(original_logger_level)
        else:
            yield None

    @contextmanager
    def as_if_dist_delta_from_combatant(self, combatant1, combatant2, dist):
        """
        Context manager which pretends that the distance betweent two comabatans is modified by dist. Dist > 0 means farther away. Dist < 0
        means closer.
        """
        orig_dist_hop_func = self.get_hop_distance_combatants
        orig_dist_cartesian_func = self.get_cartesian_distance_combatants

        def monkeypatch_hop_dist_combatants(subject1, subject2):
            if subject1 is combatant1 and subject2 is combatant2:
                return max(1, orig_dist_hop_func(subject1, subject2) + dist)
            else:
                return orig_dist_hop_func(subject1, subject2)
        def monkeypatch_cartesian_dist(subject1, subject2):
            if subject1 is combatant1 and subject2 is combatant2:
                return max(1.0, orig_dist_cartesian_func(subject1, subject2) + dist)
            else:
                return orig_dist_cartesian_func(subject1, subject2)

        self.get_hop_distance_combatants = monkeypatch_hop_dist_combatants
        self.get_cartesian_distance_combatants = monkeypatch_cartesian_dist
        try:
            self.cache_enabled = False
            yield self
        finally:
            self.get_hop_distance_combatants = orig_dist_hop_func
            self.get_cartesian_distance_combatants = orig_dist_cartesian_func
            self.cache_enabled = True


    @contextmanager
    def replace_combatant_if_action_by_wildshaped(self, action, combatant, orig_coords: tuple):
        """
        Replaces the combatant's position with the position of a wilshaped form if the actor of the action is a wildshaped for
        :param action:
        :param combatant:
        :param orig_coords: the very original coordinates where the combatant actually is (before as_if... operator)
        :return: True if action is a wildshape action, False otherwise
        """
        if combatant is not action.factory.combatant:
            before_wildshape_position = self.get_combatant_position(combatant)
            try:
                self.cache_enabled = False
                self.teams.replace_combatant(combatant, action.factory.combatant)
                wildshape_position = self.find_wildshaped_coordinate(combatant, action.factory.combatant.size, orig_coords)
                assert wildshape_position
                self.remove_combatant(combatant)
                try:
                    self.set_combatant_coordinates(action.factory.combatant, np.array(wildshape_position))
                except Exception as e:
                    print("FIXME")
                yield True
            finally:
                self.teams.replace_combatant(action.factory.combatant, combatant)
                self.remove_combatant(action.factory.combatant)
                self.set_combatant_coordinates(combatant, before_wildshape_position.get()[0])
                self.cache_enabled = True
        else:
            yield False


    def find_wildshaped_coordinate(self, combatant, size: Size, orig_coords: tuple=None):  # TODO caching cancidate
        """
        Since the druid's size may increase when using wildshape we want to allow the druid to shift their position when doing so
        in order to fit. We have to contend that the battle_map vs matrix coords are swapped and y-axis is inverted w.r.t. rows.
        :param combatant: the combatant who wants to wildshpae
        :param size: size of the wildshaped form
        :param orig_coords: Optionally, the very original coordinates where the combatant actually is (before as_if... operator)
        :return: root coordinate of the wildshaped form
        """
        before_wildshape_coordinate = self.get_combatant_position(combatant).get()[0]
        before_wildshape_coordinate = (self.size - before_wildshape_coordinate[1] - 1, before_wildshape_coordinate[0])  # Convert to matrix coordinates
        map_accessibility_matrix = np.zeros((self.size, self.size))
        for coord in combatant.shortest_paths_cache.keys():
            map_accessibility_matrix[self.size - coord[1] - 1, coord[0]] = 1
        map_accessibility_matrix[before_wildshape_coordinate] = 1
        if orig_coords is not None:
            map_accessibility_matrix[self.size - orig_coords[1] - 1, orig_coords[0]] = 1

        start_row = before_wildshape_coordinate[0]
        end_row = min(before_wildshape_coordinate[0] + size.value, self.size - 1)
        start_col = max(before_wildshape_coordinate[1] - size.value, 0)
        end_col = before_wildshape_coordinate[1]

        possible_root_coordinates = []
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                possible_root_coordinates.append((row, col))

        result_coordinates = []
        for coord in possible_root_coordinates:
            if coord[0] - size.value < 0 or coord[1] + size.value >= self.size:
                continue
            if np.all(map_accessibility_matrix[coord[0] - size.value:coord[0] + 1, coord[1]:coord[1] + size.value + 1] > 0):
                result_coordinates.append((coord[1], self.size - 1 - coord[0]))  # Convert back to battle_map coords

        original_coordinate = (before_wildshape_coordinate[1], self.size - 1 - before_wildshape_coordinate[0])
        result_coordinates.sort(key=lambda point: euclidean(original_coordinate, point))

        return result_coordinates[0] if result_coordinates else None

    def set_effect_tracker(self, effect_tracker):
        self.effect_tracker = effect_tracker

    def place_circular_element(self, coord, terrain_type, radius=0):
        """
        Places a terrain element of a 'circular' type onto the map
        :param coord: origin coordinate of the terrain element
        :param terrain_type: difficult terrain or impassable terrain
        :param radius: radius of the element
        :return:
        """
        N = self.size
        if radius == 0:
            x = max(0, min(coord[0], N - 1))
            y = max(0, min(coord[1], N - 1))
            if terrain_type == Terrain.IMPASSABLE_TERRAIN:
                self.grid[x][y].terrain = Terrain.IMPASSABLE_TERRAIN
                self.impassable_set.add((coord[0], coord[1]))
                self.obstacles.append(Obstacle(coord))
            elif terrain_type == Terrain.DIFFICULT_TERRAIN:
                self.grid[x][y].terrain = Terrain.DIFFICULT_TERRAIN
                self.difficult_set.add((coord[0], coord[1]))
        elif radius > 0:
            if terrain_type == Terrain.IMPASSABLE_TERRAIN:
                self.obstacles.append(Obstacle(coord, radius))
            for x_offset in range(-radius, radius + 1):
                for y_offset in range(-radius, radius + 1):
                    x = max(0, min(coord[0] + x_offset, N - 1))
                    y = max(0, min(coord[1] + y_offset, N - 1))
                    try:
                        if terrain_type == Terrain.IMPASSABLE_TERRAIN:
                            self.grid[x][y].terrain = Terrain.IMPASSABLE_TERRAIN
                            self.impassable_set.add((x, y))
                            try:
                                self.difficult_set.remove((x, y))
                            except KeyError:
                                pass
                        elif terrain_type == Terrain.DIFFICULT_TERRAIN:
                            self.grid[x][y].terrain = Terrain.DIFFICULT_TERRAIN
                            self.difficult_set.add((x, y))
                            try:
                                self.impassable_set.remove((x, y))
                            except KeyError:
                                pass
                    except IndexError:
                        pass  # out of grid

    def build_adjacency_matrix(self):
        # start_time = time.time()
        N = self.size
        Nsq = N ** 2
        adj = np.zeros((N, N, N, N), dtype=int)
        # Take adj to encode (x,y) coordinate to (x,y) coordinate edges
        # Let's now connect the nodes
        for i in range(N):
            for j in range(N):
                # TODO I don't think the min is needed
                adj[i, j, max((i - 1), 0), max((j - 1), 0)] = 1
                adj[i, j, max((i - 1), 0), j] = 1
                adj[i, j, max((i - 1), 0), min(j + 1, N - 1)] = 1

                adj[i, j, i, max((j - 1), 0)] = 1
                adj[i, j, i, j] = 1
                adj[i, j, i, min(j + 1, N - 1)] = 1

                adj[i, j, min(i + 1, N - 1), max((j - 1), 0)] = 1
                adj[i, j, min(i + 1, N - 1), j] = 1
                adj[i, j, min(i + 1, N - 1), min(j + 1, N - 1)] = 1

        adj = adj.reshape(Nsq, Nsq)  # Back to node-to-node shape
        # Remove self-connections (optional)
        adj -= np.eye(Nsq, dtype=int)
        for coord in self.difficult_set:
            adj[:, coord[0] * N + coord[1]] *= 2

        for coord in self.impassable_set:
            adj[:, coord[0] * N + coord[1]] = 0
        self.base_adjacency_matrix = adj
        # print("---build_adjacency_matrix took %s seconds ---" % (time.time() - start_time))


    def build_flaming_sphere_adjacency_matrix(self):
        N = self.size
        Nsq = N ** 2
        adj = np.zeros((N, N, N, N), dtype=int)
        # Take adj to encode (x,y) coordinate to (x,y) coordinate edges
        # Let's now connect the nodes
        for i in range(N):
            for j in range(N):
                # TODO I don't think the min is needed
                adj[i, j, max((i - 1), 0), max((j - 1), 0)] = 1
                adj[i, j, max((i - 1), 0), j] = 1
                adj[i, j, max((i - 1), 0), min(j + 1, N - 1)] = 1

                adj[i, j, i, max((j - 1), 0)] = 1
                adj[i, j, i, j] = 1
                adj[i, j, i, min(j + 1, N - 1)] = 1

                adj[i, j, min(i + 1, N - 1), max((j - 1), 0)] = 1
                adj[i, j, min(i + 1, N - 1), j] = 1
                adj[i, j, min(i + 1, N - 1), min(j + 1, N - 1)] = 1

        adj_reshaped = adj.reshape(Nsq, Nsq)  # Back to node-to-node shape
        # Remove self-connections (optional)
        adj_reshaped -= np.eye(Nsq, dtype=int)
        for curr_combatant, coords in self.combatant_coordinate_cache.items():
            if curr_combatant.is_alive() and curr_combatant.size.value >= Size.LARGE.value:
                for coord in coords.get():
                    adj[:, :, max(0, coord[0]):(coord[0] + 1), max(0, coord[1]):(coord[1] + 1)].fill(0)
        for coord in self.impassable_set:
            adj[:, :, max(0, coord[0]):(coord[0] + 1), max(0, coord[1]):(coord[1] + 1)].fill(0)
        return adj_reshaped


    def build_combatant_adjacency_mask(self, combatant, consider_aoo=False):
        """
        Builds a combatant-specific mask for the adjacency matrix. It models enemies as being impassable by 0.
        Allies are considered difficult terrain (potentially on top of already difficult terrain).
        Optionally, moves that incur AoO are also modelled as difficult terrain to avoid it if possible.
        For combatants larger than MEDIUM obstacles are also inflated accordingly
        :param combatant: for whom the mask is to be constructed
        :param consider_aoo: True if should AoOs should be modelled as difficult terrain
        :return: adjacency matrix mask
        """
        N = self.size
        # TODO consider preallocating this for all combatants and only resetting it to ones

        offset = 0
        if combatant.size.value > Size.MEDIUM.value:
            offset = combatant.size.value

        mask = np.ones((self.size ** 2, self.size ** 2), dtype=int)
        mv_reshaped = mask.view().reshape(N, N, N, N)  # Reshape to NxNxNxN where first two coords are 'from' and second are 'to'
        for curr_combatant, coords in self.combatant_coordinate_cache.items():
            if curr_combatant is not combatant and curr_combatant.is_alive():
                for coord in coords.get():
                    # TODO try to do this more efficiently
                    # TODO even allies are now impassable, try and figure out of a way to improve this
                    # Inflate in the opposite direction (root coord is bottom left so this inflated from the top right to bottom left)
                    mv_reshaped[:, :, max(0, (coord[0] - offset)):(coord[0] + 1), max(0, (coord[1] - offset)):(coord[1] + 1)].fill(0)
        for coord in self.impassable_set:
            # Inflate in the opposite direction (root coord is bottom left so this inflated from the top right to bottom left)
            mv_reshaped[:, :, max(0, (coord[0] - offset)):(coord[0] + 1), max(0, (coord[1] - offset)):(coord[1] + 1)].fill(0)

        # account for AoO
        if consider_aoo:
            enemies = self.get_enemies(combatant)
            for e in enemies:
                if not e.has_reaction:
                    continue
                rng = e.melee_reaction_range
                coords = self.get_combatant_position(e)
                adj_coords = self.get_free_coords_in_hop_range(coords, inflate_to_dist=combatant.size.value, rng=rng)
                for ac in adj_coords:
                    # it should be ok to apply this to coords that are part of the set or inaccessible
                    mv_reshaped[ac[0], ac[1], :, :] *= 2

        # Inflate the edges of the map. Prevent larger combatants from stepping out of the map
        mv_reshaped[:, :, (N - offset):N, :].fill(0)
        mv_reshaped[:, :, :, (N - offset):N].fill(0)
        return mask

    def printDijkstra(self, distances, my_coords: np.array, enemy_coords: np.array, reconstructed_path):
        """
        Prints the distances to all locations on the map from my_location and highlights the reconstructed path to enemy_location.
        It prints it as standard cartesian coordinate system.
        ^ y
        |
        |
        _________> x
        0
        :param distances: list of distances to all coords (flattened)
        :param my_coords: coordinates of the source
        :param enemy_coords: coordinates of the destination
        :param reconstructed_path: list of coordinates from my_location to enemy_location
        :return: void
        """
        for y in range(self.size - 1, -1, -1):
            row = ""
            for x in range(self.size):
                coord = np.array([x, y])
                index = x * self.size + y
                dist = str(distances[index]) if distances[index] < sys.maxsize else "-"
                if any((my_coords[:] == coord).all(1)):  # basically equivalent to 'is coord in rows of my_coord'
                    row += "\x1b[38;5;39m%s\x1b[0m\t" % dist
                elif any((enemy_coords[:] == coord).all(1)):  # basically equivalent to 'is coord in rows of enemy_coords'
                    row += "\x1b[38;5;196m%s\x1b[0m\t" % dist
                elif (x, y) in reconstructed_path:
                    row += "\u001b[36m%s\x1b[0m\t" % dist
                else:
                    row += "%s\t" % dist if (x, y) not in self.difficult_set else "\x1b[38;5;226m%s\x1b[0m\t" % dist
            logger.debug(row)

    def minDistance(self, dist, open_set):
        """
        Helper function for the Dijkstra algorithm. Finds the index (coordinate) of an unexplored vertex with the lowest distance
        :param dist: list of distances to vertices
        :param open_set: list of vertices, True = explored, False = unexplored
        :return: index to min distance unexplored vertex
        """
        # TODO Consider replacing this with a priority queue
        Nsq = self.size ** 2
        min = sys.maxsize
        min_index = None

        for u in range(Nsq):
            if dist[u] < min and open_set[u] is False:
                min = dist[u]
                min_index = u
        return min_index

    def dijkstra(self, src, adj_matrix=None, mask=None):
        """
        Implementation of the Dijkstra algorithm with a preference for the least zig-zaggy path
        :param src: source coordinate
        :param adj_matrix: adjacency matrix, if None the base_adjacency_matrix will be used
        :param mask: combatant-specific mask for the adjacency matrix
        :return: list of distances to all vertices, list of predecessors for every vertex
        """
        # start_time = time.time()
        src = np.array(src)
        N = self.size
        Nsq = self.size ** 2
        dist = [sys.maxsize] * Nsq
        src_idx = src[0] * self.size + src[1]
        dist[src_idx] = 0
        open_set = [False] * Nsq
        adj_matrix = self.base_adjacency_matrix if adj_matrix is None else adj_matrix
        mask = np.ones((self.size ** 2, self.size ** 2), dtype=int) if mask is None else mask
        adj = np.multiply(adj_matrix, mask)
        shortest_paths = {}

        pq = [(0, src_idx)]
        while pq:
            _, x = heapq.heappop(pq)
            if open_set[x]:
                continue
            open_set[x] = True
            for y in range(Nsq):
                if adj[x][y] > 0 and not open_set[y]:
                    coord_to = (y // N, y % N)
                    coord_to_np = np.array([coord_to[0], coord_to[1]])
                    coord_from = np.array([x // N, x % N])
                    new_dist = dist[x] + adj[x][y]
                    if dist[y] > new_dist:
                        dist[y] = dist[x] + adj[x][y]
                        shortest_paths[coord_to] = coord_from
                        heapq.heappush(pq, (new_dist, y))
                    elif dist[y] >= new_dist and np.sum(np.abs(shortest_paths[coord_to] - coord_to_np)) > np.sum(
                            np.abs(coord_to_np - coord_from)):
                        # TODO this should also work with ==, try that
                        # prefer the path with the least coordinate diff, i.e. the less zig-zaggy path
                        shortest_paths[coord_to] = coord_from
                        heapq.heappush(pq, (new_dist, y))
        # end_time = time.time()
        # execution_time = end_time - start_time
        # print("Execution time:", execution_time)
        return dist, shortest_paths

    def get_pam_eligible_combatants(self, combatant, increment):
        eligible_combatants = []
        try:
            combatant_coords = self.combatant_coordinate_cache[combatant]
        except KeyError:
            # Follows after AoO, so the moving combatant might be dead
            return eligible_combatants
        for curr_combatant, coords in self.combatant_coordinate_cache.items():
            if curr_combatant is not combatant and self.teams.are_enemies(curr_combatant, combatant):
                if curr_combatant.is_affected_by_any(Conditions.INCAPACITATED, Conditions.STUNNED, Conditions.PARALYZED, Conditions.UNCONSCIOUS, Conditions.PETRIFIED):
                    continue
                try:
                    pre_increment_dist = self.get_hop_distance_combatants(combatant, curr_combatant)
                    post_increment_dist = self.get_hop_distance_coords(combatant_coords.get() + increment, coords.get())
                except KeyError:
                    continue
                if curr_combatant.has_passive(
                        Passive.POLEARM_MASTER) and pre_increment_dist > curr_combatant.melee_reaction_range and post_increment_dist == curr_combatant.melee_reaction_range and curr_combatant.has_reaction:
                    eligible_combatants.append(curr_combatant)
        return eligible_combatants

    def get_aoo_eligible_combatants(self, combatant, increment):
        eligible_combatants = []
        for curr_combatant, pos in self.combatant_coordinate_cache.items():
            if curr_combatant is not combatant and curr_combatant.is_alive() and self.teams.are_enemies(curr_combatant, combatant):
                if curr_combatant.is_affected_by_any(Conditions.INCAPACITATED, Conditions.STUNNED, Conditions.PARALYZED, Conditions.UNCONSCIOUS, Conditions.PETRIFIED):
                    continue
                pre_increment_dist = self.get_hop_distance_coords(self.combatant_coordinate_cache[combatant].get(), self.combatant_coordinate_cache[curr_combatant].get())
                post_increment_dist = self.get_hop_distance_coords(self.combatant_coordinate_cache[combatant].get() + increment, pos.get())
                if pre_increment_dist == curr_combatant.melee_reaction_range and post_increment_dist > curr_combatant.melee_reaction_range and curr_combatant.has_reaction:
                    eligible_combatants.append(curr_combatant)
        return eligible_combatants

    # @dispatch(np.array)
    def is_empty(self, coord):
        try:
            empty = self.grid[coord[0], coord[1]].is_empty()
        except IndexError:
            return False
        return empty

    def are_empty(self, coords: Coords):
        vec_is_empty = np.vectorize(GridSquare.is_empty)
        return np.all(vec_is_empty(self.grid[coords.get()[:, 0], coords.get()[:, 1]]))

    # @dispatch(Coords)
    def are_empty_or_self(self, coords: Coords, combatant):
        """
        The version of are_empty for larger combatants since when they're moving some squares are still going to be taken up by themselves
        """
        vec_is_empty = np.vectorize(lambda square: square.is_empty_or_self(combatant))
        return np.all(vec_is_empty(self.grid[coords.get()[:, 0], coords.get()[:, 1]]))

    def are_valid_coords(self, coords):
        return False if ((coords < 0).any() or (coords > self.size - 1).any()) else True


    def move_combatant_by_increment(self, combatant, increment):
        """
        Removes the combatant from the old coordinate and moves them to a new one by a given increment
        :param combatant:
        :param increment:
        :return:
        """
        old_coords = self.combatant_coordinate_cache[combatant].get()
        for old_coord in old_coords:
            self.grid[old_coord[0], old_coord[1]].remove_combatant()
        new_coords = old_coords + increment
        assert self.size > np.amax(new_coords) and np.amin(new_coords) > -1, f"Invalid coord {new_coords}"
        for new_coord in new_coords:
            self.grid[new_coord[0], new_coord[1]].set_combatant(combatant)
        self.combatant_coordinate_cache[combatant].set(new_coords)
        logger.info(f"{combatant} moved to {new_coords[0]}", extra={"team": self.teams.get_team(combatant)})

    def move_combatant(self, combatant, new_coords: np.array):
        """
        Removes the combatant from the old coordinate and moves them to a new one
        :param combatant:
        :param new_coords:
        :return:
        """
        old_coords = self.get_combatant_position(combatant).get()
        for old_coord in old_coords:
            self.grid[old_coord[0], old_coord[1]].remove_combatant()
        new_coords = Coords(new_coords, combatant.size)
        new_coords_data = new_coords.get()
        assert self.size > np.amax(new_coords_data) and np.amin(new_coords_data) > -1, f"Invalid coord {new_coords_data}"
        for new_coord in new_coords_data:
            self.grid[new_coord[0], new_coord[1]].set_combatant(combatant)
        self.combatant_coordinate_cache[combatant] = new_coords
        logger.info(f"{combatant} moved to {new_coords_data[0]}", extra={"team": self.teams.get_team(combatant)})

    def set_combatant_coordinates(self, combatant, coords: np.array):
        coords = Coords(coords, combatant.size)
        def set_comb(square):
            square.set_combatant(combatant)
            return square
        vec_set_comb = np.vectorize(set_comb)
        self.grid[coords.get()[:, 0], coords.get()[:, 1]] = vec_set_comb(self.grid[coords.get()[:, 0], coords.get()[:, 1]])
        self.combatant_coordinate_cache[combatant] = coords

    def get_nearest(self, combatant, side=Side.ENEMY, dist_type=DistanceMetric.HOP):
        """
        Returns nearest enemy/ally to combatant by hop distance
        :param combatant:
        :param side: either Side.ENEMY or Side.ALLY
        :param dist_type: either DistanceMetric.HOP or DistanceMetric.CARTESIAN
        :return: the nearest enemy/ally and distance to them in hops or cartesian
        """
        team_func = self.teams.are_enemies if side is Side.ENEMY else self.teams.are_allies
        dist_func = self.get_hop_distance_coords if dist_type is DistanceMetric.HOP else self.get_cartesian_distance_coords
        min_dist = sys.float_info.max
        nearest = None
        target_coord = None
        self_position = self.combatant_coordinate_cache[combatant]
        for potential_target, target_coord in self.combatant_coordinate_cache.items():
            dist = dist_func(self_position.get(), target_coord.get())
            if potential_target is not combatant and potential_target.is_alive() and team_func(potential_target,
                                                                                               combatant) and dist < min_dist:
                min_dist = dist
                nearest = potential_target
        return nearest, min_dist, target_coord


    def is_enemy_adjacent(self, combatant):
        nearest, dist, _ = self.get_nearest(combatant)
        if nearest and dist == 1:
            return True
        return False


    def is_ally_adjacent_to_target(self, combatant, target):
        """
        Used for pack tactics to determine if an ally that is not incapacitated is adjacent to a combatant
        :param combatant: the combatant to test if they benefit from pack tactics
        :param target: the target combatant
        :return: True if there's a non-incapacited ally adjacent
        """
        target_coords = self.combatant_coordinate_cache[target]
        adjacent_coords = self.get_adjacent_coords(target_coords)
        for adjacent_coord in adjacent_coords:
            potential_ally = self.grid[adjacent_coord[0], adjacent_coord[1]].combatant
            if potential_ally and potential_ally is not combatant and self.teams.are_allies(combatant, potential_ally) and not potential_ally.is_affected_by_any(Conditions.INCAPACITATED):
                return True
        return False

    def are_in_hop_range(self, combatant1, combatant2, distance):
        return self.get_hop_distance_combatants(combatant1, combatant2) <= distance

    @cached(cache={}, key=lambda self, coords1, coords2: hashkey(tuple(map(tuple, coords1)), tuple(map(tuple, coords2))))
    def get_hop_distance_coords(self, coords1: np.array, coords2: np.array):
        """
        Universal hop distance function. Accepts both characters or coordinates
        :param coords1:
        :param coords2:
        :return: distance between two sets of coords in number of hops, None if one of the subjects is dead
        """
        try:
            dist_mat = distance_matrix(coords1, coords2)
            min_dist_index = np.argmin(dist_mat)  # find the index closest distance between the two sets of points
            sub1_closest_coord = coords1[min_dist_index // dist_mat.shape[1], :]
            sub2_closest_coord = coords2[min_dist_index % dist_mat.shape[1], :]
            res = np.max(np.abs(sub1_closest_coord - sub2_closest_coord))
        except TypeError as e:
            res = None
        return res

    @cached(cache={}, key=lambda self, combatant1, combatant2: hashkey(combatant1.name, combatant2.name))
    def get_hop_distance_combatants(self, combatant1: ProtoCombatant, combatant2: ProtoCombatant):
        """
        Universal hop distance function. Accepts both characters or coordinates
        :param combatant1:
        :param combatant2:
        :return: distance between two combatants in number of hops, None if one of the combatants is dead
        """
        coords1 = self.combatant_coordinate_cache[combatant1].get()
        coords2 = self.combatant_coordinate_cache[combatant2].get()
        try:
            dist_mat = distance_matrix(coords1, coords2)
            min_dist_index = np.argmin(dist_mat)  # find the index closest distance between the two sets of points
            sub1_closest_coord = coords1[min_dist_index // dist_mat.shape[1], :]
            sub2_closest_coord = coords2[min_dist_index % dist_mat.shape[1], :]
            res = np.max(np.abs(sub1_closest_coord - sub2_closest_coord))
        except TypeError:
            res = None
        return res

    @cached(cache={}, key=lambda self, combatant1, combatant2: hashkey(combatant1.name, combatant2.name))
    def get_cartesian_distance_combatants(self, combatant1: ProtoCombatant, combatant2: ProtoCombatant):
        """
        Universal cartesian distance function. Accepts both characters or coordinates
        :param combatant1:
        :param comabtant2:
        :return: cartesian distance between two combatants, None if one of the combatants is dead
        """
        coords1 = self.combatant_coordinate_cache[combatant1].get()
        coords2 = self.combatant_coordinate_cache[combatant2].get()
        try:
            res = np.amin(distance_matrix(coords1, coords2))
        except TypeError:
            res = None
        return res

    @cached(cache={}, key=lambda self, coords1, coords2: hashkey(tuple(map(tuple, coords1)), tuple(map(tuple, coords2))))
    def get_cartesian_distance_coords(self, coords1: np.array, coords2: np.array):
        """
        Universal cartesian distance function. Accepts both characters or coordinates
        :param coords1:
        :param coords2:
        :return: cartesian distance between two sets of coords, None if one of the subjects is dead
        """
        try:
            res = np.amin(distance_matrix(coords1, coords2))
        except TypeError:
            res = None
        return res

    def inflate_coords(self, coords: Coords, inflate_to_dist):
        """
        A helper function which inflates the given Coords to a given size (they may already by inflated but may need further inflation
        due to the size of the other combatant).
        :param coords: target combatant coordinates
        :param inflate_to_dist: size of the other combatant
        :return: inflated set of coordinates (as x, y tuples)
        """
        offset = 0
        if inflate_to_dist > Size.MEDIUM.value:
            offset = inflate_to_dist

        inflated = set()
        for coord in coords.get():
            try:
                for x, y in [(x, y) for x in range(coord[0] - offset, coord[0] + 1) for y in range(coord[1] - offset, coord[1] + 1)]:
                    inflated.add((max(0, x), max(0, y)))
            except TypeError:
                print("FIXME")
        return inflated

    @toggled_cache(key=lambda self, coords, distances=[], inflate_to_dist=Size.MEDIUM.value, rng=1, combatant=None: hashkey(coords, tuple(distances), inflate_to_dist, rng, combatant))
    def get_free_coords_in_hop_range(self, coords: Coords, distances=None, inflate_to_dist=Size.MEDIUM.value, rng=1, combatant=None):
        """
        Returns free squares coordinates adjacent (up to the range distance) to a given coordinate that can be occupied
        by a combatant of 'inflate_to_dist' size.
        :param coords: target combatant coordinates
        :param distances: the distances to all squares (result of Dijkstra) to be able to recognize accessibility of coordinates
        :param inflate_to_dist: inflate for the sake of pathfinding BY larger combatants
        :param rng: maximum range of what is considered 'adjacent'
        :param combatant: optional combatant which is to be considered 'self' for the sake of is_empty_or_self
        :return: free adjacent coordinates as a set of tuples (x, y)
        """
        assert rng > 0
        inflated = self.inflate_coords(coords, inflate_to_dist)

        adjacent_coords = set()
        for coord in inflated:
            for x, y in [(coord[0] + i, coord[1] + j) for i in range(-rng, rng + 1) for j in range(-rng, rng + 1)]:
                if x < 0 or x >= self.size or y < 0 or y >= self.size:
                    continue
                square = self.grid[x, y]
                consider_accesibility = (distances[x * self.size + y] < sys.maxsize) if distances is not None else True
                if square.is_empty_or_self(combatant) and consider_accesibility:# and (x, y) not in inflated:
                    # have to use tuples since np.array is unhashable
                    adjacent_coords.add((x, y))
        return list(adjacent_coords)

    @toggled_cache(key=lambda self, coords, distances=[], inflate_to_dist=Size.MEDIUM.value, rng=1, combatant=None: hashkey(coords, tuple(distances), inflate_to_dist, rng, combatant))
    def get_free_coords_in_cartesian_range(self, coords: Coords, distances=(), inflate_to_dist=Size.MEDIUM.value, rng=1, combatant=None):
        """
        Returns free square coordinates that are at the most rng away from the coords as measured by cartesian distance that can be occupied
        by a combatant of 'inflate_to_dist' size. It's pretty much the same as get_free_coords_in_hop_range but it uses the rng as a
        bounding box to narrow down the search.
        :param coords: target combatant or destination coordinates
        :param distances: the distances to all squares (result of Dijkstra) to be able to recognize accessibility of coordinates
        :param inflate_to_dist: inflate for the sake of pathfinding BY larger combatants (as opposed to TO larger combatants)
        :param rng: maximum range
        :param combatant: optional combatant which is to be considered 'self' for the sake of is_empty_or_self
        :return: free adjacent coordinates as a set of tuples (x, y)
        """
        assert rng > 0
        # First inflate it by the size of the combatant looking for the path
        inflated = self.inflate_coords(coords, inflate_to_dist)

        coords_in_range = list()
        for coord in inflated:
            # the rng can be used as a bounding box for the search
            for x, y in [(coord[0] + i, coord[1] + j) for i in range(-rng, rng + 1) for j in range(-rng, rng + 1)]:
                if x < 0 or x >= self.size or y < 0 or y >= self.size or self.get_cartesian_distance_coords(coords.get(), np.array([[x, y]])) > rng:
                    continue
                square = self.grid[x, y]
                consider_accesibility = (distances[x * self.size + y] < sys.maxsize) if distances else True
                if square.is_empty_or_self(combatant) and consider_accesibility:# and (x, y) not in inflated:
                    # have to use tuples since np.array is unhashable
                    coords_in_range.append((x, y))
        return coords_in_range

    def get_all_accessible_coords(self, shortest_paths, combatant):
        """
        Returns all free and square coordinates accessible by a combatant given the shortest paths dict (output of Dijkstra)
        :param shortest_paths: the shortest paths to all squares (result of Dijkstra)
        :param combatant: the subject combatant
        :return: free and accessible coordinates as a set of tuples (x, y)
        """
        ret = list(shortest_paths.keys())
        ret.append(tuple(self.get_combatant_position(combatant).get()[0]))
        return ret


    def get_adjacent_coords(self, coords: Coords):
        """
        Returns accessible squares adjacent to a given coordinate
        :param coords: target combatant coordinates
        :return: adjacent coordinates as a set of tuples (x, y)
        """
        adjacent_coords = set()
        self_coords = coords.get()
        for coord in self_coords:
            for x, y in [(coord[0] + i, coord[1] + j) for i in (-1, 0, 1) for j in (-1, 0, 1) if i != 0 or j != 0]:
                if any((self_coords[:] == [x, y]).all(1)) or x < 0 or x >= self.size or y < 0 or y >= self.size:
                    continue
                square = self.grid[x, y]
                if square.terrain is not Terrain.IMPASSABLE_TERRAIN:
                    # have to use tuples since np.array is unhashable
                    adjacent_coords.add((x, y))
        return adjacent_coords

    def get_nearest_free_adjacent_coords(self, combatant, my_location: Coords, target_location: Coords, distances, rng=1):
        """
        Get nearest free adjacent coordinates accounting for the combatant's size. Potentially increasing what is considered adjacent to rng.
        :param combatant:
        :param my_location: combatant's location
        :param target_location: the target location
        :param distances: distances for all coords in the grid
        :param rng: the range of what is considered adjacent
        :return:
        """
        adjacent_coords = self.get_free_coords_in_hop_range(target_location, distances, my_location.size.value, rng,
                                                            combatant=combatant)
        if not adjacent_coords:
            return None
        adjacent_coords = [np.array([x]) for x in adjacent_coords]
        adjacent_coords.sort(key=lambda coord: self.get_cartesian_distance_coords(coord, my_location.get()))
        return adjacent_coords[0][0]


    def calc_dijkstra(self, combatant):
        """
        Calculates the Dijkstra algorithm for a given combatant. Currently used only for testing
        :param combatant: combatant who wants to move
        :return: :return: list of distances to all vertices, list of predecessors for every vertex and the threat adjacency matrix
        """
        my_location = self.get_combatant_position(combatant)
        mask = self.build_combatant_adjacency_mask(combatant)
        distances, shortest_paths = self.dijkstra(my_location.get()[0], mask=mask)
        return distances, shortest_paths


    def get_path_to_combatant(self, combatant, target, distances=None, shortest_paths=None, rng=1, consider_aoo=False):
        """
        Calculates a path to a target combatant
        :param combatant:Combatant who wants to move
        :param target:
        :param distances: potentially already pre-computed distances to all coords
        :param shortest_paths: potentially already pre-computed shortest paths to all coords
        :param rng: the range of what is considered adjacent
        :return: list of np.array increments to the target combatant
        """
        my_location = self.get_combatant_position(combatant)
        logger.debug(f"Origin {my_location.get()[0]}")
        enemy_location = self.get_combatant_position(target)
        logger.debug(f"Destination {enemy_location.get()[0]}")
        if not distances or not shortest_paths:
            mask = self.build_combatant_adjacency_mask(combatant, consider_aoo)
            distances, shortest_paths = self.dijkstra(my_location.get()[0], mask=mask)
        enemy_adjacent_location = self.get_nearest_free_adjacent_coords(combatant, my_location, enemy_location, distances, rng)
        if enemy_adjacent_location is None:
            return None
        reconstructed_path = reconstruct_from_shortest_path(shortest_paths, my_location.get()[0], enemy_adjacent_location)
        if reconstructed_path is None:
            return None
        if logger.root.level <= logging.INFO:
            self.printDijkstra(distances, my_location.get(), enemy_location.get(), reconstructed_path['tuples'])
        return convert_path_to_increments(reconstructed_path['numpy'])

    def get_path_to_coord(self, combatant, target_coord, distances=None, shortest_paths=None, consider_aoo=False):
        """
        Calculates a path to destination coordinates
        :param combatant:Combatant who wants to move
        :param target_coord:
        :param distances: potentially already pre-computed distances to all coords
        :param shortest_paths: potentially already pre-computed shortest paths to all coords
        :return: list of np.array increments to the target destination
        """
        my_location = self.get_combatant_position(combatant)
        logger.debug(f"Origin {my_location.get()[0]}")
        logger.debug(f"Destination {target_coord}")
        if not distances or not shortest_paths:
            mask = self.build_combatant_adjacency_mask(combatant, consider_aoo)
            distances, shortest_paths = self.dijkstra(my_location.get()[0], mask=mask)
        reconstructed_path = reconstruct_from_shortest_path(shortest_paths, my_location.get()[0], target_coord)
        if reconstructed_path is None:
            return None
        if logger.root.level <= logging.INFO:
            self.printDijkstra(distances, my_location.get(), np.array([target_coord]), reconstructed_path['tuples'])
        return convert_path_to_increments(reconstructed_path['numpy'])


    def get_effect_path_to_coord(self, current_coord, target_coord, shortest_paths):
        """
        Similar to get_path_to_coord but for moving effects such as a spiritual weapon or flaming sphere
        :param current_coord: current coordinate tuple
        :param target_coord: target coordinate tuple
        :param shortest_paths: potentially already pre-computed shortest paths to all coords
        :return: list of np.array increments to the target destination
        """
        return reconstruct_from_shortest_path(shortest_paths, current_coord, target_coord)


    def get_combatant_position(self, combatant):
        try:
            if not combatant.is_swallowed[0]:
                return self.combatant_coordinate_cache[combatant]
            else:
                return self.combatant_coordinate_cache[combatant.is_swallowed[1]]
        except KeyError as e:
            # logger.error(f"Combatant doesn't exist {e}")
            return None



    def remove_combatant(self, combatant):
        """
        Removes a combatant from the grid
        :param combatant:
        :return:
        """
        try:
            old_coords = self.combatant_coordinate_cache[combatant].get()
        except KeyError:
            return  # already removed
        for coord in old_coords:
            self.grid[coord[0], coord[1]].remove_combatant()
        del self.combatant_coordinate_cache[combatant]

    def remove_combatant_if_dead(self, combatant):
        """
        Removes a dead combatant from the grid
        :param combatant:
        :return: new target which can be either None in case both forms are dead or the combatant's original form
        """
        if combatant.get_original_form() is combatant and not combatant.is_alive():
            logger.info(f"{combatant} died")
            combatant.on_die()
            self.remove_combatant(combatant)
            return None
        else:
            if not combatant.get_original_form().is_alive():
                combatant.get_original_form().on_die()
                logger.info(f"{combatant.get_original_form()} died")
                self.remove_combatant(combatant.get_original_form())
                return None
            else:
                return combatant.get_original_form()


    def reset(self, combatant_initial_positions):
        """
        Resets all combatants to their initial positions
        :param combatant_initial_positions: the initial positions as a dict
        """
        logger.debug("Resetting the battle map")
        for row in self.grid:
            for square in row:
                logger.debug("Resetting square")
                square.remove_combatant()
        for combatant, coord in combatant_initial_positions.items():
            self.set_combatant_coordinates(combatant, copy.deepcopy(coord))

    def get_harmful_bounding_box(self, caster, inflation):
        """
        A helper function which constructs a bounding box which contains all enemies inflated by the inflation size
        :param caster: the caster (since the BB is determined by enemies)
        :param inflation: radius or side length of the harmful AoE effect
        :return: bounding box in [[x1, y1], [x2, y2]] where x1,y1 are top right, x2,y2 are bottom left
        """
        bb = np.array([[self.size, self.size], [0, 0]])  # top right, bottom left
        for combatant, coords in self.combatant_coordinate_cache.items():
            if self.teams.are_enemies(caster, combatant):
                coords = coords.get()
                bb[0] = np.minimum(bb[0], coords.min(axis=0))
                bb[1] = np.maximum(bb[1], coords.max(axis=0))
        # inflate the BB
        bb[0] = np.maximum(bb[0] - inflation, np.array([0, 0]))
        bb[1] = np.minimum(bb[1] + inflation, np.array([self.size - 1, self.size - 1]))
        return bb

    @cached(cache={}, key=lambda self, caster, spell_range, radius, factory: hashkey(caster.name, spell_range, radius, str(factory)))
    def find_best_placement_harmful_circular(self, caster, spell_range, radius, factory):
        """
        Finds the best placement of a spherical harmful AoE effect
        :param caster: the caster
        :param spell_range: range of the spell/ability
        :param radius: radius of the harmful AoE effect
        :param factory: factory of the harmful effect, is used to determine the threat score
        :return: best coordinate,achieved score and set of affected combatants
        """
        # Find a BB for all the enemy combatants inflated by the range and then iterate over all squares finding one with the best hit score
        bb = self.get_harmful_bounding_box(caster, radius)
        max_score = -sys.maxsize - 1
        best_placement = None
        swallower = caster.get_swallower()
        if swallower:
            caster_coords = self.combatant_coordinate_cache[swallower].get()
        else:
            caster_coords = self.combatant_coordinate_cache[caster].get()
        for x, y in [(x, y) for x in range(bb[0][0], bb[1][0]) for y in range(bb[0][1], bb[1][1])]:
            curr_coord = np.array([[x, y]])
            if self.get_cartesian_distance_coords(caster_coords, curr_coord) > spell_range or any((caster_coords[:] == curr_coord).all(1)):
                continue  # Skip those outside of spell range and those taken up by the caster
            threat_score = factory.create(curr_coord[0]).calculate_threat()
            if threat_score > max_score:
                max_score = threat_score
                best_placement = curr_coord
        # logger.info(f"HARMFUL EFFECT PLACEMENT {best_placement} with score {max_score}")
        return best_placement, max_score

    def find_best_placement_harmful_square(self, caster, spell_range, length):
        """
        Finds the best placement of a square harmful AoE effect
        :param caster: the caster
        :param spell_range: range of the spell/ability
        :param length: side length of the box
        :return: best coordinate,achieved score and set of affected combatants
        """
        # Find a BB for all the enemy combatants inflated by the range and then iterate over all squares finding one with the best hit score
        bb = self.get_harmful_bounding_box(caster, length)
        max_score = -sys.maxsize - 1
        best_placement = None
        best_affected = None
        caster_coords = self.combatant_coordinate_cache[caster].get()
        for x, y in [(x, y) for x in range(bb[0][0], bb[1][0]) for y in range(bb[0][1], bb[1][1])]:
            curr_coord = np.array([[x, y]])
            affected = []
            if self.get_cartesian_distance_coords(caster_coords, curr_coord) > spell_range or any((caster_coords[:] == curr_coord).all(1)):
                continue  # Skip those outside of spell range and those taken up by the caster
            score = 0
            for combatant, coords in self.combatant_coordinate_cache.items():
                if any((coords.get()[:] >= curr_coord).all(1)) and any((coords.get()[:] < curr_coord + length).all(1)):
                    score += 1 if self.teams.are_enemies(caster, combatant) and combatant.is_alive() else -4
                    affected.append(combatant)
            if score > max_score:
                max_score = score
                best_placement = curr_coord
                best_affected = affected
        return best_placement, max_score, best_affected

    def get_coords_affected_by_square_aoe(self, origin, length):
        """
        Gets coordinates of grid squares affected by a square effect originating at bottom left corner of a square at origin coordinates.
        :param origin: bottom left coordinate of the square
        :param length: length of the square's side
        :return: affected coordinates as a np.array of nx2 where n is the number of coordinates returned
        """
        coords = []
        try:
            for x, y in [(origin[0] + i, origin[1] + j) for i in range(0, length) for j in range(0, length)]:
                if x < 0 or x >= self.size or y < 0 or y >= self.size:
                    continue
                coords.append(np.array([x, y]))
        except TypeError:
            print("FIXME")
        return np.stack([c for c in coords])

    def get_combatants_affected_by_aoe(self, caster, target_template, ability_type, origin, angle=0):
        """
        Gets combatants affected by an AoE effect
        :param caster: the caster of the AoE
        :param target_template: RADIUS_X, CONE_Y, BOX_Z
        :param ability_type: SpellStats.Type.HARMFUL or SpellStats.Type.BUFF
        :param origin: origin of the AoE
        :param angle: yaw angle of the cone, marks the center line through the cone, north clock-wise oriented
        :return: affected combatants
        """
        # TODO potentially check for protective abilities
        affected_combatants = []
        match target_template:
            case SpellStats.Target.RADIUS_10 | SpellStats.Target.RADIUS_20 | SpellStats.Target.RADIUS_30:
                for potential_target, combatant_coords in self.combatant_coordinate_cache.items():
                    if ability_type is SpellStats.Type.HARMFUL:
                        if self.get_cartesian_distance_coords(combatant_coords.get(), np.array([origin])) <= SpellStats.TRANSLATE_RADIUS[
                                target_template]:
                            affected_combatants.append(potential_target)
                    elif ability_type is SpellStats.Type.BUFF:
                        # generally you can opt only to target your allies with buff spells
                        if self.get_cartesian_distance_coords(combatant_coords.get(), np.array([origin])) <= SpellStats.TRANSLATE_RADIUS[
                                target_template] and self.teams.are_allies(caster, potential_target):
                            affected_combatants.append(potential_target)
            case SpellStats.Target.CONE_15 | SpellStats.Target.CONE_30 | SpellStats.Target.CONE_60 | SpellStats.Target.CONE_90:
                # TODO make this work with larger combatants
                # Cone spells and abilities are generally only harmful
                angle_deg = angle
                radius = SpellStats.TRANSLATE_CONE[target_template]
                origin = self.combatant_coordinate_cache[caster]
                affected_coords = get_affected_by_cone(origin, angle_deg, radius, self.size)
                affected_combatants = [pt for (pt, cc) in self.combatant_coordinate_cache.items() if (cc[0], cc[1]) in affected_coords]

            case SpellStats.Target.BOX_5 | SpellStats.Target.BOX_20:
                affected_coords = self.get_coords_affected_by_square_aoe(origin, SpellStats.TRANSLATE_BOX[target_template])
                for potential_target, combatant_coords in self.combatant_coordinate_cache.items():
                    if self.get_cartesian_distance_coords(combatant_coords.get(), affected_coords) == 0:
                        affected_combatants.append(potential_target)
            case _:
                logger.error("Unrecognized ability target type")
        return affected_combatants


    def get_enemies_within_radius_sorted_by_distance(self, combatant, radius):
        enemies = [e for e in self.teams.get_enemies(combatant) if e.is_alive() and self.get_cartesian_distance_combatants(e, combatant) <= radius]
        distances = [self.get_cartesian_distance_combatants(e, combatant) for e in enemies]
        enemies.sort(key=lambda e: self.get_cartesian_distance_combatants(e, combatant))
        distances.sort()
        return enemies, distances

    def get_visibility(self, observer: Coords, target: Coords):
        """
        The visibility is calculated terms of how much of the field of view of the target is blocked by obstacles. I find the leftmost and
        the rightmost vertex of coord2. I then stretch a bounding box between the observer coordinates and the farthest point of the
        observer. Inside this bounding box I find all obstacles (plus maybe other combatants) and store them as objects. I then find the
        leftmost and rightmost vertices for all obstacles. Each pair of vertices together with the observer's mid point define a pair of
        vectors. Then I go obstacle vector pair by vector pair and classify their field of view angles. I need to identify six different
        cases:
        A) The obstacle is too far to the right, the target is fully visible
        B) The right side of the target is partially hidden behind the obstacle
        C) The obstacle is somewhere in the center of the target but parts of the target can still be seen on left and right
        D) The left side of the target is partially hidden behind the obstacle
        E) The obstacle is too far to the left, the target is fully visible
        F) The target is fully blocked by the obstacle
        From this I calculate the overall visible percentage.

        :param observer:
        :param target:
        :return: the degree of Visibility between the two coordinates
        """
        bottom_left, top_right = get_bounding_box(observer, target)
        objects = []
        for obstacle in self.obstacles:
            obstacle_tr = (obstacle.coord[0] + obstacle.radius, obstacle.coord[1] + obstacle.radius)
            obstacle_bl = (obstacle.coord[0] - obstacle.radius, obstacle.coord[1] - obstacle.radius)
            if obstacle_tr[0] < bottom_left[0] or obstacle_bl[0] > top_right[0] or obstacle_bl[1] > top_right[1] or obstacle_tr[1] < bottom_left[1]:
                continue
            objects.append(obstacle)
        objects.append(target)

        vec_to_object = [(vec, o) for o in objects for vec in find_fov_vectors(observer, o)]
        central_vector = target.get_center() - observer.get_center()
        vec_to_object.sort(key=lambda x: angle_between_vectors(central_vector, x[0]) * np.sign(np.cross(x[0], central_vector)), reverse=True)

        entered_target_fov = False
        opened = set()
        start_of_hidden_fov = None
        hidden_fov = 0
        for vo in vec_to_object:
            if vo[1] is not target:
                if vo[1] not in opened:
                    if not opened:
                        start_of_hidden_fov = vo[0]
                    opened.add(vo[1])
                else:
                    opened.remove(vo[1])
                    if not opened and entered_target_fov:
                        hidden_fov += angle_between_vectors(start_of_hidden_fov, vo[0])
                        # start_of_hidden_fov = None
            elif entered_target_fov:
                if opened:
                    hidden_fov += angle_between_vectors(start_of_hidden_fov, vo[0])
                break
            else:
                entered_target_fov = True
                start_of_hidden_fov = vo[0]  # Override the potential start of hidden FoV, we don't care about area outside the target FoV

        target_vectors = find_fov_vectors(observer, target)
        target_fov = angle_between_vectors(target_vectors[0], target_vectors[1])
        visible_fov = target_fov - hidden_fov
        visible_percentage = int(visible_fov / (target_fov * 0.01))

        match visible_percentage:
            case pct if 50 < pct:
                return Visibility.FULL
            case pct if 25 < pct <= 50:
                return Visibility.HALF_COVER
            case pct if 0 < pct <= 25:
                return Visibility.THREE_QUARTERS_COVER
            case _:
                return Visibility.NONE

    def get_visibility_dict(self, combatant, coords: np.array):
        """
        Calculates the visibility for all enemies of a given combatant given a theoretical root coord to which the combatant is to be moved.
        :param combatant:
        :param coords: theoretical root coordinate for combatant
        :return: dict mapping enemy -> Visibility
        """
        combatant_coords = Coords(coords, combatant.size)
        ret = {e: self.get_visibility(combatant_coords, self.get_combatant_position(e)) for e in self.get_combatants(combatant)}
        ret[combatant] = Visibility.FULL
        return ret

    def calc_visibility_dict_for_all_coords(self, combatant, shortest_paths):
        """
        Calculates and caches the visibility dict for all coords accessible to a combatant.
        :param combatant:
        :param shortest_paths: the shortest paths to all squares (result of Dijkstra)
        :return: None
        """
        current_position = self.get_combatant_position(combatant).get()[0]
        self.visibility_dict_for_all_coords = {coord: self.get_visibility_dict(combatant, np.array(coord)) for coord in shortest_paths.keys()}
        self.visibility_dict_for_all_coords[tuple(current_position)] = self.get_visibility_dict(combatant, current_position)

    def get_adjacent_enemies(self, combatant):
        return [e for e in self.teams.get_enemies(combatant) if e.is_alive() and self.get_hop_distance_combatants(e, combatant) == 1]

    def get_enemies_within_radius(self, combatant, radius):
        return [e for e in self.teams.get_enemies(combatant) if e.is_alive() and self.get_hop_distance_combatants(e, combatant) <= radius]

    def get_allies_within_radius(self, combatant, radius):
        return [a for a in self.teams.get_allies(combatant) if a.is_alive() and self.get_hop_distance_combatants(a, combatant) <= radius]

    def get_enemies(self, combatant):
        return [e for e in self.teams.get_enemies(combatant) if e.is_alive()]

    def get_combatants(self, combatant):
        return [c for c in self.combatant_coordinate_cache.keys() if c.is_alive() and c is not combatant]

    def get_allies(self, combatant):
        return [a for a in self.teams.get_allies(combatant) if a.is_alive()]

    def get_enemies_within_hop_distance(self, combatant, distance):
        return [e for e in self.teams.get_enemies(combatant) if e.is_alive() and self.get_hop_distance_combatants(e, combatant) <= distance]

    def get_enemies_without_hop_distance(self, combatant, distance):
        return [e for e in self.teams.get_enemies(combatant) if e.is_alive() and self.get_hop_distance_combatants(e, combatant) > distance]

    def get_enemies_within_their_movement_range(self, combatant):
        return [e for e in self.teams.get_enemies(combatant) if e.is_alive() and self.get_hop_distance_combatants(e, combatant) <= e.movement + 1]

    def is_difficult_terrain_at(self, coords: Coords):
        vec_is_difficult_terrain = np.vectorize(GridSquare.is_difficult_terrain)
        return np.any(vec_is_difficult_terrain(self.grid[coords.get()[:, 0], coords.get()[:, 1]]))

    def clear_caches(self):
        self.get_hop_distance_coords.cache_clear()
        self.get_hop_distance_combatants.cache_clear()
        self.get_cartesian_distance_combatants.cache_clear()
        self.get_cartesian_distance_coords.cache_clear()

        self.get_free_coords_in_cartesian_range.cache_clear()
        self.get_free_coords_in_hop_range.cache_clear()
        self.find_best_placement_harmful_circular.cache_clear()

