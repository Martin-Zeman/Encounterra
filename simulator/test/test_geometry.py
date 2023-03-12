from simulator.geometry import *
from simulator.spells.spell import *
import numpy as np


def test_cone_15_feet():
    coords = get_affected_by_cone(origin=np.array([2, 0]), angle_deg=45, radius=SpellStats.TRANSLATE_CONE[SpellStats.Target.CONE_15],
                                  grid_size=15)
    expected_coords = {(3, 1), (4, 1), (3, 2), (4, 2)}
    assert coords == expected_coords

    coords = get_affected_by_cone(origin=np.array([2, 0]), angle_deg=29, radius=SpellStats.TRANSLATE_CONE[SpellStats.Target.CONE_15],
                                  grid_size=15)
    expected_coords = {(2, 1), (3, 1), (2, 2), (3, 2), (4, 2)}
    assert coords == expected_coords

    coords = get_affected_by_cone(origin=np.array([2, 0]), angle_deg=0, radius=SpellStats.TRANSLATE_CONE[SpellStats.Target.CONE_15],
                                  grid_size=15)
    expected_coords = {(2, 1), (2, 2), (1, 2), (3, 2)}
    assert coords == expected_coords

    coords = get_affected_by_cone(origin=np.array([2, 0]), angle_deg=30, radius=SpellStats.TRANSLATE_CONE[SpellStats.Target.CONE_15],
                                  grid_size=15)
    expected_coords = {(2, 1), (2, 2), (3, 1), (3, 2), (4, 2)}
    assert coords == expected_coords


def test_cone_30_feet():
    coords = get_affected_by_cone(origin=np.array([4, 7]), angle_deg=180, radius=SpellStats.TRANSLATE_CONE[SpellStats.Target.CONE_30], grid_size=15)
    expected_coords = {(2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (3, 2), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3), (3, 4), (4, 4), (5, 4),
                       (3, 5), (4, 5), (5, 5), (4, 6)}
    assert coords == expected_coords

    coords = get_affected_by_cone(origin=np.array([1, 4]), angle_deg=90, radius=SpellStats.TRANSLATE_CONE[SpellStats.Target.CONE_30], grid_size=15)
    expected_coords = {(2, 4), (3, 3), (3, 4), (3, 5), (4, 3), (4, 4), (4, 5), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (6, 2), (6, 3),
                       (6, 4), (6, 5), (6, 6)}
    assert coords == expected_coords

    coords = get_affected_by_cone(origin=np.array([7, 4]), angle_deg=270, radius=SpellStats.TRANSLATE_CONE[SpellStats.Target.CONE_30], grid_size=15)
    expected_coords = {(2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (4, 3), (4, 4), (4, 5), (5, 3),
                       (5, 4), (5, 5), (6, 4)}
    assert coords == expected_coords


def test_do_squares_overlap():
    # A up and to the left of B
    assert do_squares_overlap(np.array([2, 5]), 3, np.array([4, 4]), 3)
    assert do_squares_overlap(np.array([2, 5]), 3, np.array([4, 4]), 2)
    assert not do_squares_overlap(np.array([2, 5]), 3, np.array([4, 4]), 1)
    assert not do_squares_overlap(np.array([2, 5]), 2, np.array([4, 4]), 3)
    assert not do_squares_overlap(np.array([2, 5]), 1, np.array([4, 4]), 3)

    # A up and to the right of B
    assert do_squares_overlap(np.array([4, 3]), 3, np.array([2, 1]), 3)
    assert do_squares_overlap(np.array([4, 3]), 2, np.array([2, 1]), 3)
    assert do_squares_overlap(np.array([4, 3]), 1, np.array([2, 1]), 3)
    assert not do_squares_overlap(np.array([4, 3]), 3, np.array([2, 1]), 2)
    assert not do_squares_overlap(np.array([4, 3]), 3, np.array([2, 1]), 1)

    # A down and to the right of B
    assert do_squares_overlap(np.array([3, 3]), 3, np.array([2, 4]), 3)
    assert do_squares_overlap(np.array([3, 3]), 3, np.array([2, 4]), 2)
    assert not do_squares_overlap(np.array([3, 3]), 3, np.array([2, 4]), 1)
    assert do_squares_overlap(np.array([3, 3]), 2, np.array([2, 4]), 2)
    assert do_squares_overlap(np.array([3, 3]), 2, np.array([2, 4]), 3)
    assert not do_squares_overlap(np.array([3, 3]), 1, np.array([2, 4]), 3)

    # A down and to the left of B
    assert do_squares_overlap(np.array([2, 2]), 3, np.array([4, 4]), 3)
    assert do_squares_overlap(np.array([2, 2]), 3, np.array([4, 4]), 2)
    assert do_squares_overlap(np.array([2, 2]), 3, np.array([4, 4]), 1)
    assert not do_squares_overlap(np.array([2, 2]), 2, np.array([4, 4]), 3)
    assert not do_squares_overlap(np.array([2, 2]), 1, np.array([4, 4]), 3)
