import math

import numpy as np

from .combatant_coords import Coords
from .obstacle import Obstacle


def get_square_center(coord):
    return coord + np.array([0.5, 0.5])


def get_affected_by_cone(origin, angle_deg, radius, grid_size):
    """
    Gets coordinates of grid squares affected by a cone effect originating at the center of a square at origin coordinates.
    :param origin:
    :param angle_deg: yaw angle of the cone, marks the center line through the cone, north clock-wise oriented
    :param radius: radius of the cone in grid coordinates
    :param grid_size: size of the grid
    :return: affected coordinates
    """
    origin_center = get_square_center(origin)
    line_increment = lambda angle: np.array([origin_center[0] + radius * math.sin(angle), origin_center[1] + radius * math.cos(angle)])
    # determinant of (AB, AQ) where A is origin, B is line_point and Q is query point
    polarity = lambda line_point, query_point: np.linalg.det([line_point - origin_center, query_point - origin_center])

    first_angle = angle_deg - 30
    first_angle_rad = math.radians(first_angle)
    first_line_point = line_increment(first_angle_rad)

    second_angle = angle_deg + 30
    second_angle_rad = math.radians(second_angle)
    second_line_point = line_increment(second_angle_rad)

    coords = set()
    for x in range(0, grid_size):
        for y in range(0, grid_size):
            curr_coord_center = get_square_center(np.array([x, y]))
            if np.linalg.norm(
                    origin_center - curr_coord_center) < radius and polarity(first_line_point, curr_coord_center) <= 0 and polarity(
                second_line_point, curr_coord_center) >= 0:
                # if they lie on the opposite half-planes of the two lines their product is negative which means the coordinate lies in
                # between the cone lines
                coords.add((x, y))

    try:
        coords.remove((origin[0], origin[1]))
    except KeyError:
        pass

    # approximation of an  > 1/2 of area covered for the corners of the cone
    first_corner_decimal = np.modf(first_line_point)
    if first_corner_decimal[0][0] >= 0.5 or first_corner_decimal[0][1] <= 0.5:
        try:
            coords.remove((math.floor(first_line_point[0]), math.floor(first_line_point[1])))
        except KeyError:
            pass
    second_corner_decimal = np.modf(second_line_point)
    if second_corner_decimal[0][0] <= 0.5 or second_corner_decimal[0][1] <= 0.5:
        try:
            coords.remove((math.floor(second_line_point[0]), math.floor(second_line_point[1])))
        except KeyError:
            pass
    return coords


def do_squares_overlap(origin1: np.array, length1, origin2: np.array, length2):
    """
    Given two squares represented by their origin (bottom-left corner) and their length, return if they overlap
    :param origin1: origin of the first square
    :param length1: side length of the first square
    :param origin2: origin of the second square
    :param length2: side length of the second square
    :return: True if they overlap, false otherwise
    """
    return (origin1[0] < (origin2[0] + length2) and (origin1[0] + length1) > origin2[0]) and (origin1[1] < (origin2[1] + length2) and (origin1[1] + length1) > origin2[1])


def angle_between_vectors(vector_1: np.array, vector_2: np.array):
    """
    Calculates the angle (in degrees) between two points and a given center point
    :param point1: The first vector
    :param point2: The second vector
    :return: The convex angle (in degrees) formed by the two vectors.
    """
    dot_prod = np.dot(vector_1, vector_2)
    mag_1 = np.dot(vector_1, vector_1)**0.5
    mag_2 = np.dot(vector_2, vector_2)**0.5
    angle_rad = math.acos(max(-1.0, min(dot_prod / mag_2 / mag_1, 1.0)))
    angle_deg = math.degrees(angle_rad) % 360
    return angle_deg if (angle_deg - 180 < 0) else 360 - angle_deg


def find_fov_vectors(observer: Coords, target: Coords | Obstacle):
    """
    Calculates the field of view vector from right and leftmost points of a target from the perspective of the observer
    :param observer: observer coordinates
    :param target: target coordinates
    :return: normalized vectors to the left and right most points from the observer's perspective ordered in counter-clockwise manner
    (using the convex angle they define)
    """
    observer_center = observer.get_center()
    target_center = target.get_center()
    vectors = sorted([(c - observer_center, angle_between_vectors(target_center - observer_center, c - observer_center)) for c in target.get_corners()], key=lambda x: x[1], reverse=True)
    assert len(vectors) > 1
    if np.cross(vectors[0][0], vectors[1][0]) > 0:
        return vectors[0][0] / np.linalg.norm(vectors[0][0]), vectors[1][0] / np.linalg.norm(vectors[1][0])
    return vectors[1][0] / np.linalg.norm(vectors[1][0]), vectors[0][0] / np.linalg.norm(vectors[0][0])


def get_bounding_box(combatant1: Coords, combatant2: Coords):
    """
    Calculates a bounding box which encloses both combatants
    :param combatant1:
    :param combatant2:
    :return: bottom left corner, top right corner
    """
    combined = np.concatenate((combatant1.get(), combatant2.get()), axis=0)
    bottom_left = np.min(combined, axis=0)
    top_right = np.max(combined, axis=0)
    return bottom_left, top_right
