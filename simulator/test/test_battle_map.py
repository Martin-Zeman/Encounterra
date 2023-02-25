from simulator.battle_map import Map
from simulator.combatants.faurung import Faurung
from simulator.combatants.goblin import Goblin
from simulator.effects.effect_tracker import EffectTracker
from simulator.misc import DistanceMetric
from simulator.teams import Teams
import numpy as np
import pytest

@pytest.fixture()
def teams():
    return Teams()

@pytest.fixture()
def effect_tracker():
    return EffectTracker()

@pytest.fixture()
def battle_map(teams):
    return Map(15, teams)

@pytest.fixture()
def combatant1(effect_tracker):
    return Faurung(effect_tracker, "Faurung")

@pytest.fixture()
def combatant2(effect_tracker):
    return Goblin(effect_tracker, "Goblin")

def test_as_if_combatant_position(teams, effect_tracker, battle_map, combatant1, combatant2):
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)

    battle_map.set_combatant_coordinates(combatant1, np.array([5, 7]))
    battle_map.set_combatant_coordinates(combatant2, np.array([10, 7]))

    assert battle_map.get_cartesian_distance(combatant1, combatant2) == 5
    with battle_map.as_if_combatant_position(combatant1, np.array([9, 7])):
        assert battle_map.get_cartesian_distance(combatant1, combatant2) == 1
    assert battle_map.get_cartesian_distance(combatant1, combatant2) == 5
    with battle_map.as_if_combatant_position(combatant1, np.array([0, 7])):
        assert battle_map.get_cartesian_distance(combatant1, combatant2) == 10
    assert battle_map.get_cartesian_distance(combatant1, combatant2) == 5

def test_as_if_dist_from_combatant(teams, effect_tracker, battle_map, combatant1, combatant2):
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    combatant3 = Goblin(effect_tracker, "Goblin 2")
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)

    battle_map.set_combatant_coordinates(combatant1, np.array([5, 7]))
    battle_map.set_combatant_coordinates(combatant2, np.array([10, 7]))
    battle_map.set_combatant_coordinates(combatant3, np.array([4, 7]))
    # establish baseline
    assert battle_map.get_hop_distance(combatant1, combatant2) == 5
    assert battle_map.get_hop_distance(combatant1, combatant3) == 1
    # now test that new distance applies only to combatant 1 and 2 but 1 and 3 are unchanged
    with battle_map.as_if_dist_from_combatant(combatant1, combatant2, 10, dist_type=DistanceMetric.HOP):
        assert battle_map.get_hop_distance(combatant1, combatant2) == 10
        assert battle_map.get_hop_distance(combatant1, combatant3) == 1
    # test return to previous state
    assert battle_map.get_hop_distance(combatant1, combatant2) == 5
    assert battle_map.get_hop_distance(combatant1, combatant3) == 1
    # now test the combatant 1 and 3
    with battle_map.as_if_dist_from_combatant(combatant1, combatant3, 20, dist_type=DistanceMetric.HOP):
        assert battle_map.get_hop_distance(combatant1, combatant2) == 5
        assert battle_map.get_hop_distance(combatant1, combatant3) == 20
    # test return to previous state
    assert battle_map.get_hop_distance(combatant1, combatant2) == 5
    assert battle_map.get_hop_distance(combatant1, combatant3) == 1

    # Now let's also test cartesian distance
    battle_map.set_combatant_coordinates(combatant2, np.array([6, 8]))
    assert battle_map.get_cartesian_distance(combatant1, combatant2) == pytest.approx(1.41, 0.01)
    with battle_map.as_if_dist_from_combatant(combatant1, combatant2, 5.5, dist_type=DistanceMetric.CARTESIAN):
        assert battle_map.get_cartesian_distance(combatant1, combatant2) == 5.5
    # test return to previous state
    assert battle_map.get_cartesian_distance(combatant1, combatant2) == pytest.approx(1.41, 0.01)


def test_as_if_dist_mod_from_combatant(teams, effect_tracker, battle_map, combatant1, combatant2):
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    combatant3 = Goblin(effect_tracker, "Goblin 2")
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)

    battle_map.set_combatant_coordinates(combatant1, np.array([5, 7]))
    battle_map.set_combatant_coordinates(combatant2, np.array([10, 7]))
    battle_map.set_combatant_coordinates(combatant3, np.array([4, 7]))
    # establish baseline
    assert battle_map.get_hop_distance(combatant1, combatant2) == 5
    assert battle_map.get_hop_distance(combatant1, combatant3) == 1
    # now test that new distance applies only to combatant 1 and 2 but 1 and 3 are unchanged
    with battle_map.as_if_dist_mod_from_combatant(combatant1, combatant2, 2):
        assert battle_map.get_hop_distance(combatant1, combatant2) == 7
        assert battle_map.get_cartesian_distance(combatant1, combatant2) == 7
        assert battle_map.get_hop_distance(combatant1, combatant3) == 1
        assert battle_map.get_cartesian_distance(combatant1, combatant3) == 1
    # test return to previous state
    assert battle_map.get_hop_distance(combatant1, combatant2) == 5
    assert battle_map.get_hop_distance(combatant1, combatant3) == 1
    # now test the combatant 1 and 3
    with battle_map.as_if_dist_mod_from_combatant(combatant1, combatant3, -1):  # This closer
        assert battle_map.get_hop_distance(combatant1, combatant2) == 5
        assert battle_map.get_cartesian_distance(combatant1, combatant2) == 5
        assert battle_map.get_hop_distance(combatant1, combatant3) == 1 # 1 is min
        assert battle_map.get_cartesian_distance(combatant1, combatant3) == 1 # 1 is min
    # test return to previous state
    assert battle_map.get_hop_distance(combatant1, combatant2) == 5
    assert battle_map.get_hop_distance(combatant1, combatant3) == 1
    with battle_map.as_if_dist_mod_from_combatant(combatant1, combatant3, 3):
        assert battle_map.get_hop_distance(combatant1, combatant2) == 5
        assert battle_map.get_cartesian_distance(combatant1, combatant2) == 5
        assert battle_map.get_hop_distance(combatant1, combatant3) == 4 # 1 is min
        assert battle_map.get_cartesian_distance(combatant1, combatant3) == 4 # 1 is min
    assert battle_map.get_hop_distance(combatant1, combatant2) == 5
    assert battle_map.get_hop_distance(combatant1, combatant3) == 1
    
    
    
# def get_hop_distance(self, subject1, subject2):
#     subject1 = self.combatant_coordinate_cache[subject1] if issubclass(type(subject1), Combatant) else subject1
#     subject2 = self.combatant_coordinate_cache[subject2] if issubclass(type(subject2), Combatant) else subject2
#     try:
#         dist_mat = np.amin(distance_matrix(subject1, subject2))
#         min_dist_index = np.argmin(dist_mat)  # find the index closest distance between the two sets of points
#         sub1_closest_coord = subject1[min_dist_index // subject1.shape[0], :]
#         sub2_closest_coord = subject2[min_dist_index % subject2.shape[0], :]
#         res = np.max(np.abs(sub1_closest_coord - sub2_closest_coord))
#     except TypeError as e:
#         res = None
#     return res
# 
# def get_cartesian_distance(self, subject1, subject2):
#     try:
#         subject1 = self.combatant_coordinate_cache[subject1] if issubclass(type(subject1), Combatant) else subject1
#         subject2 = self.combatant_coordinate_cache[subject2] if issubclass(type(subject2), Combatant) else subject2
#     except KeyError:
#         return None
#     try:
#         new_res = np.amin(distance_matrix(subject1, subject2))
#         res = get_cartesian_distance(subject1, subject2)  # TODO REMOVE THIS
#     except TypeError:
#         res = None
#     assert res == new_res
#     return new_res


def test_hop_distance_diagonal(battle_map, combatant1, combatant2):
    # Two large combatants
    combatant1_coords = np.array([[0, 0], [1, 0], [0, 1], [1, 1]])
    combatant2_coords = np.array([[4, 4], [5, 4], [5, 4], [5, 5]])
    battle_map.set_combatant_coordinates(combatant1, combatant1_coords)
    battle_map.set_combatant_coordinates(combatant2, combatant2_coords)
    assert battle_map.get_hop_distance(combatant1, combatant2) == 3, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(combatant1_coords, combatant2) == 3, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(combatant1, combatant2_coords) == 3, "Incorrect distance between two large combatants"

def test_hop_distance_same_y(battle_map, combatant1, combatant2):
    combatant1_coords = np.array([[0, 0], [1, 0], [0, 1], [1, 1]])
    combatant2_coords = np.array([[6, 0], [7, 0], [6, 1], [7, 1]])
    battle_map.set_combatant_coordinates(combatant1, combatant1_coords)
    battle_map.set_combatant_coordinates(combatant2, combatant2_coords)
    assert battle_map.get_hop_distance(combatant1, combatant2) == 5, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(combatant1_coords, combatant2) == 5, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(combatant1, combatant2_coords) == 5, "Incorrect distance between two large combatants"

def test_hop_distance_same_x(battle_map, combatant1, combatant2):
    combatant1_coords = np.array([[0, 0], [1, 0], [0, 1], [1, 1]])
    combatant2_coords = np.array([[0, 4], [1, 4], [0, 5], [1, 5]])
    battle_map.set_combatant_coordinates(combatant1, combatant1_coords)
    battle_map.set_combatant_coordinates(combatant2, combatant2_coords)
    assert battle_map.get_hop_distance(combatant1, combatant2) == 3, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(combatant1_coords, combatant2) == 3, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(combatant1, combatant2_coords) == 3, "Incorrect distance between two large combatants"

def test_hop_distance_random(battle_map, combatant1, combatant2):
    combatant1_coords = np.array([[0, 0], [1, 0], [0, 1], [1, 1]])
    combatant2_coords = np.array([[3, 5], [4, 5], [3, 6], [4, 6]])
    battle_map.set_combatant_coordinates(combatant1, combatant1_coords)
    battle_map.set_combatant_coordinates(combatant2, combatant2_coords)
    assert battle_map.get_hop_distance(combatant1, combatant2) == 4, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(combatant1_coords, combatant2) == 4, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(combatant1, combatant2_coords) == 4, "Incorrect distance between two large combatants"
