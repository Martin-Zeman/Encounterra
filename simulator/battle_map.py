import numpy as np
import math
import sys
import logging
from simulator.spells.spell import SpellStats
from simulator.combatant import Combatant
from multipledispatch import dispatch
from simulator.misc import Conditions
from simulator.action_factory import Passive
from simulator.geometry import get_affected_by_cone, get_cartesian_distance, get_square_center
from simulator.misc import Side, DistanceMetric
from contextlib import contextmanager
import time
from enum import Enum

logger = logging.getLogger(__name__)


def reconstruct_from_shortest_path(shortest_path, my_location, target_location):
    current_position = target_location
    # The square of the enemy itself is inaccessible, have to take the closest free adjacent one
    path = {'tuples': [], 'numpy': []}
    while not np.array_equal(current_position, my_location):
        path['numpy'].append(current_position)
        path['tuples'].append(tuple(current_position))
        # have to convert to tuple cause numpy array is non-hashable
        try:
            current_position = shortest_path[tuple(current_position)]
        except KeyError as e:
            # logger.error(e)  # TODO remove this once fixed
            return None
    else:
        path['numpy'].append(my_location)
        path['tuples'].append(tuple(my_location))
    path['numpy'].reverse()
    path['tuples'].reverse()
    return path


# def get_hop_distance(coord1, coord2):
#     return np.max(np.abs(coord1 - coord2))


def convert_path_to_increments(path):
    increments = []
    for i in range(len(path) - 1):
        increments.append(path[i + 1] - path[i])
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
    def __init__(self):
        self.combatant = None
        self.terrain = Terrain.NORMAL_TERRAIN
        self.is_opaque = False
        self.occupancy = Occupancy.FREE

    def set_combatant(self, combatant):
        assert (self.occupancy is Occupancy.FREE or self.combatant is combatant) and self.terrain is not Terrain.IMPASSABLE_TERRAIN
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


class Map:

    def __init__(self, size, teams):
        self.size = size
        self.teams = teams
        self.grid = [[GridSquare() for _ in range(size)] for _ in range(size)]
        self.terrain_encoding = np.zeros((size, size), dtype=int)
        self.base_adjacency_matrix = np.zeros((size, size))
        self.difficult_set = set()
        self.impassable_set = set()
        self.combatant_coordinate_cache = {}  # Maps combatant -> coordinate
        self.effect_tracker = None

    def __str__(self):
        string_repr = ""
        for y in range(self.size - 1, -1, -1):
            row_text = ""
            for x in range(self.size):
                square = self.grid[x][y]
                combatant = square.combatant
                if combatant:
                    row_text += self.teams.get_team_color_code(combatant) + str(combatant)[0] + str(combatant)[-1] + "\x1b[0m\t"
                elif square.terrain is Terrain.DIFFICULT_TERRAIN:
                    row_text += "\x1b[38;5;226m00\x1b[0m\t"
                elif square.terrain is Terrain.IMPASSABLE_TERRAIN:
                    row_text += "\x1b[38;5;196m--\x1b[0m\t"
                else:
                    row_text += "00\t"
            string_repr += row_text + "\n"
        return string_repr

    @contextmanager
    def as_if_combatant_position(self, combatant, coord):
        original_coord = self.combatant_coordinate_cache[combatant]
        self.move_combatant(combatant, coord)
        try:
            yield self
        finally:
            self.move_combatant(combatant, original_coord)

    @contextmanager
    def as_if_dist_from_combatant(self, combatant1, combatant2, dist, dist_type=DistanceMetric.HOP):
        orig_dist_func = self.get_hop_distance if dist_type is DistanceMetric.HOP else self.get_cartesian_distance
        def monkeypatch_dist(subject1, subject2):
            if subject1 is combatant1 and subject2 is combatant2:
                return dist
            else:
                return orig_dist_func(subject1, subject2)
        if dist_type is DistanceMetric.HOP:
            self.get_hop_distance = monkeypatch_dist
        else:
            self.get_cartesian_distance = monkeypatch_dist
        try:
            yield self
        finally:
            if dist_type is DistanceMetric.HOP:
                self.get_hop_distance = orig_dist_func
            else:
                self.get_cartesian_distance = orig_dist_func

    @contextmanager
    def as_if_dist_mod_from_combatant(self, combatant1, combatant2, dist):
        """
        Context manager which pretends that the distance betweent two comabatans is modified by dist. Dist > 0 means farther away. Dist < 0
        means closer.
        """
        orig_dist_hop_func = self.get_hop_distance
        orig_dist_cartesian_func = self.get_cartesian_distance

        def monkeypatch_hop_dist(subject1, subject2):
            if subject1 is combatant1 and subject2 is combatant2:
                return max(1, orig_dist_hop_func(subject1, subject2) + dist)
            else:
                return orig_dist_hop_func(subject1, subject2)
        def monkeypatch_cartesian_dist(subject1, subject2):
            if subject1 is combatant1 and subject2 is combatant2:
                return max(1.0, orig_dist_cartesian_func(subject1, subject2) + dist)
            else:
                return orig_dist_cartesian_func(subject1, subject2)

        self.get_hop_distance = monkeypatch_hop_dist
        self.get_cartesian_distance = monkeypatch_cartesian_dist
        try:
            yield self
        finally:
            self.get_hop_distance = orig_dist_hop_func
            self.get_cartesian_distance = orig_dist_cartesian_func

    def set_effect_tracker(self, effect_tracker):
        self.effect_tracker = effect_tracker

    def place_circular_element(self, coords, terrain_type, diameter=1):
        N = self.size
        if diameter == 1:
            x = max(0, min(coords[0], N - 1))
            y = max(0, min(coords[1], N - 1))
            if terrain_type == Terrain.IMPASSABLE_TERRAIN:
                self.grid[x][y].terrain = Terrain.IMPASSABLE_TERRAIN
                self.terrain_encoding[x][y] = Terrain.IMPASSABLE_TERRAIN.value
                self.impassable_set.add((coords[0], coords[1]))
            elif terrain_type == Terrain.DIFFICULT_TERRAIN:
                self.grid[x][y].terrain = Terrain.DIFFICULT_TERRAIN
                self.terrain_encoding[x][y] = Terrain.DIFFICULT_TERRAIN.value
                self.difficult_set.add((coords[0], coords[1]))
        elif diameter > 1:
            for x in range(-math.floor(diameter / 2), math.floor(diameter / 2) + 1):
                for y in range(-math.floor(diameter / 2), math.floor(diameter / 2) + 1):
                    try:
                        if terrain_type == Terrain.IMPASSABLE_TERRAIN:
                            self.grid[coords[0] + x][coords[1] + y].terrain = Terrain.IMPASSABLE_TERRAIN
                            self.terrain_encoding[coords[0] + x][coords[1] + y] = Terrain.IMPASSABLE_TERRAIN.value
                            self.impassable_set.add((coords[0] + x, coords[1] + y))
                        elif terrain_type == Terrain.DIFFICULT_TERRAIN:
                            self.grid[coords[0] + x][coords[1] + y].terrain = Terrain.DIFFICULT_TERRAIN
                            self.terrain_encoding[coords[0] + x][coords[1] + y] = Terrain.DIFFICULT_TERRAIN.value
                            self.difficult_set.add((coords[0] + x, coords[1] + y))
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
                adj[i, j, max((i - 1), 0), max((j - 1), 0)] = 1
                adj[i, j, max((i - 1), 0), j] = 1
                adj[i, j, max((i - 1), 0), min(j + 1, N - 1)] = 1

                adj[i, j, i, max((j - 1), 0)] = 1
                adj[i, j, i, j] = 1
                adj[i, j, i, min(j + 1, N - 1)] = 1

                adj[i, j, min(i + 1, N - 1), max((j - 1), 0)] = 1
                adj[i, j, min(i + 1, N - 1), j] = 1
                adj[i, j, min(i + 1, N - 1), min(j + 1, N - 1)] = 1

                # max is used to avoid negative slicing, and +2 is used because
                # slicing does not include last element.
        adj = adj.reshape(Nsq, Nsq)  # Back to node-to-node shape
        # Remove self-connections (optional)
        adj -= np.eye(Nsq, dtype=int)
        for coord in self.difficult_set:
            adj[:, coord[0] * N + coord[1]] *= 2
        for coord in self.impassable_set:
            adj[:, coord[0] * N + coord[1]] = 0
        self.base_adjacency_matrix = adj
        # print("---build_adjacency_matrix took %s seconds ---" % (time.time() - start_time))

    def build_combatant_adjacency_mask(self, combatant):
        """
        Builds a combatant-specific mask for the adjacency matrix. It models enemies as being impassable by 0.
        Allies are considered difficult terrain (potentially on top of already difficult terrain)
        :param combatant: for whom the mask is to be constructed
        :return: adjacency matrix mask
        """
        N = self.size
        # TODO consider preallocating this for all combatants and only resetting it to ones
        mask = np.ones((self.size ** 2, self.size ** 2), dtype=int)
        for curr_combatant, coord in self.combatant_coordinate_cache.items():
            if curr_combatant is not combatant and curr_combatant.is_alive():
                # TODO even allies are now impassable, try and figure out of a way to improve this
                mask[:, coord[0] * N + coord[1]] = 0  # if self.teams.are_enemies(curr_combatant, combatant) else 2
        return mask

    def printDijkstra(self, distances, my_location, enemy_location, reconstructed_path):
        """
        Prints the distances to all locations on the map from my_location and highlights the reconstructed path to enemy_location.
        It prints it as standard cartesian coordinate system.
        ^ y
        |
        |
        _________> x
        0
        :param distances: list of distances to all coords (flattened)
        :param my_location: coordinates of the source
        :param enemy_location: coordinates of the destination
        :param reconstructed_path: list of coordinates from my_location to enemy_location
        :return: void
        """
        my_coord = my_location[0] * self.size + my_location[1]
        enemy_coord = enemy_location[0] * self.size + enemy_location[1]
        for y in range(self.size - 1, -1, -1):
            row = ""
            for x in range(self.size):
                coord = x * self.size + y
                dist = str(distances[coord]) if distances[coord] < sys.maxsize else "-"
                if coord == my_coord:
                    row += "\x1b[38;5;39m%s\x1b[0m\t" % dist
                elif coord == enemy_coord:
                    row += "\x1b[38;5;196m%s\x1b[0m\t" % dist
                elif (x, y) in reconstructed_path:
                    row += "\u001b[36m%s\x1b[0m\t" % dist
                else:
                    row += "%s\t" % dist if (x, y) not in self.difficult_set else "\x1b[38;5;226m%s\x1b[0m\t" % dist
            logger.debug(row)

    def minDistance(self, dist, open_set):
        """
        Helper function for the Dijkstra algorithm. Finds the index (coodinate) of an unexplored vertices with the lowest distance
        :param dist: list of distances to vertices
        :param open_set: list of vertices, True = explored, False = unexplored
        :return: index to min distance unexplored vertex
        """
        Nsq = self.size ** 2
        min = sys.maxsize
        min_index = None

        for u in range(Nsq):
            if dist[u] < min and open_set[u] is False:
                min = dist[u]
                min_index = u
        return min_index

    def dijkstra(self, src, mask):
        """
        Implementation of the Dijkstra algorithm with a preference for the least zig-zaggy path
        :param src:
        :param mask:
        :return: list of distances to all vertices, list of predecessors for every vertex
        """
        src = np.array(src)
        N = self.size
        Nsq = self.size ** 2
        dist = [sys.maxsize] * Nsq
        dist[src[0] * self.size + src[1]] = 0
        open_set = [False] * Nsq
        adj = np.multiply(self.base_adjacency_matrix, mask)
        shortest_paths = {}

        for _ in range(Nsq):
            x = self.minDistance(dist, open_set)
            if x is None:
                # enemy-occupied squares are unreachable
                continue
            open_set[x] = True
            for y in range(Nsq):
                if adj[x][y] > 0 and open_set[y] is False:
                    coord_to = (y // N, y % N)
                    coord_to_np = np.array([coord_to[0], coord_to[1]])
                    coord_from = np.array([x // N, x % N])
                    if dist[y] > dist[x] + adj[x][y]:
                        dist[y] = dist[x] + adj[x][y]
                        shortest_paths[coord_to] = coord_from
                    elif dist[y] >= dist[x] + adj[x][y] and np.sum(np.abs(shortest_paths[coord_to] - coord_to_np)) > np.sum(
                            np.abs(coord_to_np - coord_from)):
                        # TODO this should also work with ==, try that
                        # prefer the path with the least coordinate diff, i.e. the less zig-zaggy path
                        shortest_paths[coord_to] = coord_from

        return dist, shortest_paths

    def move_combatant_by_increment(self, combatant, increment):
        """
        Removes the combatant from the old coordinate and moves them to a new one by a given increment
        :param combatant:
        :param increment:
        :return:
        """
        old_coord = self.combatant_coordinate_cache[combatant]
        self.grid[old_coord[0]][old_coord[1]].remove_combatant()
        new_coord = old_coord + increment
        self.grid[new_coord[0]][new_coord[1]].set_combatant(combatant)
        self.combatant_coordinate_cache[combatant] = new_coord
        logger.debug(f"{combatant} moved to {new_coord}", extra={"team": self.teams.get_team(combatant)})

    def move_combatant(self, combatant, new_coord):
        """
        Removes the combatant from the old coordinate and moves them to a new one
        :param combatant:
        :param new_coord:
        :return:
        """
        old_coord = self.combatant_coordinate_cache[combatant]
        self.grid[old_coord[0]][old_coord[1]].remove_combatant()
        self.grid[new_coord[0]][new_coord[1]].set_combatant(combatant)
        self.combatant_coordinate_cache[combatant] = new_coord
        logger.debug(f"{combatant} moved to {new_coord}", extra={"team": self.teams.get_team(combatant)})

    def get_aoo_eligible_combatants(self, combatant, increment):
        eligible_combatants = []
        for curr_combatant, pos in self.combatant_coordinate_cache.items():
            if curr_combatant is not combatant and curr_combatant.is_alive() and self.teams.are_enemies(curr_combatant, combatant):
                pre_increment_dist = self.get_hop_distance(combatant, curr_combatant)
                post_increment_dist = self.get_hop_distance(self.combatant_coordinate_cache[combatant] + increment, pos)
                if pre_increment_dist == curr_combatant.max_melee_range and post_increment_dist > curr_combatant.max_melee_range and curr_combatant.has_reaction:
                    eligible_combatants.append(curr_combatant)
        return eligible_combatants

    def get_pam_eligible_combatants(self, combatant, increment):
        eligible_combatants = []
        for curr_combatant, pos in self.combatant_coordinate_cache.items():
            if curr_combatant is not combatant and self.teams.are_enemies(curr_combatant, combatant):
                try:
                    pre_increment_dist = self.get_hop_distance(combatant, curr_combatant)
                    post_increment_dist = self.get_hop_distance(self.combatant_coordinate_cache[combatant] + increment, pos)
                except KeyError:
                    continue
                if curr_combatant.has_passive(
                        Passive.POLEARM_MASTER) and pre_increment_dist > curr_combatant.max_melee_range and post_increment_dist == curr_combatant.max_melee_range and curr_combatant.has_reaction:
                    eligible_combatants.append(curr_combatant)
        return eligible_combatants

    def is_empty(self, coord):
        try:
            empty = self.grid[coord[0]][coord[1]].is_empty()
        except IndexError:
            return False
        return empty

    def is_valid_coord(self, coord):
        return False if (coord.any() < 0 or coord.any() > self.size - 1) else True

    def set_combatant_coordinates(self, combatant, coord):
        # TODO: redo this as np.array
        self.grid[coord[0]][coord[1]].set_combatant(combatant)
        self.combatant_coordinate_cache[combatant] = coord

    def move_combatant(self, combatant, coord):
        old_coord = self.combatant_coordinate_cache[combatant]
        self.grid[old_coord[0]][old_coord[1]].remove_combatant()
        self.set_combatant_coordinates(combatant, coord)

    def get_nearest(self, combatant, side=Side.ENEMY, dist_type=DistanceMetric.HOP):
        """
        Returns nearest enemy/ally to combatant by hop distance
        :param combatant:
        :param side: either Side.ENEMY or Side.ALLY
        :param dist_type: either DistanceMetric.HOP or DistanceMetric.CARTESIAN
        :return: the nearest enemy/ally and distance to them in hops or cartesian
        """
        team_func = self.teams.are_enemies if side is Side.ENEMY else self.teams.are_allies
        dist_func = self.get_hop_distance if dist_type is DistanceMetric.HOP else self.get_cartesian_distance
        min_dist = sys.float_info.max
        nearest = None
        self_position = self.combatant_coordinate_cache[combatant]
        nearest_coord = None
        for potential_target, target_coord in self.combatant_coordinate_cache.items():
            dist = dist_func(self_position, target_coord)
            if potential_target is not combatant and potential_target.is_alive() and team_func(potential_target,
                                                                                               combatant) and dist < min_dist:
                min_dist = dist
                nearest = potential_target
                nearest_coord = target_coord
        return nearest, min_dist, target_coord

    def is_enemy_adjacent(self, character):
        self_coords = self.combatant_coordinate_cache[character]
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if self_coords[0] + dx < 0 or self_coords[0] + dx >= self.size or self_coords[1] + dy < 0 or self_coords[
                    1] + dy >= self.size:
                    continue
                cmbt = self.grid[self_coords[0] + dx][self_coords[1] + dy].combatant
                if cmbt and self.teams.are_enemies(character, cmbt):
                    return True
        return False

    def is_ally_adjacent(self, character, target):
        """
        Used for pack tactics to determine if an ally that is not incapacitated is adjacent to my target
        :param target: the target combatant
        :param coord:
        :return:
        """
        target_coord = self.combatant_coordinate_cache[target]
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if target_coord[0] + dx < 0 or target_coord[0] + dx >= self.size or target_coord[1] + dy < 0 or target_coord[1] + dy >= self.size:
                    continue
                cmbt = self.grid[target_coord[0] + dx][target_coord[1] + dy].combatant
                if cmbt and cmbt is not character and self.teams.are_allies(character, cmbt) and not cmbt.is_affected_by_any(
                        Conditions.INCAPACITATED):
                    return True
        return False

    def are_in_range(self, combatant1, combatant2, distance):
        combatant1_position = np.array(self.combatant_coordinate_cache[combatant1])
        combatant2_position = np.array(self.combatant_coordinate_cache[combatant2])
        return np.max(np.abs(combatant1_position - combatant2_position)) <= distance

    def get_hop_distance(self, subject1, subject2):
        """
        Universal hop distance function. Accepts both characters or coordinates
        :param subject1: either a character or a numpy array
        :param subject2: either a character or a numpy array
        :return: distance between subjects in number of hops, None if one of the subjects is dead
        """
        subject1 = self.combatant_coordinate_cache[subject1] if issubclass(type(subject1), Combatant) else subject1
        subject2 = self.combatant_coordinate_cache[subject2] if issubclass(type(subject2), Combatant) else subject2
        try:
            res = np.max(np.abs(subject1 - subject2))
        except TypeError as e:
            res = None
        return res

    def get_cartesian_distance(self, subject1, subject2):
        """
        Universal cartesian distance function. Accepts both characters or coordinates
        :param subject1: either a character or a numpy array
        :param subject2: either a character or a numpy array
        :return: cartesian distance between subjects, None if one of the subjects is dead
        """
        try:
            subject1 = self.combatant_coordinate_cache[subject1] if issubclass(type(subject1), Combatant) else subject1
            subject2 = self.combatant_coordinate_cache[subject2] if issubclass(type(subject2), Combatant) else subject2
        except KeyError:
            return None
        try:
            res = get_cartesian_distance(subject1, subject2)
        except TypeError as e:
            res = None
        return res

    def get_adjacent_coords(self, coord):
        """
        Returns free and accessible squares adjacent to a given coordinate
        :param coord: target coordinate
        :return: free adjacent coordinates as a set of tuples (x, y)
        """
        adjacent_coords = set()
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if coord[0] + dx < 0 or coord[0] + dx >= self.size or coord[1] + dy < 0 or coord[1] + dy >= self.size:
                    continue
                square = self.grid[coord[0] + dx][coord[1] + dy]
                if square.occupancy is Occupancy.FREE and square.terrain is not Terrain.IMPASSABLE_TERRAIN:
                    # have to use tuples since np.array is unhashable
                    adjacent_coords.add((coord[0] + dx, coord[1] + dy))
        return adjacent_coords

    def get_nearest_adjacent_coord(self, my_location, target_location):
        adjacent_coords = self.get_adjacent_coords(target_location)
        if not adjacent_coords:
            return None
        adjacent_coords = [np.array(x) for x in adjacent_coords]
        adjacent_coords.sort(key=lambda coord: self.get_hop_distance(coord, my_location))
        return adjacent_coords[0]

    @dispatch(Combatant, Combatant)
    def get_path_to(self, combatant, target_combatant):
        """
        Calculates a path to a target combatant
        :param combatant:Combatant who wants to move
        :param target_combatant:
        :return: list of np.array increments to the target combatant
        """
        my_location = self.get_combatant_position(combatant)
        logger.debug(f"Origin {my_location}")
        enemy_location = self.get_combatant_position(target_combatant)
        logger.debug(f"Destination {enemy_location}")
        mask = self.build_combatant_adjacency_mask(combatant)
        distances, shortest_paths = self.dijkstra(my_location, mask)
        enemy_adjacent_location = self.get_nearest_adjacent_coord(my_location, enemy_location)
        if enemy_adjacent_location is None:
            return None
        reconstructed_path = reconstruct_from_shortest_path(shortest_paths, my_location, enemy_adjacent_location)
        if reconstructed_path is None:
            return None
        self.printDijkstra(distances, my_location, enemy_location, reconstructed_path['tuples'])
        return convert_path_to_increments(reconstructed_path['numpy'])

    @dispatch(Combatant, np.ndarray)
    def get_path_to(self, combatant, target_coord):
        """
        Calculates a path to destination coordinates
        :param combatant:Combatant who wants to move
        :param target_coord:
        :return: list of np.array increments to the target destination
        """
        # TODO: consider making a variant which doesn't provoke AOO
        my_location = self.get_combatant_position(combatant)
        logger.debug(f"Origin {my_location}")
        logger.debug(f"Destination {target_coord}")
        mask = self.build_combatant_adjacency_mask(combatant)
        distances, shortest_paths = self.dijkstra(my_location, mask)
        reconstructed_path = reconstruct_from_shortest_path(shortest_paths, my_location, target_coord)
        if reconstructed_path is None:
            return None
        self.printDijkstra(distances, my_location, target_coord, reconstructed_path['tuples'])
        return convert_path_to_increments(reconstructed_path['numpy'])

    def get_combatant_position(self, combatant):
        try:
            return self.combatant_coordinate_cache[combatant]
        except KeyError as e:
            logger.error(e)
            return None

    def get_free_coords_away_from_enemies(self, character, distance, dist_type=DistanceMetric.HOP):
        """
        Returns a list of coordinates that are at a certain distance from character. Sorted by distance to the nearest enemy
        :param character: combatant who wants to get away
        :param distance: how far the combatant can go
        :return: sorted by the minimum distance to any enemy in ascending order
        """
        elligible_coords = []
        self_coord = self.combatant_coordinate_cache[character]
        dist_func = self.get_hop_distance if dist_type is DistanceMetric.HOP else self.get_cartesian_distance
        # optimization - narrowing search down to a bounding box
        for i in range(-distance, distance + 1):
            for j in range(-distance, distance + 1):
                curr_coord = self_coord + np.array([i, j])
                if curr_coord[0] in range(0, self.size) and curr_coord[1] in range(0, self.size):
                    # TODO modify and use is_empty
                    square = self.grid[curr_coord[0]][curr_coord[1]]
                    if square.is_empty() and dist_func(curr_coord, self_coord) == distance:
                        elligible_coords.append(curr_coord)

        def by_distance_to_nearest_enemy(coord):
            min_dist = sys.maxsize
            min_dist_coord = coord
            for combatant, cmbt_coord in self.combatant_coordinate_cache.items():
                if combatant.is_alive() and self.teams.are_enemies(character, combatant):
                    dist = self.get_hop_distance(coord, cmbt_coord)
                    min_dist = min(dist, min_dist)
            return min_dist

        elligible_coords.sort(key=by_distance_to_nearest_enemy, reverse=True)
        return elligible_coords

    def get_free_coords_at_distance(self, target_combatant, combatant, min_dist, max_dist=sys.maxsize):
        """
        Returns a list of coordinates that are unoccupied and at a given distance from a target, sorted by ascending proximity to the target
        combatant
        :param target_combatant: target to which the distance is measured
        :param combatant: sorted by ascending proximity to this combatant
        :param min_dist: minimum desired distance
        :param max_dist: maximum desired distance
        :return: list of numpy.array coordinates
        """
        assert min_dist > 0
        # mask_self = self.build_combatant_adjacency_mask(combatant)
        # distances_self, _ = self.dijkstra(self.combatant_coordinate_cache[combatant], mask_self)
        mask_target = self.build_combatant_adjacency_mask(target_combatant)
        distances_from_target, _ = self.dijkstra(self.combatant_coordinate_cache[target_combatant], mask_target)
        free_positions = []
        # target_coords = self.combatant_coordinate_cache[target_combatant]


        coords = []
        for i, dist in enumerate(distances_from_target):
            curr_coord = np.array([i // self.size, i % self.size])
            is_empty = self.grid[curr_coord[0]][curr_coord[1]].is_empty()
            if is_empty and min_dist <= dist <= max_dist:
                coords.append(curr_coord)
        # for x in range(-distance, distance + 1):
        #     for y in range(-distance, distance + 1):
        #         if (target_coords[0] + x) < 0 or (target_coords[1] + y) < 0 or (target_coords[0] + x) >= self.size or (
        #                 target_coords[1] + y) >= self.size:
        #             continue
        #         curr_coord = target_coords + np.array([x, y])
        #         is_empty = self.grid[curr_coord[0]][curr_coord[1]].is_empty()
        #         hop_distance = self.get_hop_distance(target_coords, curr_coord)
        #         if is_empty and min_dist <= hop_distance <= max_dist:
        #             free_positions.append(np.array([target_coords[0] + x, target_coords[1] + y]))

        # combatant_coord = self.combatant_coordinate_cache[combatant]
        # sort them by cartesian distance to get the most direct one
        # coords.sort(key=lambda coord: np.linalg.norm(coord - combatant_coord))
        coords.sort(key=lambda coord: distances_from_target[coord[0] * self.size + coord[1]])
        for coord in coords:
            assert self.is_valid_coord(coord), "INVALID COORD"
        return coords

    def remove_combatant(self, combatant):
        """
        Removes a dead combatant from the grid
        :param combatant:
        :return:
        """
        logger.debug(f"{combatant} died")
        try:
            old_coord = self.combatant_coordinate_cache[combatant]
        except KeyError:
            return  # already removed
        self.grid[old_coord[0]][old_coord[1]].remove_combatant()
        del self.combatant_coordinate_cache[combatant]

    def clear(self):
        for row in self.grid:
            for square in row:
                square.remove_combatant()
                square.reset_terrain()
        for coord in self.combatant_coordinate_cache.values():
            coord.fill(0)
        self.impassable_set.clear()
        self.difficult_set.clear()
        self.terrain_encoding.fill(Terrain.NORMAL_TERRAIN.value)


    def reset(self, combatant_initial_positions):
        for row in self.grid:
            for square in row:
                square.remove_combatant()
        for combatant, coord in combatant_initial_positions.items():
            self.set_combatant_coordinates(combatant, coord)

    def find_best_placement_harmful_circular(self, caster, spell_range, radius):
        """
        Finds the best placement of a spherical harmful AoE effect
        :param caster:
        :param spell_range:
        :param radius:
        :return: coordinate and achieved score
        """
        # or find a BB for all the enemy combatants inflated by the range and then iterate over all squares finding one with the best hit score
        bb = np.array([[self.size, self.size], [0, 0]])  # top left, bottom right
        for combatant, coord in self.combatant_coordinate_cache.items():
            if self.teams.are_enemies(caster, combatant):
                bb[0] = np.minimum(bb[0], coord)
                bb[1] = np.maximum(bb[1], coord)
        # inflate the BB
        bb[0] = np.maximum(bb[0] - radius, np.array([0, 0]))
        bb[1] = np.minimum(bb[1] + radius, np.array([self.size - 1, self.size - 1]))
        max_score = -sys.maxsize - 1
        best_placement = None
        best_affected = None
        caster_coord = self.combatant_coordinate_cache[caster]
        for i in range(bb[0][0], bb[1][0]):
            for j in range(bb[0][1], bb[1][1]):
                curr_coord = np.array([i, j])
                affected = []
                if get_cartesian_distance(get_square_center(caster_coord), curr_coord) <= spell_range and caster_coord is not curr_coord:
                    score = 0
                    for combatant, coord in self.combatant_coordinate_cache.items():
                        if get_cartesian_distance(get_square_center(coord), curr_coord) <= radius:
                            score += 1 if self.teams.are_enemies(caster, combatant) and combatant.is_alive() else -4
                            affected.append(combatant)
                    if score > max_score:
                        max_score = score
                        best_placement = curr_coord
                        best_affected = affected
        logger.debug(self)
        # logger.debug(f"HARMFUL EFFECT PLACEMENT {best_placement} with score {max_score}")
        return best_placement, max_score, best_affected

    def get_combatants_affected_by_aoe(self, caster, target_template, ability_type, origin, angle=0):
        # TODO potentially check for protective abilities
        affected_combatants = []
        match target_template:
            case SpellStats.Target.RADIUS_10 | SpellStats.Target.RADIUS_20 | SpellStats.Target.RADIUS_30:
                for potential_target, combatant_coord in self.combatant_coordinate_cache.items():
                    if ability_type is SpellStats.Type.HARMFUL:
                        if get_cartesian_distance(get_square_center(combatant_coord), origin) <= SpellStats.TRANSLATE_RADIUS[
                                target_template]:
                            affected_combatants.append(potential_target)
                    elif ability_type is SpellStats.Type.BUFF:
                        # generally you can opt only to target your allies with buff spells
                        if get_cartesian_distance(get_square_center(combatant_coord), origin) <= SpellStats.TRANSLATE_RADIUS[
                                target_template] and self.teams.are_allies(caster, potential_target):
                            affected_combatants.append(potential_target)
            case SpellStats.Target.CONE_15 | SpellStats.Target.CONE_30 | SpellStats.Target.CONE_60 | SpellStats.Target.CONE_90:
                # Cone spells and abilities are generally only harmful
                angle_deg = angle
                radius = SpellStats.TRANSLATE_CONE[target_template]
                origin = self.combatant_coordinate_cache[caster]
                affected_coords = get_affected_by_cone(origin, angle_deg, radius, self.size)
                affected_combatants = [pt for (pt, cc) in self.combatant_coordinate_cache.items() if (cc[0], cc[1]) in affected_coords]
            case _:
                logger.error("Unrecognized ability target type")
        return affected_combatants

    def get_enemies_within_radius_sorted_by_distance(self, combatant, radius):
        enemies = [e for e in self.teams.get_enemies(combatant) if e.is_alive() and self.get_cartesian_distance(e, combatant) <= radius]
        distances = [self.get_cartesian_distance(e, combatant) for e in enemies]
        enemies.sort(key=lambda e: self.get_cartesian_distance(e, combatant))
        distances.sort()
        return enemies, distances

    def get_adjacent_enemies(self, combatant):
        return [e for e in self.teams.get_enemies(combatant) if e.is_alive() and self.get_hop_distance(e, combatant) == 1]
    def get_enemies_within_radius(self, combatant, radius):
        return [e for e in self.teams.get_enemies(combatant) if e.is_alive() and self.get_cartesian_distance(e, combatant) <= radius]

    def get_allies_within_radius(self, combatant, radius):
        return [e for e in self.teams.get_allies(combatant) if e.is_alive() and self.get_cartesian_distance(e, combatant) <= radius]

    def get_enemies(self, combatant):
        return self.teams.get_enemies(combatant)

    def get_allies(self, combatant):
        return self.teams.get_allies(combatant)

    def get_enemies_within_hop_distance(self, combatant, distance):
        return [e for e in self.teams.get_enemies(combatant) if e.is_alive() and self.get_hop_distance(e, combatant) <= distance]

    def get_enemies_within_their_movement_range(self, combatant):
        return [e for e in self.teams.get_enemies(combatant) if e.is_alive() and self.get_hop_distance(e, combatant) <= e.movement + 1]
