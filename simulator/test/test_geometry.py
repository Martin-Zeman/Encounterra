from simulator.geometry import *
from simulator.spells.spell import *
import numpy as np
import pytest

def test_cone():
    origin = np.array([2, 0])
    grid_size = 15
    # coords = get_affected_by_cone(origin, 45, Spell.TRANSLATE_CONE[Spell.Target.CONE_15], grid_size)
    # coords_det = get_affected_by_cone_det(origin, 45, Spell.TRANSLATE_CONE[Spell.Target.CONE_15], grid_size)
    # expected_coords = {(3, 1), (4, 1), (3, 2), (4, 2)}
    # assert coords == expected_coords
    # assert coords == coords_det
    #
    # coords = get_affected_by_cone(origin, 29, Spell.TRANSLATE_CONE[Spell.Target.CONE_15], grid_size)
    # coords_det = get_affected_by_cone_det(origin, 29, Spell.TRANSLATE_CONE[Spell.Target.CONE_15], grid_size)
    # expected_coords = {(2, 1), (3, 1), (4, 2), (2, 3), (2, 2), (3, 2)}
    # assert coords == expected_coords
    # assert coords == coords_det
    #
    # coords = get_affected_by_cone(origin, 0, Spell.TRANSLATE_CONE[Spell.Target.CONE_15], grid_size)
    # coords_det = get_affected_by_cone_det(origin, 0, Spell.TRANSLATE_CONE[Spell.Target.CONE_15], grid_size)
    # expected_coords = {(2, 1), (2, 2), (2, 3), (1, 2), (3, 2)}
    # assert coords == expected_coords
    # assert coords == coords_det

    coords = get_affected_by_cone_det(origin, 30, Spell.TRANSLATE_CONE[Spell.Target.CONE_15], grid_size)
    expected_coords = {(2, 1), (1, 1), (1, 2), (2, 2), (1, 3), (2, 3)}
    assert coords == expected_coords