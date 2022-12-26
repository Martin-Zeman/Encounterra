import numpy as np
import math
import sys
import logging
from simulator.spells.spell import Spell
from simulator.combatant import Combatant
from multipledispatch import dispatch
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
            logger.error(e)  # TODO remove this once fixed
    else:
        path['numpy'].append(my_location)
        path['tuples'].append(tuple(my_location))
    path['numpy'].reverse()
    path['tuples'].reverse()
    return path


def get_hop_distance(coord1, coord2):
    return np.max(np.abs(coord1 - coord2))


def do_circles_boxes_overlap(origin1, origin2, radius):
    """
    :param origin1:
    :param origin2:
    :param radius: radius share by both circles
    :return: True if they overlap by at least width 1, false otherwise
    """
    dist = get_hop_distance(origin1, origin2)
    return (2 * radius) >= dist + 1

class Terrain(Enum):
    NORMAL_TERRAIN = 1
    DIFFICULT_TERRAIN = 2
    IMPASSABLE_TERRAIN = 3

class Occupancy(Enum):
    FREE = 1
    OCCUPIED_BY_COMBATANT = 2

class GridCell:
    def __init__(self):
        self.combatant = None
        self.terrain = Terrain.NORMAL_TERRAIN
        self.is_opaque = False
        self.occupancy = Occupancy.FREE

    def set_combatant(self, combatant):
        if self.occupancy is not Occupancy.FREE or self.terrain is Terrain.IMPASSABLE_TERRAIN or self.combatant:
            logger.error("FIXME")# TODO remove me
        self.combatant = combatant
        self.occupancy = Occupancy.OCCUPIED_BY_COMBATANT

    def remove_combatant(self):
        self.combatant = None
        self.occupancy = Occupancy.FREE

    def get_combatant(self):
        return self.combatant

    # def set_opaqueness(self, opaque):
    #     self.is_opaque = opaque

    def set_occupancy(self, occupancy):
        self.occupancy = occupancy

    def is_empty(self):
        # TODO only the first two parts of the condition should suffice
        return self.occupancy is Occupancy.FREE and self.terrain is not Terrain.IMPASSABLE_TERRAIN and self.combatant is None


class Map:

    def __init__(self, size, teams):
        self.size = size
        self.teams = teams
        self.grid = [[GridCell() for _ in range(size)] for _ in range(size)]
        self.base_adjacency_matrix = np.zeros((size, size))
        self.difficult_set = set()
        self.combatant_coordinate_cache = {}

    def __str__(self):
        string_repr = ""
        for row in self.grid:
            row_text = ""
            for cell in row:
                combatant = cell.get_combatant()
                if combatant:
                    row_text += self.teams.get_team_color_code(combatant) + combatant.get_name()[0] + "\x1b[0m\t"
                else:
                    row_text += "0\t"
            string_repr += row_text + "\n"
        return string_repr

    def place_circular_element(self, coords, terrain_type, diameter=1):
        N = self.size
        coords = (coords[0], coords[1])
        if diameter == 1:
            if terrain_type == Terrain.IMPASSABLE_TERRAIN:
                self.grid[max(0, min(coords[0], N - 1))][max(0, min(coords[1], N - 1))].terrain = Terrain.IMPASSABLE_TERRAIN
            elif terrain_type == Terrain.DIFFICULT_TERRAIN:
                self.grid[max(0, min(coords[0], N - 1))][max(0, min(coords[1], N - 1))].terrain = Terrain.DIFFICULT_TERRAIN
                self.difficult_set.add((coords[0], coords[1]))
        elif diameter > 1:
            for x in range(-math.floor(diameter / 2), math.floor(diameter / 2) + 1):
                for y in range(-math.floor(diameter / 2), math.floor(diameter / 2) + 1):
                    try:
                        if terrain_type == Terrain.IMPASSABLE_TERRAIN:
                            self.grid[coords[0] + x][coords[1] + y].terrain = Terrain.IMPASSABLE_TERRAIN
                        elif terrain_type == Terrain.DIFFICULT_TERRAIN:
                            self.grid[coords[0] + x][coords[1] + y].terrain = Terrain.DIFFICULT_TERRAIN
                            self.difficult_set.add((coords[0] + x, coords[1] + y))
                    except IndexError:
                        pass  # out of grid

    def build_adjacency_matrix(self):
        start_time = time.time()
        N = self.size
        Nsq = N ** 2
        adj = np.zeros((N, N, N, N))
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
        adj -= np.eye(Nsq)
        for coord in self.difficult_set:
            adj[:, coord[0] * N + coord[1]] *= 2
        self.base_adjacency_matrix = adj
        print("---build_adjacency_matrix took %s seconds ---" % (time.time() - start_time))

    def build_combatant_adjacency_mask(self, combatant):
        """
        Builds a combatant-specific mask for the adjacency matrix. It models enemies as being impassable by 0.
        Allies are considered difficult terrain (potentially on top of already difficult terrain)
        :param combatant: for whom the mask is to be constructed
        :return: adjacency matrix mask
        """
        N = self.size
        # TODO consider preallocating this for all combatants and only resetting it to ones
        mask = np.ones((self.size**2, self.size**2))
        for curr_combatant, coord in self.combatant_coordinate_cache.items():
            if curr_combatant is not combatant and curr_combatant.is_alive():
                mask[:, coord[0] * N + coord[1]] = 0 if self.teams.are_enemies(curr_combatant, combatant) else 2
        return mask

    def printSolution(self, distances, my_location, enemy_location, reconstructed_path):
        my_coord = my_location[0] * self.size + my_location[1]
        enemy_coord = enemy_location[0] * self.size + enemy_location[1]
        for x in range(self.size):
            row = ""
            for y in range(self.size):
                coord = x * self.size + y
                if coord == my_coord:
                    row += "\x1b[38;5;39m%d\x1b[0m\t" % distances[coord]
                elif coord == enemy_coord:
                    row += "\x1b[38;5;196m%d\x1b[0m\t" % distances[coord]
                elif (x, y) in reconstructed_path:
                    row += "\u001b[36m%d\x1b[0m\t" % distances[coord]
                else:
                    row += "%d\t" % distances[coord] if (x, y) not in self.difficult_set else "\x1b[38;5;226m%d\x1b[0m\t" % distances[coord]
            logger.debug(row)

    def minDistance(self, dist, sptSet):
        Nsq = self.size ** 2
        min = sys.maxsize
        min_index = None

        for u in range(Nsq):
            if dist[u] < min and sptSet[u] is False:
                min = dist[u]
                min_index = u
        return min_index

    def dijkstra(self, src, mask):
        src = np.array(src)
        N = self.size
        Nsq = self.size ** 2
        dist = [sys.maxsize] * Nsq
        dist[src[0] * self.size + src[1]] = 0
        sptSet = [False] * Nsq
        adj = np.multiply(self.base_adjacency_matrix, mask)
        shortest_paths = {}

        for _ in range(Nsq):
            x = self.minDistance(dist, sptSet)
            if x is None:
                # enemy-occupied cells are unreachable
                continue
            sptSet[x] = True
            for y in range(Nsq):
                if adj[x][y] > 0 and sptSet[y] is False:
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

    def convert_path_to_increments(self, path):
        increments = []
        for i in range(len(path) - 1):
            increments.append(path[i + 1] - path[i])
        logger.debug(increments)
        return increments

    def move_combatant_by_increment(self, combatant, increment):
        old_coord = self.combatant_coordinate_cache[combatant]
        self.grid[old_coord[0]][old_coord[1]].remove_combatant()
        new_coord = old_coord + increment
        self.grid[new_coord[0]][new_coord[1]].set_combatant(combatant)
        self.combatant_coordinate_cache[combatant] = new_coord
        logger.debug(f"{combatant.get_name()} moved to {new_coord}", extra={"team": self.teams.get_team(combatant)})

    def move_combatant(self, combatant, new_coord):
        old_coord = self.combatant_coordinate_cache[combatant]
        self.grid[old_coord[0]][old_coord[1]].remove_combatant()
        self.grid[new_coord[0]][new_coord[1]].set_combatant(combatant)
        self.combatant_coordinate_cache[combatant] = new_coord
        logger.debug(f"{combatant.get_name()} moved to {new_coord}", extra={"team": self.teams.get_team(combatant)})

    def get_aoo_eligible_combatants(self, combatant, increment):
        eligible_combatants = []
        for curr_combatant, pos in self.combatant_coordinate_cache.items():
            if curr_combatant is not combatant and curr_combatant.is_alive() and self.teams.are_enemies(curr_combatant, combatant):
                pre_increment_dist = self.get_distance(combatant, curr_combatant)
                post_increment_dist = get_hop_distance(self.combatant_coordinate_cache[combatant] + increment, pos)
                if pre_increment_dist == curr_combatant.max_melee_range and post_increment_dist > curr_combatant.max_melee_range and curr_combatant.has_reaction:
                    eligible_combatants.append(curr_combatant)
        return eligible_combatants

    def get_pam_eligible_combatants(self, combatant, increment):
        eligible_combatants = []
        for curr_combatant, pos in self.combatant_coordinate_cache.items():
            if curr_combatant is not combatant and self.teams.are_enemies(curr_combatant, combatant):
                try:
                    pre_increment_dist = self.get_distance(combatant, curr_combatant)
                    post_increment_dist = get_hop_distance(self.combatant_coordinate_cache[combatant] + increment, pos)
                except KeyError:
                    continue
                if pre_increment_dist > curr_combatant.max_melee_range and post_increment_dist == curr_combatant.max_melee_range and curr_combatant.has_reaction and curr_combatant.has_polearm_master:
                    eligible_combatants.append(curr_combatant)
        return eligible_combatants

    def is_empty(self, coord):
        return self.grid[coord[0]][coord[1]].is_empty()

    def can_see(self, x1, y1, x2, y2):
        return True

    def set_combatant_coordinates(self, combatant, coord):
        # TODO: redo this as np.array
        logger.debug(f"Setting coordinates {coord} for comabatant {combatant.get_name()}")
        self.grid[coord[0]][coord[1]].set_combatant(combatant)
        self.combatant_coordinate_cache[combatant] = coord

    def get_nearest_enemy(self, combatant):
        min_dist = sys.float_info.max
        nearest_enemy = None
        self_position = self.combatant_coordinate_cache[combatant]
        for potential_target, target_coord in self.combatant_coordinate_cache.items():
            dist = np.linalg.norm(target_coord - self_position)
            if potential_target is not combatant and potential_target.is_alive() and self.teams.are_enemies(potential_target, combatant) and dist < min_dist:
                min_dist = dist
                nearest_enemy = potential_target
        return nearest_enemy

    def is_enemy_adjacent(self, character):
        self_coords = self.combatant_coordinate_cache[character]
        for x in range(-1, 2):
            for y in range(-1, 2):
                try:
                    cmbt = self.grid[self_coords[0] + x][self_coords[1] + y].combatant
                    if cmbt and self.teams.are_enemies(character, cmbt):
                        return True
                except IndexError:
                    continue
        return False

    def are_in_range(self, combatant1, combatant2, distance):
        combatant1_position = np.array(self.combatant_coordinate_cache[combatant1])
        combatant2_position = np.array(self.combatant_coordinate_cache[combatant2])
        return np.max(np.abs(combatant1_position - combatant2_position)) <= distance

    def get_distance(self, subject1, subject2):
        """
        Universal distance function. Accepts both characters or coordinates
        :param subject1: either a character or a numpy array
        :param subject2: either a character or a numpy array
        :return: distance between subjects, None if one of the subjects is dead
        """
        subject1 = self.combatant_coordinate_cache[subject1] if issubclass(type(subject1), Combatant) else subject1
        subject2 = self.combatant_coordinate_cache[subject2] if issubclass(type(subject2), Combatant) else subject2
        try:
            res = np.max(np.abs(subject1 - subject2))
        except TypeError as e:
            res = None
        return res

    def get_adjacent_coords(self, coord):
        adjacent_coords = set()
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                cell = self.grid[np.clip(coord[0] + dx, 0, self.size - 1)][np.clip(coord[1] + dy, 0, self.size - 1)]
                if cell.occupancy is Occupancy.FREE and cell.terrain is not Terrain.IMPASSABLE_TERRAIN:
                    # have to use tuples since np.array is unhashable
                    adjacent_coords.add((coord[0] + dx, coord[1] + dy))
        return adjacent_coords


    def get_nearest_adjacent_coord(self, my_location, target_location):
        adjacent_coords = self.get_adjacent_coords(target_location)
        assert adjacent_coords
        adjacent_coords = [np.array(x) for x in adjacent_coords]
        adjacent_coords.sort(key=lambda coord: np.linalg.norm(coord - my_location))
        return adjacent_coords[0]

    @dispatch(Combatant, Combatant)
    def get_path_to(self, combatant, target_combatant):
        my_location = self.get_combatant_position(combatant)
        logger.debug(f"My location {my_location}")
        enemy_location = self.get_combatant_position(target_combatant)
        logger.debug(f"Enemy location {enemy_location}")
        mask = self.build_combatant_adjacency_mask(combatant)
        distances, shortest_path = self.dijkstra(my_location, mask)
        enemy_adjacent_location = self.get_nearest_adjacent_coord(my_location, enemy_location)
        reconstructed_path = reconstruct_from_shortest_path(shortest_path, my_location, enemy_adjacent_location)
        self.printSolution(distances, my_location, enemy_location, reconstructed_path['tuples'])
        return self.convert_path_to_increments(reconstructed_path['numpy'])

    @dispatch(Combatant, np.ndarray)
    def get_path_to(self, combatant, target_coord):
        """
        calculates a path to destination coordinates
        :param combatant:Combatant who wants to move
        :param target_coord:
        :return:
        """
        # TODO: consider making a variant which doesn't provoke AOO
        my_location = self.get_combatant_position(combatant)
        logger.debug(f"My location {my_location}")
        logger.debug(f"Destination location {target_coord}")
        mask = self.build_combatant_adjacency_mask(combatant)
        distances, shortest_path = self.dijkstra(my_location, mask)
        reconstructed_path = reconstruct_from_shortest_path(shortest_path, my_location, target_coord)
        self.printSolution(distances, my_location, target_coord, reconstructed_path['tuples'])
        return self.convert_path_to_increments(reconstructed_path['numpy'])

    def get_combatant_position(self, combatant):
        try:
            return self.combatant_coordinate_cache[combatant]
        except KeyError as e:
            logger.error(e)
            return None

    def get_free_coords_away_from_enemies(self, character, distance):
        """
        Returns a list of coordinates that are at a certain distance from character. Sorted by distance to the nearest enemy
        :param character: combatant who wants to get away
        :param distance: how far the combatant can go
        :return: sorted by the minimum distance to any enemy in ascending order
        """
        elligible_coords = []
        self_coord = self.combatant_coordinate_cache[character]
        # optimization - narrowing search down to a bounding box
        for i in range(-distance, distance + 1):
            for j in range(-distance, distance + 1):
                curr_coord = self_coord + np.array([i, j])
                if curr_coord[0] in range(0, self.size) and curr_coord[1] in range(0, self.size):
                    # TODO modify and use is_empty
                    cell = self.grid[curr_coord[0]][curr_coord[1]]
                    if cell.is_empty() and get_hop_distance(curr_coord, self_coord) == distance:
                        elligible_coords.append(curr_coord)

        # for i in range(self.size):
        #     for j in range(self.size):
        #         if get_hop_distance(np.array([i, j]), self_coord) == distance:
        #             elligible_coords.append(np.array([i, j]))

        def by_distance_to_nearest_enemy(coord):
            min_dist = sys.float_info.max
            min_dist_coord = coord
            for combatant, cmbt_coord in self.combatant_coordinate_cache.items():
                if combatant.is_alive() and self.teams.are_enemies(character, combatant):
                    dist = get_hop_distance(coord, cmbt_coord)
                    min_dist = min(dist, min_dist)
            return min_dist

        elligible_coords.sort(key=by_distance_to_nearest_enemy, reverse=True)
        return elligible_coords

    def get_free_coords_at_distance(self, target_combatant, distance, combatant):
        """
        Returns a list of coordinates that are unoccupied and at a given distance from a target, sorted by proximity to a
        combatant
        :param target_combatant: target to which the distance is measured
        :param distance: desired distance
        :param combatant: sorted by ascending proximity to this combatant
        :return: list of numpy.array coordinates
        """
        if distance <= 0:
            return []
        free_positions = []
        target_coords = self.combatant_coordinate_cache[target_combatant]
        for x in range(-distance, distance + 1):
            for y in range(-distance, distance + 1):
                if (target_coords[0] + x) < 0 or (target_coords[1] + y) < 0 or (target_coords[0] + x) >= self.size or (
                        target_coords[1] + y) >= self.size:
                    continue
                is_empty = self.grid[target_coords[0] + x][target_coords[1] + y].is_empty()
                curr_coord = target_coords + np.array([x, y])
                if is_empty and np.max(np.abs(target_coords - curr_coord)) == distance:
                    free_positions.append(np.array([target_coords[0] + x, target_coords[1] + y]))

        combatant_coord = self.combatant_coordinate_cache[combatant]
        free_positions.sort(key=lambda coord: np.linalg.norm(coord - combatant_coord))
        return free_positions

    def remove_combatant(self, combatant):
        """
        Removes a dead combatant from the grid
        :param combatant:
        :return:
        """
        logger.debug(f"Removing combatant {combatant.get_name()}")
        try:
            old_coord = self.combatant_coordinate_cache[combatant]
        except KeyError:
            return  # already removed
        self.grid[old_coord[0]][old_coord[1]].remove_combatant()
        del self.combatant_coordinate_cache[combatant]

    def reset(self):
        for row in self.grid:
            for cell in row:
                cell.remove_combatant()
        for combatant in self.combatant_coordinate_cache.keys():
            self.combatant_coordinate_cache[combatant] = np.zeros(2)

    def find_best_placement_harmful_circular(self, caster, spell_range, radius):
        # or find a BB for all the enemy combatants inflated by the range and then iterate over all cells finding one with the best hit score
        bb = np.array([[self.size, self.size], [0, 0]])  # top left, bottom right
        for combatant, coord in self.combatant_coordinate_cache.items():
            if self.teams.are_enemies(caster, combatant):
                bb[0] = np.minimum(bb[0], self.combatant_coordinate_cache[combatant])
                bb[1] = np.maximum(bb[1], self.combatant_coordinate_cache[combatant])
        # inflate the BB
        bb[0] = np.maximum(bb[0] - radius, np.array([0, 0]))
        bb[1] = np.minimum(bb[1] + radius, np.array([self.size - 1, self.size - 1]))
        max_score = -sys.maxsize - 1
        best_placement = None
        caster_coord = self.combatant_coordinate_cache[caster]
        for i in range(bb[0][0], bb[1][0]):
            for j in range(bb[0][1], bb[1][1]):
                curr_coord = np.array([i, j])
                if get_hop_distance(caster_coord, curr_coord) <= spell_range and caster_coord is not curr_coord:
                    score = 0
                    for combatant, coord in self.combatant_coordinate_cache.items():
                        score += (1 if self.teams.are_enemies(caster, combatant) and combatant.is_alive() else -4) if get_hop_distance(
                            coord,
                            curr_coord) <= radius else 0
                    if score > max_score:
                        max_score = score
                        best_placement = curr_coord
        logger.debug(self)
        logger.debug(f"HARMFUL EFFECT PLACEMENT {best_placement} with score {max_score}")
        return best_placement

    def get_combatants_affected_by_aoe(self, caster, ability):
        # TODO potentially check for protective abilities
        affected_combatants = []
        match ability.target:
            case Spell.Target.RADIUS_10 | Spell.Target.RADIUS_20 | Spell.Target.RADIUS_30:
                for potential_target, combatant_coord in self.combatant_coordinate_cache.items():
                    if ability.type is Spell.Type.HARMFUL:
                        if get_hop_distance(combatant_coord, ability.coord) <= Spell.TRANSLATE_RADIUS[ability.target]:
                            affected_combatants.append(potential_target)
                    elif ability.type is Spell.Type.BUFF:
                        # generally you can opt only to target your allies with buff spells
                        if get_hop_distance(combatant_coord, ability.coord) <= Spell.TRANSLATE_RADIUS[ability.target] and self.teams.are_allies(
                                caster, potential_target):
                            affected_combatants.append(potential_target)
            case _:
                logger.error("Unrecognized ability target type")
        return affected_combatants
