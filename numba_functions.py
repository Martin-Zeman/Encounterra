import heapq
import sys

from numba.np.arraymath import cross2d
from numba.pycc import CC
import numpy as np
from numba import int64, float64, int32, types, boolean, njit

from simulator.battle_map import Occupancy, Terrain
from simulator.misc import Size

cc = CC('numba_functions')


@cc.export('reconstruct_from_shortest_path', int64[:, :](int64[:, :, :], int64[:], int64[:]))
def reconstruct_from_shortest_path(shortest_path, source, target):
    """
    Works backwards using the shortest paths produced by Dijkstra to obtain a sequence of coordinates from source to
    target.
    :param shortest_path: shortest path ndarray of shape (15, 15, 2), dtype=np.int64
    :param source: source coordinates (numpy array of shape (2,), dtype=np.int64)
    :param target: target coordinates (numpy array of shape (2,), dtype=np.int64)
    :return: path from source to target as a sequence of coordinates (numpy array of dtype=np.int64)
    """
    max_path_length = shortest_path.shape[0] * shortest_path.shape[1]
    path = np.empty((max_path_length, 2), dtype=np.int64)
    path_length = 0

    source = source.astype(np.int64)
    current = target.astype(np.int64).copy()

    while not np.array_equal(current, source):
        path[path_length] = current
        path_length += 1
        current = shortest_path[current[0], current[1]]
        if np.array_equal(current, np.array([-1, -1], dtype=np.int64)):
            return np.empty((0, 2), dtype=np.int64)  # Return an empty array if no path is found

    path[path_length] = source
    path_length += 1
    return path[:path_length][::-1]


@njit
@cc.export('avg_roll_multi', float64(types.List(types.UniTuple(int32, 2))))
def avg_roll_multi(dice):
    acc = 0.0
    for d in dice:
        acc += d[0] * ((1.0 + d[1]) / 2.0)
    return acc


@cc.export('mean_dmg', float64(int32, types.List(types.UniTuple(int32, 2)), int32, int32, boolean, boolean, float64))
def mean_dmg(to_hit, dmg_dice, dmg_bonus, ac, is_immune=False, is_resistant=False, crit_range=1.0):
    """
    Calculates mean damage of an attack-like ability.
    """
    if is_immune:
        return 0.0

    rv = np.arange(1, 21) + to_hit
    p_hit = 1.0 - (np.sum(rv < ac) / 20.0)

    avg_dmg_die_roll = avg_roll_multi(dmg_dice)
    res = (avg_dmg_die_roll + dmg_bonus) * p_hit + 0.05 * crit_range * avg_dmg_die_roll
    if is_resistant:
        res /= 2.0

    return res


@cc.export('mean_dmg_dc_attack', float64(int32, types.List(types.UniTuple(int32, 2)), boolean, int32, boolean, boolean))
def mean_dmg_dc_attack(dc, dmg_dice, half_on_success, st_bonus, is_immune=False, is_resistant=False):
    """
    Calculates mean damage of a DC-based ability
    @param dc: DC
    @param dmg_dice: dmg dice as a list of tuples
    @param half_on_success: True if half damage is received on a successful saving throw, False if zero
    @param st_bonus: The relevant saving throw bonus for the check
    @param is_immune: is target immune to the dmg type
    @param is_resistant: is target resistant to the dmg type
    @return: Mean damage
    """
    if is_immune:
        return 0

    avg_dmg_die_roll = avg_roll_multi(dmg_dice)

    # Calculate probability of failing the saving throw
    p_fail = min(max((dc - st_bonus - 1) / 20, 0), 1)

    fail_dmg = avg_dmg_die_roll * p_fail
    success_dmg = avg_dmg_die_roll / 2.0 * (1.0 - p_fail) if half_on_success else 0
    final_avg_dmg = fail_dmg + success_dmg

    return final_avg_dmg if not is_resistant else final_avg_dmg / 2


@cc.export('mean_dmg_auto_hit', float64(types.List(types.UniTuple(int32, 2)), boolean))
def mean_dmg_auto_hit(dmg_dice, is_resistant=False):
    """
    Calculates mean dmg of an attack-like ability
    @param dmg_dice: damage dice as a list of tuples
    @param is_resistant: True if the target is resistant to the dmg type
    @return: mean damage
    """
    avg_dmg_die_roll = avg_roll_multi(dmg_dice)
    return avg_dmg_die_roll if not is_resistant else (avg_dmg_die_roll / 2)



@njit
@cc.export('roll_dice', int32(types.UniTuple(int32, 2)))
def roll_dice(dice):
    """
    Basic function for rolling dice
    @param dice: a dice tuple (number of dice, number of sides)
    @return: sum of dice rolls
    """
    num_dice, num_sides = dice
    return np.random.randint(1, num_sides + 1, num_dice).sum()


@cc.export('roll_dice_multi', int32(types.List(types.UniTuple(int32, 2))))
def roll_dice_multi(dice_list):
    """
    Function for rolling multiple sets of dice
    @param dice_list: list of dice tuples, each tuple is (number of dice, number of sides)
    @return: sum of all dice rolls
    """
    total_sum = 0
    for dice in dice_list:
        total_sum += roll_dice(dice)
    return total_sum


@cc.export('calc_p_hit', float64(int32, int32))
def calc_p_hit(to_hit, ac):
    """
    Calculates the probability of hitting
    @param to_hit: to hit bonus
    @param ac: target's AC
    @return: probability of hitting
    """
    min_roll = ac - to_hit
    min_roll = max(1, min(20, min_roll))
    p_hit = (21 - min_roll) / 20.0
    return p_hit


@cc.export('dfs', types.List(int64[::1])(int32[:, :, ::1], int32, int32))
def dfs(dag_forward, current_state, max_sequence_length):
    sequences = []
    empty_sequence = np.zeros(max_sequence_length, dtype=np.int64)
    sequence_length = 0
    stack = [(current_state, sequence_length, empty_sequence.copy())]

    while stack:
        state, sequence_length, current_sequence = stack.pop()

        if state == 1:  # 'nop' state
            sequences.append(current_sequence[:sequence_length].copy())
            continue

        for i in range(dag_forward.shape[1]):
            transition, next_state = dag_forward[state, i]
            if transition == -1:
                break
            if sequence_length < max_sequence_length:
                new_sequence = current_sequence.copy()
                new_sequence[sequence_length] = transition
                stack.append((next_state, sequence_length + 1, new_sequence))
    return sequences


@cc.export('dijkstra', types.Tuple((int64[::1], int64[:, :, ::1]))(int64[::1], int64, int64[:, ::1], int64[:, ::1]))
def dijkstra(src, size, adj_matrix, mask):
    N = size
    Nsq = size ** 2
    maxsize = sys.maxsize

    dist = np.full(Nsq, maxsize, dtype=np.int64)
    src_idx = src[0] * N + src[1]
    dist[src_idx] = 0

    open_set = np.zeros(Nsq, dtype=np.bool_)
    adj = (adj_matrix * mask).astype(np.int64)

    pq = [(0, src_idx)]

    shortest_paths = np.full((N, N, 2), -1, dtype=np.int64)

    while len(pq) > 0:
        current_dist, x = heapq.heappop(pq)
        if open_set[x]:
            continue
        open_set[x] = True

        from_x = x // N
        from_y = x % N

        for y in range(Nsq):
            if adj[x, y] > 0 and not open_set[y]:
                to_x = y // N
                to_y = y % N
                new_dist = dist[x] + adj[x, y]

                if dist[y] > new_dist:
                    dist[y] = new_dist
                    shortest_paths[to_x, to_y] = np.array([from_x, from_y], dtype=np.int64)
                    heapq.heappush(pq, (new_dist, y))
                elif dist[y] == new_dist:
                    # Check for the least zig-zaggy path
                    current_path_diff = np.sum(np.abs(shortest_paths[to_x, to_y] - np.array([to_x, to_y], dtype=np.int64)))
                    new_path_diff = np.sum(np.abs(np.array([to_x, to_y], dtype=np.int64) - np.array([from_x, from_y], dtype=np.int64)))
                    if current_path_diff > new_path_diff:
                        shortest_paths[to_x, to_y] = np.array([from_x, from_y], dtype=np.int64)
                        heapq.heappush(pq, (new_dist, y))

    return dist, shortest_paths


@njit
@cc.export('is_empty_or_self', boolean(types.Array(types.Record([('combatant', {'type': int64, 'offset': 0, 'alignment': None, 'title': None, }), ('terrain', {'type': int32, 'offset': 8, 'alignment': None, 'title': None, }), ('occupancy', {'type': int32, 'offset': 12, 'alignment': None, 'title': None, })], 16, False), 2, 'C', False, aligned=False), int64, int64, int64))
def is_empty_or_self(grid, x, y, combatant_id):
    """Check if the grid square is empty or occupied by the given combatant."""
    square = grid[x, y]
    return ((square['occupancy'] == Occupancy.FREE.value) or (combatant_id != -1 and square['combatant'] == combatant_id)) and (square['terrain'] != Terrain.IMPASSABLE_TERRAIN.value)


@njit
@cc.export('inflate_coords', (types.Array(int64, 2, 'C', False, aligned=True), int64))
def inflate_coords(coords: np.array, inflate_to_dist):
    """
    A helper function which inflates the given numpy array coordinates to a given size (they may already by inflated but may need further inflation
    due to the size of the other combatant).
    :param coords: target combatant coordinates
    :param inflate_to_dist: size of the other combatant
    :return: inflated set of coordinates (as x, y tuples)
    """
    offset = 0
    if inflate_to_dist > Size.MEDIUM.value:
        offset = inflate_to_dist

    inflated = set()
    for coord in coords:
        for x, y in [(x, y) for x in range(coord[0] - offset, coord[0] + 1) for y in range(coord[1] - offset, coord[1] + 1)]:
            inflated.add((max(0, x), max(0, y)))
    return inflated


@njit
@cc.export('distance_matrix', float64[:, :](types.Array(int64, 2, 'C', False, aligned=True), types.Array(int64, 2, 'C', False, aligned=True)))
def distance_matrix(coords1, coords2):
    """
    Computes the pairwise Euclidean distances between two sets of coordinates.
    :param coords1: numpy array of shape (n, 2)
    :param coords2: numpy array of shape (m, 2)
    :return: numpy array of shape (n, m) containing cartesian distances
    """
    n = coords1.shape[0]
    m = coords2.shape[0]
    distances = np.zeros((n, m))

    for i in range(n):
        for j in range(m):
            distances[i, j] = np.sqrt((coords1[i, 0] - coords2[j, 0]) ** 2 + (coords1[i, 1] - coords2[j, 1]) ** 2)

    return distances

@njit
@cc.export('get_cartesian_distance_coords', float64(types.Array(int64, 2, 'C', False, aligned=True), types.Array(int64, 2, 'C', False, aligned=True)))
def get_cartesian_distance_coords(coords1, coords2):
    """
    Calculates the cartesian distance between two coordinates
    :param coords1:
    :param coords2:
    :return: cartesian distance between two sets of coords, None if one of the subjects is dead
    """
    return np.amin(distance_matrix(coords1, coords2))


@njit
@cc.export('get_hop_distance_coords', float64(types.Array(int64, 2, 'C', False, aligned=True), types.Array(int64, 2, 'C', False, aligned=True)))
def get_hop_distance_coords(coords1, coords2):
    """
    Calculates hop distance between coords
    :param coords1:
    :param coords2:
    :return: distance between two sets of coords in number of hops, None if one of the subjects is dead
    """
    dist_mat = distance_matrix(coords1, coords2)
    min_dist_index = np.argmin(dist_mat)  # find the index closest distance between the two sets of points
    sub1_closest_coord = coords1[min_dist_index // dist_mat.shape[1], :]
    sub2_closest_coord = coords2[min_dist_index % dist_mat.shape[1], :]
    return np.max(np.abs(sub1_closest_coord - sub2_closest_coord))


@cc.export('get_free_coords_at_hop_range', types.List(types.UniTuple(int64, 2))(
    types.Array(types.Record([('combatant', {'type': int64, 'offset': 0, 'alignment': None, 'title': None, }), ('terrain', {'type': int32, 'offset': 8, 'alignment': None, 'title': None, }), ('occupancy', {'type': int32, 'offset': 12, 'alignment': None, 'title': None, })], 16, False), 2, 'C', False, aligned=False),
    types.Array(int64, 2, 'C', False, aligned=True),
    types.Array(int64, 1, 'C', False, aligned=True),
    int64,
    int64,
    int64))
def get_free_coords_at_hop_range(
        grid,
        coords,
        distances: np.ndarray = np.array([], dtype=np.float64),
        inflate_to_dist: int = Size.MEDIUM.value,
        rng: int = 1,
        combatant_id: int = -1
):
    """
    Returns coordinates exactly at 'rng' distance from the nearest edge of an area occupied by a combatant, considering combatant size for pathfinding.
    :param grid: the map numpy array grid
    :param coords: target combatant coordinates
    :param distances: the distances to all squares (result of Dijkstra) to recognize accessibility of coordinates
    :param inflate_to_dist: inflate for the sake of pathfinding by larger combatants
    :param rng: exact range of what is considered 'adjacent'
    :param combatant_id: optional unique combatant id which is to be considered 'self' for the sake of is_empty_or_self
    :return: coordinates exactly at 'rng' distance as a set of tuples (x, y)
    """
    assert rng > 0
    size = grid.shape[0]
    inflated = inflate_coords(coords, inflate_to_dist)
    perimeter_coords = set()

    # Calculate bounds of the inflated area without using generator expressions
    min_x = size
    max_x = 0
    min_y = size
    max_y = 0

    for coord in inflated:
        if coord[0] < min_x:
            min_x = coord[0]
        if coord[0] > max_x:
            max_x = coord[0]
        if coord[1] < min_y:
            min_y = coord[1]
        if coord[1] > max_y:
            max_y = coord[1]

    min_x -= rng
    max_x += rng
    min_y -= rng
    max_y += rng

    # Generate perimeter coordinates at exactly rng distance
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            # Check if (x, y) is on the perimeter of the inflated area at rng distance
            if x == min_x or x == max_x or y == min_y or y == max_y:
                if 0 <= x < size and 0 <= y < size:  # Check boundaries
                    accessible = (distances[x * size + y] < sys.maxsize) if distances.size > 0 else True
                    if is_empty_or_self(grid, x, y, combatant_id) and accessible:
                        perimeter_coords.add((x, y))

    return list(perimeter_coords)


@cc.export('get_free_coords_in_hop_range', types.List(types.UniTuple(int64, 2))(
    types.Array(types.Record([('combatant', {'type': int64, 'offset': 0, 'alignment': None, 'title': None, }), ('terrain', {'type': int32, 'offset': 8, 'alignment': None, 'title': None, }), ('occupancy', {'type': int32, 'offset': 12, 'alignment': None, 'title': None, })], 16, False), 2, 'C', False, aligned=False),
    types.Array(int64, 2, 'C', False, aligned=True),
    types.Array(int64, 1, 'C', False, aligned=True),
    int64,
    int64,
    int64))
def get_free_coords_in_hop_range(
        grid: np.ndarray,
        coords: np.ndarray,
        distances: np.ndarray = np.array([], dtype=np.float64),
        inflate_to_dist: int = Size.MEDIUM.value,
        rng: int = 1,
        combatant_id: int = -1
):
    """
    Returns free squares coordinates adjacent (up to the range distance) to a given coordinate that can be occupied
    by a combatant of 'inflate_to_dist' size.
    :param grid: the map numpy array grid
    :param coords: target combatant coordinates
    :param distances: the distances to all squares (result of Dijkstra) to be able to recognize accessibility of coordinates
    :param inflate_to_dist: inflate for the sake of pathfinding BY larger combatants
    :param rng: maximum range of what is considered 'adjacent'
    :param combatant_id: optional unique combatant id which is to be considered 'self' for the sake of is_empty_or_self
    :return: free adjacent coordinates as a set of tuples (x, y)
    """
    assert rng > 0
    size = grid.shape[0]
    inflated = inflate_coords(coords, inflate_to_dist)

    adjacent_coords = set()
    for coord in inflated:
        for x, y in [(coord[0] + i, coord[1] + j) for i in range(-rng, rng + 1) for j in range(-rng, rng + 1)]:
            if x < 0 or x >= size or y < 0 or y >= size:
                continue
            consider_accesibility = (distances[x * size + y] < sys.maxsize) if distances.size > 0 else True
            if is_empty_or_self(grid, x, y, combatant_id) and consider_accesibility:# and (x, y) not in inflated:
                # have to use tuples since np.array is unhashable
                adjacent_coords.add((x, y))
    return list(adjacent_coords)


@cc.export('get_free_coords_in_cartesian_range', types.List(types.UniTuple(int64, 2))(
    types.Array(types.Record([('combatant', {'type': int64, 'offset': 0, 'alignment': None, 'title': None, }), ('terrain', {'type': int32, 'offset': 8, 'alignment': None, 'title': None, }), ('occupancy', {'type': int32, 'offset': 12, 'alignment': None, 'title': None, })], 16, False), 2, 'C', False, aligned=False),
    types.Array(int64, 2, 'C', False, aligned=True),
    types.Array(int64, 1, 'C', False, aligned=True),
    int64,
    int64,
    int64))
def get_free_coords_in_cartesian_range(
        grid: np.ndarray,
        coords: np.ndarray,
        distances: np.ndarray = np.array([], dtype=np.float64),
        inflate_to_dist: int = Size.MEDIUM.value,
        rng: int = 1,
        combatant_id: int = -1
):
    """
    Returns free square coordinates that are at the most rng away from the coords as measured by cartesian distance that can be occupied
    by a combatant of 'inflate_to_dist' size. It's pretty much the same as get_free_coords_in_hop_range but it uses the rng as a
    bounding box to narrow down the search.
    :param grid: the map numpy array grid
    :param coords: target combatant or destination coordinates
    :param distances: the distances to all squares (result of Dijkstra) to be able to recognize accessibility of coordinates
    :param inflate_to_dist: inflate for the sake of pathfinding BY larger combatants (as opposed to TO larger combatants)
    :param rng: maximum range
    :param combatant_id: optional unique combatant id which is to be considered 'self' for the sake of is_empty_or_self
    :return: free adjacent coordinates as a set of tuples (x, y)
    """
    assert rng > 0
    size = grid.shape[0]
    # First inflate it by the size of the combatant looking for the path
    inflated = inflate_coords(coords, inflate_to_dist)

    coords_in_range = set()
    for coord in inflated:
        # the rng can be used as a bounding box for the search
        for x, y in [(coord[0] + i, coord[1] + j) for i in range(-rng, rng + 1) for j in range(-rng, rng + 1)]:
            if x < 0 or x >= size or y < 0 or y >= size or get_cartesian_distance_coords(coords, np.array([[x, y]], dtype=np.int64)) > rng:
                continue
            consider_accessibility = (distances[x * size + y] < sys.maxsize) if distances.size > 0 else True
            if is_empty_or_self(grid, x, y, combatant_id) and consider_accessibility:# and (x, y) not in inflated:
                # have to use tuples since np.array is unhashable
                coords_in_range.add((x, y))
    return list(coords_in_range)


@cc.export('angle_between_vectors', float64(types.Array(float64, 1, 'C', False, aligned=True), types.Array(float64, 1, 'C', False, aligned=True)))
def angle_between_vectors(vector_1, vector_2):
    """
    Calculates the angle (in degrees) between two vectors
    :param vector_1: The first vector
    :param vector_2: The second vector
    :return: The convex angle (in degrees) formed by the two vectors.
    """
    dot_prod = np.dot(vector_1, vector_2)
    mag_1 = np.sqrt(np.dot(vector_1, vector_1))
    mag_2 = np.sqrt(np.dot(vector_2, vector_2))
    angle_rad = np.arccos(np.maximum(-1.0, np.minimum(dot_prod / (mag_1 * mag_2), 1.0)))
    angle_deg = np.degrees(angle_rad) % 360
    return angle_deg if (angle_deg - 180.0 < 0) else 360.0 - angle_deg


@cc.export('angle_between_vectors_int', float64(types.Array(int64, 1, 'C', False, aligned=True), types.Array(int64, 1, 'C', False, aligned=True)))
def angle_between_vectors_int(vector_1, vector_2):
    """
    Calculates the angle (in degrees) between two vectors
    :param vector_1: The first vector
    :param vector_2: The second vector
    :return: The convex angle (in degrees) formed by the two vectors.
    """
    # Ensure the vectors are floats
    vector_1 = vector_1.astype(np.float64)
    vector_2 = vector_2.astype(np.float64)

    dot_prod = np.dot(vector_1, vector_2)
    mag_1 = np.sqrt(np.dot(vector_1, vector_1))
    mag_2 = np.sqrt(np.dot(vector_2, vector_2))
    angle_rad = np.arccos(np.maximum(-1.0, np.minimum(dot_prod / (mag_1 * mag_2), 1.0)))
    angle_deg = np.degrees(angle_rad) % 360
    return angle_deg if (angle_deg - 180.0 < 0) else 360.0 - angle_deg


@cc.export('avg_roll', float64(types.UniTuple(int32, 2)))
def avg_roll(dice: tuple):
    return dice[0] * ((1.0 + dice[1]) / 2.0)


@cc.export('get_bounding_box', types.UniTuple(types.Array(int64, 1, 'C', False, aligned=True), 2)(types.Array(int64, 2, 'C', False, aligned=True), types.Array(int64, 2, 'C', False, aligned=True)))
def get_bounding_box(combatant1, combatant2):
    """
    Calculates a bounding box which encloses both combatants
    :param combatant1: np.ndarray with shape (N, 2)
    :param combatant2: np.ndarray with shape (M, 2)
    :return: bottom left corner, top right corner
    """
    # Initialize min and max values with the first point of combatant1
    min_x = combatant1[0, 0]
    min_y = combatant1[0, 1]
    max_x = combatant1[0, 0]
    max_y = combatant1[0, 1]

    # Compute min and max for combatant1
    for i in range(combatant1.shape[0]):
        if combatant1[i, 0] < min_x:
            min_x = combatant1[i, 0]
        if combatant1[i, 1] < min_y:
            min_y = combatant1[i, 1]
        if combatant1[i, 0] > max_x:
            max_x = combatant1[i, 0]
        if combatant1[i, 1] > max_y:
            max_y = combatant1[i, 1]

    # Compute min and max for combatant2
    for i in range(combatant2.shape[0]):
        if combatant2[i, 0] < min_x:
            min_x = combatant2[i, 0]
        if combatant2[i, 1] < min_y:
            min_y = combatant2[i, 1]
        if combatant2[i, 0] > max_x:
            max_x = combatant2[i, 0]
        if combatant2[i, 1] > max_y:
            max_y = combatant2[i, 1]

    bottom_left = np.array([min_x, min_y], dtype=np.int64)
    top_right = np.array([max_x, max_y], dtype=np.int64)

    return bottom_left, top_right


@cc.export('roll_dice_with_reroll_and_log', (types.UniTuple(int64, 2), int64))
def roll_dice_with_reroll_and_log(dice, reroll_max_value):
    """
    Function for rolling dice which re-rolls results less than or equal to a given value. The re-rolled value must be used.
    @param dice: tuple of (# of dice (1..inf), dice size (4, 6, 8, 10, 12))
    @param reroll_max_value: the maximum die value to be rerolled
    @return: tuple of (sum of dice rolls after rerolls, list of tuples of (original roll, reroll) for logging)
    """
    num_dice, dice_size = dice
    dice_sum = 0
    reroll_log = []

    for _ in range(num_dice):
        rolled = np.random.randint(1, dice_size + 1)
        if rolled <= reroll_max_value:
            rerolled = np.random.randint(1, dice_size + 1)
            reroll_log.append((rolled, rerolled))
            rolled = rerolled
        dice_sum += rolled

    return dice_sum, reroll_log


@cc.export('is_path_straight', boolean(types.Array(int64, 2, 'C', False, aligned=True), int64))
def is_path_straight(path, length):
    if path is None or len(path) < 2 or length < 2:
        return False
    if length > len(path):
        return False

    # Extract the relevant sub-path
    sub_path = path[-length:]
    # Compare the direction of each step in the sub-path
    direction = None
    for i in range(len(sub_path) - 1):
        current_direction = sub_path[i + 1] - sub_path[i]
        if direction is None:
            direction = current_direction
        else:
            # Manual comparison instead of np.array_equal
            if not (direction[0] == current_direction[0] and direction[1] == current_direction[1]):
                return False
    return True


if __name__ == "__main__":
    cc.compile()
