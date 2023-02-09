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


def test_as_if_dist_farther_from_combatant(teams, effect_tracker, battle_map, combatant1, combatant2):
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
    with battle_map.as_if_dist_farther_from_combatant(combatant1, combatant2, 2):
        assert battle_map.get_hop_distance(combatant1, combatant2) == 7
        assert battle_map.get_cartesian_distance(combatant1, combatant2) == 7
        assert battle_map.get_hop_distance(combatant1, combatant3) == 1
        assert battle_map.get_cartesian_distance(combatant1, combatant3) == 1
    # test return to previous state
    assert battle_map.get_hop_distance(combatant1, combatant2) == 5
    assert battle_map.get_hop_distance(combatant1, combatant3) == 1
    # now test the combatant 1 and 3
    with battle_map.as_if_dist_farther_from_combatant(combatant1, combatant3, -1):
        assert battle_map.get_hop_distance(combatant1, combatant2) == 5
        assert battle_map.get_cartesian_distance(combatant1, combatant2) == 5
        assert battle_map.get_hop_distance(combatant1, combatant3) == 1 # 1 is min
        assert battle_map.get_cartesian_distance(combatant1, combatant3) == 1 # 1 is min
    # test return to previous state
    assert battle_map.get_hop_distance(combatant1, combatant2) == 5
    assert battle_map.get_hop_distance(combatant1, combatant3) == 1
    with battle_map.as_if_dist_farther_from_combatant(combatant1, combatant3, 3):
        assert battle_map.get_hop_distance(combatant1, combatant2) == 5
        assert battle_map.get_cartesian_distance(combatant1, combatant2) == 5
        assert battle_map.get_hop_distance(combatant1, combatant3) == 4 # 1 is min
        assert battle_map.get_cartesian_distance(combatant1, combatant3) == 4 # 1 is min
    assert battle_map.get_hop_distance(combatant1, combatant2) == 5
    assert battle_map.get_hop_distance(combatant1, combatant3) == 1
