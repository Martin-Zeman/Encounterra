import math
from simulator.battle_map import *
import numpy as np


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

def get_affected_by_sphere(origin, radius, grid_size):
    """
    Gets coordinates of grid squares affected by a spheric effect originating at the center of a square at origin coordinates.
    :param origin:
    :param radius: radius of the sphere in grid coordinates
    :param grid_size: size of the grid
    :return: affected coordinates as a list of np.array
    """
    coords = []
    origin_center = get_square_center(origin)
    for x, y in [(origin[0] + i, origin[1] + j) for i in range(-radius, radius + 1) for j in range(-radius, radius + 1)]:
        if x < 0 or x >= grid_size or y < 0 or y >= grid_size:
            continue
        curr_coord_center = get_square_center(np.array([x, y]))
        if np.linalg.norm(origin_center - curr_coord_center) <= radius:
            coords.append(np.array([x, y]))
    return coords

def get_affected_by_square(origin, length, grid_size):
    """
    Gets coordinates of grid squares affected by a square effect originating at bottom left corner of a square at origin coordinates.
    :param origin:
    :param length: length of the square side
    :param grid_size: size of the grid
    :return: affected coordinates as a list of np.array
    """
    coords = []
    for x, y in [(origin[0] + i, origin[1] + j) for i in range(1, length + 1) for j in range(1, length + 1)]:
        if x < 0 or x >= grid_size or y < 0 or y >= grid_size:
            continue
        coords.append(np.array([x, y]))
    return coords

def do_squares_overlap(origin1, length1, origin2, length2):
    """
    Given two squares represented by their origin (bottom-left corner) and their length, return if they overlap
    :param origin1: origin of the first square
    :param length1: side length of the first square
    :param origin2: origin of the second square
    :param length2: side length of the second square
    :return: True if they overlap, false otherwise
    """
    return (origin1[0] < (origin2[0] + length2) and (origin1[0] + length1) > origin2[0]) and (origin1[1] < (origin2[1] + length2) and (origin1[1] + length1) > origin2[1])

# def get_cartesian_distance(coord1, coord2):
#     return np.linalg.norm(coord1 - coord2)