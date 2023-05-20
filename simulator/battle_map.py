import copy
import numpy as np
import math
import sys
import logging
from simulator.combatant_coords import CombatantCoords
from simulator.spells.spell import SpellStats
from simulator.combatant import Combatant
from simulator.misc import Conditions, Size
from simulator.actions.action_factory import Passive
from simulator.geometry import get_affected_by_cone
from simulator.misc import Side, DistanceMetric
from contextlib import contextmanager
from scipy.spatial import distance_matrix
import heapq
from enum import Enum

logger = logging.getLogger("EncounTroll")

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
    while not np.array_equal(current_position, source[0]):
        path['numpy'].append(current_position)
        path['tuples'].append(tuple(current_position))
        # have to convert to tuple cause numpy array is non-hashable
        try:
            current_position = shortest_path[tuple(current_position)]
        except KeyError as e:
            # logger.error(e)  # TODO remove this once fixed
            return None
        except TypeError:
            print("FIXME")
    else:
        path['numpy'].append(source[0])
        path['tuples'].append(tuple(source[0]))
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

    def is_empty_or_self(self, combatant):
        return ((self.occupancy is Occupancy.FREE) or (self.combatant is combatant)) and self.terrain is not Terrain.IMPASSABLE_TERRAIN

    def is_difficult_terrain(self):
        return self.terrain is Terrain.DIFFICULT_TERRAIN

class Map:

    def __init__(self, size, teams):
        self.size = size
        self.teams = teams
        vGridSquare = np.vectorize(GridSquare)
        init_grid = np.arange(size**2).reshape((size, size))
        self.grid = np.empty((size, size), dtype=object)
        self.grid[:, :] = vGridSquare(init_grid)
        self.base_adjacency_matrix = np.zeros((size, size))
        self.difficult_set = set()
        self.impassable_set = set()
        self.combatant_coordinate_cache = dict()  # Maps combatant -> coordinate
        self.effect_tracker = None
        self.combatant_positioning_hash = None

    def __str__(self):
        string_repr = ""
        for y in range(self.size - 1, -1, -1):
            row_text = ""
            for x in range(self.size):
                square = self.grid[x, y]
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
    def as_if_combatant_position(self, combatant, coords: np.array):
        original_coords = self.combatant_coordinate_cache[combatant]
        original_logger_level = logger.level
        logger.setLevel(logging.WARNING)
        self.move_combatant(combatant, coords)
        try:
            yield self
        finally:
            self.move_combatant(combatant, original_coords.get()[0])
            logger.setLevel(original_logger_level)

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

    def place_circular_element(self, coord, terrain_type, diameter=1):
        N = self.size
        if diameter == 1:
            x = max(0, min(coord[0], N - 1))
            y = max(0, min(coord[1], N - 1))
            if terrain_type == Terrain.IMPASSABLE_TERRAIN:
                self.grid[x][y].terrain = Terrain.IMPASSABLE_TERRAIN
                self.impassable_set.add((coord[0], coord[1]))
            elif terrain_type == Terrain.DIFFICULT_TERRAIN:
                self.grid[x][y].terrain = Terrain.DIFFICULT_TERRAIN
                self.difficult_set.add((coord[0], coord[1]))
        elif diameter > 1:
            for x_offset in range(-math.floor(diameter / 2), math.floor(diameter / 2) + 1):
                for y_offset in range(-math.floor(diameter / 2), math.floor(diameter / 2) + 1):
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
                adj_coords = self.get_free_coords_in_hop_range(coords, inflate_to_size=combatant.size, rng=rng)
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

    def dijkstra(self, src, mask):
        """
        Implementation of the Dijkstra algorithm with a preference for the least zig-zaggy path
        :param src: source coordinate
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
        adj = np.multiply(self.base_adjacency_matrix, mask)
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
                try:
                    pre_increment_dist = self.get_hop_distance(combatant, curr_combatant)
                    post_increment_dist = self.get_hop_distance(combatant_coords.get() + increment, coords.get())
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
                pre_increment_dist = self.get_hop_distance(combatant, curr_combatant)
                post_increment_dist = self.get_hop_distance(self.combatant_coordinate_cache[combatant].get() + increment, pos.get())
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

    def are_empty(self, coords: CombatantCoords):
        vec_is_empty = np.vectorize(GridSquare.is_empty)
        return np.all(vec_is_empty(self.grid[coords.get()[:, 0], coords.get()[:, 1]]))

    # @dispatch(CombatantCoords)
    def are_empty_or_self(self, coords: CombatantCoords, combatant):
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
        old_coords = self.combatant_coordinate_cache[combatant].get()
        for old_coord in old_coords:
            self.grid[old_coord[0], old_coord[1]].remove_combatant()
        new_coords = CombatantCoords(new_coords, combatant)
        new_coords_data = new_coords.get()
        assert self.size > np.amax(new_coords_data) and np.amin(new_coords_data) > -1, f"Invalid coord {new_coords_data}"
        for new_coord in new_coords_data:
            self.grid[new_coord[0], new_coord[1]].set_combatant(combatant)
        self.combatant_coordinate_cache[combatant] = new_coords
        logger.info(f"{combatant} moved to {new_coords_data[0]}", extra={"team": self.teams.get_team(combatant)})

    def set_combatant_coordinates(self, combatant, coords: np.array):
        coords = CombatantCoords(coords, combatant)
        def set_comb(square):
            square.set_combatant(combatant)
            return square
        vec_set_comb = np.vectorize(set_comb)
        try:
            self.grid[coords.get()[:, 0], coords.get()[:, 1]] = vec_set_comb(self.grid[coords.get()[:, 0], coords.get()[:, 1]])
        except IndexError:
            print("FIXME")
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
        dist_func = self.get_hop_distance if dist_type is DistanceMetric.HOP else self.get_cartesian_distance
        min_dist = sys.float_info.max
        nearest = None
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


    def is_ally_adjacent_to_target(self, combatant, target_combatant):
        """
        Used for pack tactics to determine if an ally that is not incapacitated is adjacent to a combatant
        :param combatant: the combatant to test if they benefit from pack tactics
        :param target_combatant: the target combatant
        :return: True if there's a non-incapacited ally adjacent
        """
        target_coords = self.combatant_coordinate_cache[target_combatant]
        adjacent_coords = self.get_adjacent_coords(target_coords)
        for adjacent_coord in adjacent_coords:
            potential_ally = self.grid[adjacent_coord[0], adjacent_coord[1]].combatant
            if potential_ally and potential_ally is not combatant and self.teams.are_allies(combatant, potential_ally) and not potential_ally.is_affected_by_any(Conditions.INCAPACITATED):
                return True
        return False

    def are_in_hop_range(self, combatant1, combatant2, distance):
        return self.get_hop_distance(combatant1, combatant2) <= distance

    def get_hop_distance(self, subject1, subject2):
        """
        Universal hop distance function. Accepts both characters or coordinates
        :param subject1: either a numpy.array or a Combatant type
        :param subject2: either a numpy.array or a Combatant type
        :return: distance between subjects in number of hops, None if one of the subjects is dead
        """
        subject1 = self.combatant_coordinate_cache[subject1].get() if issubclass(type(subject1), Combatant) else subject1
        subject2 = self.combatant_coordinate_cache[subject2].get() if issubclass(type(subject2), Combatant) else subject2
        try:
            dist_mat = distance_matrix(subject1, subject2)
            min_dist_index = np.argmin(dist_mat)  # find the index closest distance between the two sets of points
            sub1_closest_coord = subject1[min_dist_index // dist_mat.shape[1], :]
            sub2_closest_coord = subject2[min_dist_index % dist_mat.shape[1], :]
            res = np.max(np.abs(sub1_closest_coord - sub2_closest_coord))
        except TypeError as e:
            res = None
        return res

    def get_cartesian_distance(self, subject1, subject2):
        """
        Universal cartesian distance function. Accepts both characters or coordinates
        :param subject1: either a Combatant type or a numpy array
        :param subject2: either a Combatant type or a numpy array
        :return: cartesian distance between subjects, None if one of the subjects is dead
        """
        try:
            subject1 = self.combatant_coordinate_cache[subject1].get() if issubclass(type(subject1), Combatant) else subject1
            subject2 = self.combatant_coordinate_cache[subject2].get() if issubclass(type(subject2), Combatant) else subject2
        except KeyError:
            return None
        try:
            res = np.amin(distance_matrix(subject1, subject2))
        except TypeError:
            res = None
        return res

    def inflate_coords(self, coords: CombatantCoords, inflate_to_size):
        """
        A helper function which inflates the given CombatantCoords to a given size (they may already by inflated but may need further inflation
        due to the size of the other combatant).
        :param coords: target combatant coordinates
        :param inflate_to_size: size of the other combatant
        :return: inflated set of coordinates (as x, y tuples)
        """
        offset = 0
        if inflate_to_size.value > Size.MEDIUM.value:
            offset = inflate_to_size.value

        inflated = set()
        for coord in coords.get():
            for x, y in [(x, y) for x in range(coord[0] - offset, coord[0] + 1) for y in range(coord[1] - offset, coord[1] + 1)]:
                inflated.add((max(0, x), max(0, y)))
        return inflated

    def get_free_coords_in_hop_range(self, coords: CombatantCoords, distances=None, inflate_to_size=Size.MEDIUM, rng=1, combatant=None):
        """
        Returns free squares coordinates adjacent (up to the range distance) to a given coordinate that can be occupied
        by a combatant of 'inflate_to_size' size.
        :param coords: target combatant coordinates
        :param distances: the distances to all squares (result of Dijkstra) to be able to recognize accessibility of coordinates
        :param inflate_to_size: inflate for the sake of pathfinding BY larger combatants
        :param rng: maximum range of what is considered 'adjacent'
        :param combatant: optional combatant which is to be considered 'self' for the sake of is_empty_or_self
        :return: free adjacent coordinates as a set of tuples (x, y)
        """
        assert rng > 0
        inflated = self.inflate_coords(coords, inflate_to_size)

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
        return adjacent_coords


    def get_free_coords_in_cartesian_range(self, coords: CombatantCoords, distances=None, inflate_to_size=Size.MEDIUM, rng=1, combatant=None):
        """
        Returns free square coordinates that are at the most rng away from the coords as measured by cartesian distance that can be occupied
        by a combatant of 'inflate_to_size' size. It's pretty much the same as get_free_coords_in_hop_range but it uses the rng as a
        bounding box to narrow down the search.
        :param coords: target combatant or destination coordinates
        :param distances: the distances to all squares (result of Dijkstra) to be able to recognize accessibility of coordinates
        :param inflate_to_size: inflate for the sake of pathfinding BY larger combatants (as opposed to TO larger combatants)
        :param rng: maximum range
        :param combatant: optional combatant which is to be considered 'self' for the sake of is_empty_or_self
        :return: free adjacent coordinates as a set of tuples (x, y)
        """
        assert rng > 0
        # First inflate it by the size of the combatant looking for the path
        inflated = self.inflate_coords(coords, inflate_to_size)

        coords_in_range = set()
        for coord in inflated:
            # the rng can be used as a bounding box for the search
            for x, y in [(coord[0] + i, coord[1] + j) for i in range(-rng, rng + 1) for j in range(-rng, rng + 1)]:
                if x < 0 or x >= self.size or y < 0 or y >= self.size or self.get_cartesian_distance(coords.get(), np.array([[x, y]])) > rng:
                    continue
                square = self.grid[x, y]
                consider_accesibility = (distances[x * self.size + y] < sys.maxsize) if distances is not None else True
                if square.is_empty_or_self(combatant) and consider_accesibility:# and (x, y) not in inflated:
                    # have to use tuples since np.array is unhashable
                    coords_in_range.add((x, y))
        return coords_in_range

    def get_all_accessible_coords(self, shortest_paths):
        """
        Returns all free and square coordinates accessible by a combatant given the shortest paths dict (output of Dijkstra)
        :param shortest_paths: the shortest paths to all squares (result of Dijkstra)
        :return: free and accessible coordinates as a set of tuples (x, y)
        """
        return set(shortest_paths.keys())


    def get_adjacent_coords(self, coords: CombatantCoords):
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

    def get_nearest_free_adjacent_coords(self, my_location: CombatantCoords, target_location: CombatantCoords, distances, rng=1):
        """
        Get nearest free adjacent coordinates accounting for the combatant's size. Potentially increasing what is considered adjacent to rng.
        :param my_location: the combatant location
        :param target_location: the target location
        :param distances: distances for all coords in the grid
        :param rng: the range of what is considered adjacent
        :return:
        """
        adjacent_coords = self.get_free_coords_in_hop_range(target_location, distances, my_location.size, rng,
                                                            combatant=my_location.combatant)
        if not adjacent_coords:
            return None
        adjacent_coords = [np.array([x]) for x in adjacent_coords]
        adjacent_coords.sort(key=lambda coord: self.get_cartesian_distance(coord, my_location.get()))
        return adjacent_coords[0][0]

    # def get_free_adjacent_coords_within_distance(self, my_location: CombatantCoords, target_location: CombatantCoords, shortest_paths, distances, max_dist):
    #     """
    #     Get all free and accessible coords withing distance from my_location and max range distance from target location.
    #     :param my_location: the origin location
    #     :param target_location: the target location distance
    #     :param target_location: the array of distances for each square from the PoV of the combatant
    #     :param distances: the array of distances for each square from the PoV of the combatant
    #     :param max_dist: the maximum hop distance from my_location
    #     :return:
    #     """
    #     adjacent_coords = self.get_free_coords_in_hop_range(target_location, shortest_paths, my_location.size)
    #     if not adjacent_coords:
    #         return None
    #     adjacent_coords = [np.array([x]) for x in adjacent_coords]
    #     adjacent_coords.sort(key=lambda coord: self.get_cartesian_distance(coord, my_location.get()))
    #     return adjacent_coords[0][0]

    def calc_dijkstra(self, combatant):
        """
        Calculates the Dijkstra algorithm for a given combatant. Currently used only for testing
        :param combatant: combatant who wants to move
        :return: :return: list of distances to all vertices, list of predecessors for every vertex and the threat adjacency matrix
        """
        my_location = self.get_combatant_position(combatant)
        mask = self.build_combatant_adjacency_mask(combatant)
        distances, shortest_paths = self.dijkstra(my_location.get()[0], mask)
        return distances, shortest_paths


    def get_path_to_combatant(self, combatant, target_combatant, distances=None, shortest_paths=None, rng=1, consider_aoo=False):
        """
        Calculates a path to a target combatant
        :param combatant:Combatant who wants to move
        :param target_combatant:
        :param distances: potentially already pre-computed distances to all coords
        :param shortest_paths: potentially already pre-computed shortest paths to all coords
        :param rng: the range of what is considered adjacent
        :return: list of np.array increments to the target combatant
        """
        my_location = self.get_combatant_position(combatant)
        logger.debug(f"Origin {my_location.get()[0]}")
        enemy_location = self.get_combatant_position(target_combatant)
        logger.debug(f"Destination {enemy_location.get()[0]}")
        if not distances or not shortest_paths:
            mask = self.build_combatant_adjacency_mask(combatant, consider_aoo)
            distances, shortest_paths = self.dijkstra(my_location.get()[0], mask)
        enemy_adjacent_location = self.get_nearest_free_adjacent_coords(my_location, enemy_location, distances, rng)
        if enemy_adjacent_location is None:
            return None
        reconstructed_path = reconstruct_from_shortest_path(shortest_paths, my_location.get(), enemy_adjacent_location)
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
            distances, shortest_paths = self.dijkstra(my_location.get()[0], mask)
        reconstructed_path = reconstruct_from_shortest_path(shortest_paths, my_location.get(), target_coord)
        if reconstructed_path is None:
            return None
        if logger.root.level <= logging.INFO:
            self.printDijkstra(distances, my_location.get(), np.array([target_coord]), reconstructed_path['tuples'])
        return convert_path_to_increments(reconstructed_path['numpy'])


    def get_combatant_position(self, combatant):
        try:
            return self.combatant_coordinate_cache[combatant]
        except KeyError as e:
            logger.error(e)
            return None

    def get_free_coords_at_distance_sorted_by_dist_to_enemies(self, moving_combatant, distance, dist_type=DistanceMetric.HOP):
        """
        Returns a list of coordinates that are at a certain distance from the moving combatant. Sorted by distance to the nearest enemy
        :param moving_combatant: combatant who wants to get away
        :param distance: how far the combatant can go
        :return: sorted by the minimum distance to any enemy in ascending order
        """
        elligible_coords = []
        root_coord = np.array([self.combatant_coordinate_cache[moving_combatant].get()[0, :]])
        dist_func = self.get_hop_distance if dist_type is DistanceMetric.HOP else self.get_cartesian_distance
        # optimization - narrowing search down to a bounding box
        for i in range(-distance, distance + 1):
            for j in range(-distance, distance + 1):
                curr_coord = root_coord + np.array([i, j])
                if curr_coord[0][0] in range(0, self.size) and curr_coord[0][1] in range(0, self.size):
                    square = self.grid[curr_coord[0][0], curr_coord[0][1]]
                    if square.is_empty() and dist_func(curr_coord, root_coord) == distance:
                        elligible_coords.append(curr_coord)

        def by_distance_to_nearest_enemy(coord):
            min_dist = sys.maxsize
            for combatant, cmbt_coord in self.combatant_coordinate_cache.items():
                if combatant.is_alive() and self.teams.are_enemies(moving_combatant, combatant):
                    dist = self.get_hop_distance(coord, cmbt_coord.get())
                    min_dist = min(dist, min_dist)
            return min_dist

        elligible_coords.sort(key=by_distance_to_nearest_enemy, reverse=True)
        return elligible_coords

    def get_free_coords_at_distance_from_target(self, target_combatant, combatant, min_dist, max_dist=sys.maxsize):
        """
        Returns a list of coordinates that are unoccupied and at a given distance range from a target, sorted by ascending proximity to self
        :param target_combatant: target to which the distance is measured
        :param combatant: sorted by ascending proximity to this combatant
        :param min_dist: minimum desired distance
        :param max_dist: maximum desired distance
        :return: list of numpy.array coordinates
        """
        assert min_dist > 0
        self_coord = self.combatant_coordinate_cache[combatant]
        target_coord = self.combatant_coordinate_cache[target_combatant]
        coords = []
        for x, y in [(x, y) for x in range(0, self.size) for y in range(0, self.size)]:
            potential_self_coord = CombatantCoords(np.array([x, y]), combatant)
            dist = self.get_hop_distance(target_coord.get(), potential_self_coord.get())
            is_empty = self.grid[x, y].is_empty()
            if is_empty and min_dist <= dist <= max_dist:
                coords.append(potential_self_coord.get()[0])

        coords.sort(key=lambda coord: self.get_hop_distance(self_coord.get(), np.array([coord])))
        return coords

    def get_free_coords_sorted_by_distance_from_enemies(self, combatant):
        """
        Returns all free coordinates in a np.array matrix sorted by distances to the nearest enemy
        :param combatant: combatant for which the coordinates are to be found
        :return: numpy.array of nx2 shape where n is the number of coordinates returned
        """
        coords = []
        distances = []
        for x, y in [(x, y) for x in range(0, self.size) for y in range(0, self.size)]:
            potential_self_coord = CombatantCoords(np.array([x, y]), combatant)
            is_empty = self.are_empty(potential_self_coord)
            if not is_empty:
                continue
            min_dist = sys.maxsize
            for potential_enemy, cmbt_coord in self.combatant_coordinate_cache.items():
                if potential_enemy.is_alive() and self.teams.are_enemies(potential_enemy, combatant):
                    dist = self.get_hop_distance(potential_enemy, potential_self_coord.get())
                    min_dist = min(min_dist, dist)
                else:
                    continue
            coords.append(potential_self_coord.get()[0])
            distances.append(min_dist)
        # Convert it into a concatenated nx2 np.array
        return np.stack([c for _, c in sorted((zip(distances, coords)), key=lambda x: x[0], reverse=True)])

    def remove_combatant(self, combatant):
        """
        Removes a dead combatant from the grid
        :param combatant:
        :return:
        """
        logger.info(f"{combatant} died")
        try:
            old_coords = self.combatant_coordinate_cache[combatant].get()
        except KeyError:
            return  # already removed
        for coord in old_coords:
            self.grid[coord[0], coord[1]].remove_combatant()
        del self.combatant_coordinate_cache[combatant]

    # def clear(self):
    #     for row in self.grid:
    #         for square in row:
    #             square.remove_combatant()
    #             square.reset_terrain()
    #     for coords in self.combatant_coordinate_cache.values():
    #         coords.get().fill(0)
    #     self.impassable_set.clear()
    #     self.difficult_set.clear()
    #     self.terrain_encoding.fill(Terrain.NORMAL_TERRAIN.value)


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

    def find_best_placement_harmful_circular(self, caster, spell_range, radius):
        """
        Finds the best placement of a spherical harmful AoE effect
        :param caster: the caster
        :param spell_range: range of the spell/ability
        :param radius: radius of the harmful AoE effect
        :return: best coordinate,achieved score and set of affected combatants
        """
        # Find a BB for all the enemy combatants inflated by the range and then iterate over all squares finding one with the best hit score
        bb = self.get_harmful_bounding_box(caster, radius)
        max_score = -sys.maxsize - 1
        best_placement = None
        best_affected = None
        caster_coords = self.combatant_coordinate_cache[caster].get()
        for x, y in [(x, y) for x in range(bb[0][0], bb[1][0]) for y in range(bb[0][1], bb[1][1])]:
            curr_coord = np.array([[x, y]])
            affected = []
            if self.get_cartesian_distance(caster_coords, curr_coord) > spell_range or any((caster_coords[:] == curr_coord).all(1)):
                continue  # Skip those outside of spell range and those taken up by the caster
            score = 0
            for combatant, coords in self.combatant_coordinate_cache.items():
                if self.get_cartesian_distance(coords.get(), curr_coord) <= radius:
                    score += 1 if self.teams.are_enemies(caster, combatant) and combatant.is_alive() else -4
                    affected.append(combatant)
            if score > max_score:
                max_score = score
                best_placement = curr_coord
                best_affected = affected
        # logger.info(f"HARMFUL EFFECT PLACEMENT {best_placement} with score {max_score}")
        return best_placement, max_score, best_affected

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
            if self.get_cartesian_distance(caster_coords, curr_coord) > spell_range or any((caster_coords[:] == curr_coord).all(1)):
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
        logger.info(self)
        return best_placement, max_score, best_affected

    def get_combatants_affected_by_aoe_with_caster_mock_position(self, caster, caster_coords: CombatantCoords, target_template, ability_type, origin, angle=0):
        """
        Gets combatants affected by an AoE effect
        :param caster: the caster of the AoE
        :param caster_coords: the 'as if' position of the caster
        :param target_template: RADIUS_X or CONE_Y
        :param ability_type: SpellStats.Type.HARMFUL or SpellStats.Type.BUFF
        :param origin: origin of the AoE
        :param angle: yaw angle of the cone, marks the center line through the cone, north clock-wise oriented
        :return: affected combatants
        """
        if caster_coords is not None:
            with self.as_if_combatant_position(caster, caster_coords.get()[0]):
                ret = self.get_combatants_affected_by_aoe(caster, target_template, ability_type, origin, angle)
        else:
            ret = self.get_combatants_affected_by_aoe(caster, target_template, ability_type, origin, angle)
        return ret

    def get_combatants_affected_by_aoe(self, caster, target_template, ability_type, origin, angle=0):
        """
        Gets combatants affected by an AoE effect
        :param caster: the caster of the AoE
        :param target_template: RADIUS_X or CONE_Y
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
                        if self.get_cartesian_distance(combatant_coords.get(), np.array([origin])) <= SpellStats.TRANSLATE_RADIUS[
                                target_template]:
                            affected_combatants.append(potential_target)
                    elif ability_type is SpellStats.Type.BUFF:
                        # generally you can opt only to target your allies with buff spells
                        if self.get_cartesian_distance(combatant_coords.get(), np.array([origin])) <= SpellStats.TRANSLATE_RADIUS[
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
        return [a for a in self.teams.get_allies(combatant) if a.is_alive() and self.get_cartesian_distance(a, combatant) <= radius]

    def get_enemies(self, combatant):
        return [e for e in self.teams.get_enemies(combatant) if e.is_alive()]

    def get_allies(self, combatant):
        return [a for a in self.teams.get_allies(combatant) if a.is_alive()]

    def get_enemies_within_hop_distance(self, combatant, distance):
        return [e for e in self.teams.get_enemies(combatant) if e.is_alive() and self.get_hop_distance(e, combatant) <= distance]

    # def get_enemies_within_hop_distance(self, combatant, distance, distances):
    #     """
    #     Get all enemies from combatant within hop distance using distances computed by Dijkstra
    #     :param combatant: the combatant used as origin
    #     :param distance: the maximum distance
    #     :param distances: the array of distances for each square from the PoV of the combatant
    #     :return:
    #     """
    #     return [e for e in self.teams.get_enemies(combatant) if e.is_alive() and self.get_hop_distance(e, combatant) <= distance]

    def get_enemies_within_their_movement_range(self, combatant):
        return [e for e in self.teams.get_enemies(combatant) if e.is_alive() and self.get_hop_distance(e, combatant) <= e.movement + 1]

    def is_difficult_terrain_at(self, coords: CombatantCoords):
        vec_is_difficult_terrain = np.vectorize(GridSquare.is_difficult_terrain)
        return np.any(vec_is_difficult_terrain(self.grid[coords.get()[:, 0], coords.get()[:, 1]]))


    # def has_combatant_positioning_changed(self, new_hash):
    #     """
    #     Determines if the collective positioning of all combatants has changed since the last call. Note that this is NOT updated along
    #     with the positioning of combatants. It's determined as compared to the last call of this method ONLY!
    #     :param: new_hash the new hash  recalculated by the callee
    #     :return: True if the positioning of any combatant has changed since last call, False otherwise
    #     """
    #     # TODO Unit-test this
    #     if new_hash != self.combatant_positioning_hash:
    #         self.combatant_positioning_hash = new_hash
    #         return True
    #     return False
    #
    # def calc_positioning_hash(self):
    #     return hash(frozenset(self.combatant_coordinate_cache.items()))
