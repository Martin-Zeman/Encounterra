import pytest

from simulator.geometry import *
from simulator.misc import Size
from simulator.spells.spell import *
import numpy as np
from simulator.test.fixtures import test_stone_giant, test_ogre, test_bugbear


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

def test_angle_between_vectors():
    assert angle_between_vectors(np.array([0, 1]), np.array([1, 0])) == pytest.approx(90.0, 0.0001)
    assert angle_between_vectors(np.array([0, 1]), np.array([1, -1])) == pytest.approx(135.0, 0.0001)
    assert angle_between_vectors(np.array([0, 1]), np.array([0, -1])) == pytest.approx(180.0, 0.0001)
    assert angle_between_vectors(np.array([0, 2]), np.array([-1, 2])) == pytest.approx(26.5650, 0.0001)
    assert angle_between_vectors(np.array([1, 0.5]), np.array([1.5, -1])) == pytest.approx(60.2551, 0.0001)
    assert angle_between_vectors(np.array([6, 4]), np.array([6, 4])) == pytest.approx(0, 0.0001)
    assert angle_between_vectors(np.array([0, 4]), np.array([4, 4])) == pytest.approx(45.0, 0.0001)


def test_find_fov_vectors(test_stone_giant, test_ogre, test_bugbear):
    # Directly side by side
    outlines = find_fov_vectors(Coords(np.array([3, 7]), test_bugbear.size), Coords(np.array([6, 6]), test_stone_giant.size))
    assert len(outlines) == 2
    assert any([np.array_equal(np.array([2.5, 1.5]) / np.linalg.norm(np.array([2.5, 1.5])), point) for point in outlines])
    assert any([np.array_equal(np.array([2.5, -1.5]) / np.linalg.norm(np.array([2.5, -1.5])), point) for point in outlines])
    # Same but observer and target swapped
    outlines = find_fov_vectors(Coords(np.array([6, 6]), test_stone_giant.size), Coords(np.array([3, 7]), test_bugbear.size))
    assert len(outlines) == 2
    assert any([np.array_equal(np.array([-3.5, 0.5]) / np.linalg.norm(np.array([-3.5, 0.5])), point) for point in outlines])
    assert any([np.array_equal(np.array([-3.5, -0.5]) / np.linalg.norm(np.array([-3.5, 0.5])), point) for point in outlines])
    # At a slight angle
    outlines = find_fov_vectors(Coords(np.array([0, 0]), test_stone_giant.size), Coords(np.array([5, 2]), test_ogre.size))
    assert len(outlines) == 2
    assert any([np.array_equal(np.array([3.5, 2.5]) / np.linalg.norm(np.array([3.5, 2.5])), point) for point in outlines])
    assert any([np.array_equal(np.array([5.5, 0.5]) / np.linalg.norm(np.array([5.5, 0.5])), point) for point in outlines])
    # Testing the breaking point between the selection of (6, 9) and (6, 6)
    outlines = find_fov_vectors(Coords(np.array([5, 2]), test_bugbear.size), Coords(np.array([6, 6]), test_stone_giant.size))
    assert len(outlines) == 2
    assert any([np.array_equal(np.array([3.5, 3.5]) / np.linalg.norm(np.array([3.5, 3.5])), point) for point in outlines])
    assert any([np.array_equal(np.array([0.5, 6.5]) / np.linalg.norm(np.array([0.5, 6.5])), point) for point in outlines])
    outlines = find_fov_vectors(Coords(np.array([6, 2]), test_bugbear.size), Coords(np.array([6, 6]), test_stone_giant.size))
    assert len(outlines) == 2
    assert any([np.array_equal(np.array([-0.5, 3.5]) / np.linalg.norm(np.array([-0.5, 3.5])), point) for point in outlines])
    assert any([np.array_equal(np.array([2.5, 3.5]) / np.linalg.norm(np.array([2.5, 3.5])), point) for point in outlines])



def test_get_bounding_box():
    # Test case 1: Two combatants with same size
    coord1 = Coords(np.array([1, 1]), Size.MEDIUM)
    coord2 = Coords(np.array([3, 3]), Size.MEDIUM)
    bottom_left, top_right = get_bounding_box(coord1, coord2)
    assert np.array_equal(bottom_left, np.array([1, 1]))
    assert np.array_equal(top_right, np.array([3, 3]))

    # Test case 2: Two combatants with different sizes
    coord1 = Coords(np.array([0, 0]), Size.SMALL)
    coord2 = Coords(np.array([4, 4]), Size.LARGE)
    bottom_left, top_right = get_bounding_box(coord1, coord2)
    assert np.array_equal(bottom_left, np.array([0, 0]))
    assert np.array_equal(top_right, np.array([5, 5]))

    # Test case 3: Two combatants with overlapping positions
    coord1 = Coords(np.array([2, 2]), Size.HUGE)
    coord2 = Coords(np.array([3, 3]), Size.GARGANTUAN)
    bottom_left, top_right = get_bounding_box(coord1, coord2)
    assert np.array_equal(bottom_left, np.array([2, 2]))
    assert np.array_equal(top_right, np.array([6, 6]))

    # Test case 4: Two combatants with same position
    coord1 = Coords(np.array([0, 0]), Size.TINY)
    coord2 = Coords(np.array([0, 0]), Size.TINY)
    bottom_left, top_right = get_bounding_box(coord1, coord2)
    assert np.array_equal(bottom_left, np.array([0, 0]))
    assert np.array_equal(top_right, np.array([0, 0]))

    # Test case 5: HUGE and LARGE
    coords1 = Coords(np.array([1, 11]), Size.HUGE)
    coords2 = Coords(np.array([9, 13]), Size.LARGE)
    bottom_left, top_right = get_bounding_box(coords1, coords2)
    assert np.array_equal(np.array([1, 11]), bottom_left)
    assert np.array_equal(np.array([10, 14]), top_right)
