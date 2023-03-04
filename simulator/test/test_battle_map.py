from simulator.action_types import Passive
from simulator.battle_map import Map, Terrain, CombatantCoords
from simulator.combatants.bugbear import Bugbear
from simulator.combatants.faurung import Faurung
from simulator.combatants.goblin import Goblin
from simulator.effects.effect_tracker import EffectTracker
from simulator.misc import DistanceMetric, Size, Side, Conditions
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

@pytest.fixture()
def combatant3(effect_tracker):
    return Bugbear(effect_tracker, "Bugbear")

@pytest.mark.skip(reason="enable this after combatant coord refactoring")
def test_as_if_combatant_position(teams, effect_tracker, battle_map, combatant1, combatant2):
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)

    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 7])))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([10, 7])))

    assert battle_map.get_cartesian_distance(combatant1, combatant2) == 5
    with battle_map.as_if_combatant_position(combatant1, CombatantCoords(np.array([9, 7]))):
        assert battle_map.get_cartesian_distance(combatant1, combatant2) == 1
    assert battle_map.get_cartesian_distance(combatant1, combatant2) == 5
    with battle_map.as_if_combatant_position(combatant1, CombatantCoords(np.array([0, 7]))):
        assert battle_map.get_cartesian_distance(combatant1, combatant2) == 10
    assert battle_map.get_cartesian_distance(combatant1, combatant2) == 5

@pytest.mark.skip(reason="enable this after combatant coord refactoring")
def test_as_if_dist_from_combatant(teams, effect_tracker, battle_map, combatant1, combatant2):
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    combatant3 = Goblin(effect_tracker, "Goblin 2")
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)

    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 7])))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([10, 7])))
    battle_map.set_combatant_coordinates(combatant3, CombatantCoords(np.array([4, 7])))
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
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([6, 8])))
    assert battle_map.get_cartesian_distance(combatant1, combatant2) == pytest.approx(1.41, 0.01)
    with battle_map.as_if_dist_from_combatant(combatant1, combatant2, 5.5, dist_type=DistanceMetric.CARTESIAN):
        assert battle_map.get_cartesian_distance(combatant1, combatant2) == 5.5
    # test return to previous state
    assert battle_map.get_cartesian_distance(combatant1, combatant2) == pytest.approx(1.41, 0.01)


@pytest.mark.skip(reason="enable this after combatant coord refactoring")
def test_as_if_dist_mod_from_combatant(teams, effect_tracker, battle_map, combatant1, combatant2):
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    combatant3 = Goblin(effect_tracker, "Goblin 2")
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)

    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 7])))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([10, 7])))
    battle_map.set_combatant_coordinates(combatant3, CombatantCoords(np.array([4, 7])))
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
    

def test_hop_distance_diagonal(battle_map, combatant1, combatant2):
    # Two large combatants
    combatant1.size = Size.LARGE
    combatant2.size = Size.LARGE
    combatant1_coords = CombatantCoords(np.array([0, 0]), combatant1.size)
    combatant2_coords = CombatantCoords(np.array([4, 4]), combatant2.size)
    battle_map.set_combatant_coordinates(combatant1, combatant1_coords)
    battle_map.set_combatant_coordinates(combatant2, combatant2_coords)
    assert battle_map.get_hop_distance(combatant1, combatant2) == 3, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(combatant1_coords.get(), combatant2) == 3, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(combatant1, combatant2_coords.get()) == 3, "Incorrect distance between two large combatants"


def test_hop_distance_same_y(battle_map, combatant1, combatant2):
    combatant1.size = Size.LARGE
    combatant2.size = Size.LARGE
    combatant1_coords = CombatantCoords(np.array([0, 0]), combatant1.size)
    combatant2_coords = CombatantCoords(np.array([6, 0]), combatant2.size)
    battle_map.set_combatant_coordinates(combatant1, combatant1_coords)
    battle_map.set_combatant_coordinates(combatant2, combatant2_coords)
    assert battle_map.get_hop_distance(combatant1, combatant2) == 5, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(combatant1_coords.get(), combatant2) == 5, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(combatant1, combatant2_coords.get()) == 5, "Incorrect distance between two large combatants"


def test_hop_distance_same_x(battle_map, combatant1, combatant2):
    combatant1.size = Size.LARGE
    combatant2.size = Size.LARGE
    combatant1_coords = CombatantCoords(np.array([0, 0]), combatant1.size)
    combatant2_coords = CombatantCoords(np.array([0, 4]), combatant2.size)
    battle_map.set_combatant_coordinates(combatant1, combatant1_coords)
    battle_map.set_combatant_coordinates(combatant2, combatant2_coords)
    assert battle_map.get_hop_distance(combatant1, combatant2) == 3, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(combatant1_coords.get(), combatant2) == 3, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(combatant1, combatant2_coords.get()) == 3, "Incorrect distance between two large combatants"


def test_hop_distance_random(battle_map, combatant1, combatant2):
    combatant1.size = Size.LARGE
    combatant2.size = Size.LARGE
    combatant1_coords = CombatantCoords(np.array([0, 0]), combatant1.size)
    combatant2_coords = CombatantCoords(np.array([3, 5]), combatant2.size)
    battle_map.set_combatant_coordinates(combatant1, combatant1_coords)
    battle_map.set_combatant_coordinates(combatant2, combatant2_coords)
    assert battle_map.get_hop_distance(combatant1, combatant2) == 4, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(combatant1_coords.get(), combatant2) == 4, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(combatant1, combatant2_coords.get()) == 4, "Incorrect distance between two large combatants"


def test_are_in_hop_range_medium_medium(battle_map, combatant1, combatant2):
    combatant1_coords = CombatantCoords(np.array([0, 0]), combatant1.size)
    combatant2_coords = CombatantCoords(np.array([3, 5]), combatant2.size)
    battle_map.set_combatant_coordinates(combatant1, combatant1_coords)
    battle_map.set_combatant_coordinates(combatant2, combatant2_coords)
    assert battle_map.are_in_hop_range(combatant1, combatant2, 5)
    assert not battle_map.are_in_hop_range(combatant1, combatant2, 4)
    assert battle_map.are_in_hop_range(combatant1, combatant2, 6)

def test_are_in_hop_range_medium_large(battle_map, combatant1, combatant2):
    combatant1.size = Size.LARGE
    combatant1_coords = CombatantCoords(np.array([0, 0]), combatant1.size)
    combatant2_coords = CombatantCoords(np.array([3, 5]), combatant2.size)
    battle_map.set_combatant_coordinates(combatant1, combatant1_coords)
    battle_map.set_combatant_coordinates(combatant2, combatant2_coords)
    assert battle_map.are_in_hop_range(combatant1, combatant2, 4)
    assert not battle_map.are_in_hop_range(combatant1, combatant2, 3)
    assert battle_map.are_in_hop_range(combatant1, combatant2, 5)


def test_are_in_hop_range_medium_large(battle_map, combatant1, combatant2):
    combatant1.size = Size.LARGE
    combatant2.size = Size.LARGE
    combatant1_coords = CombatantCoords(np.array([0, 0]), combatant1.size)
    combatant2_coords = CombatantCoords(np.array([3, 5]), combatant2.size)
    battle_map.set_combatant_coordinates(combatant1, combatant1_coords)
    battle_map.set_combatant_coordinates(combatant2, combatant2_coords)
    assert battle_map.are_in_hop_range(combatant1, combatant2, 4)
    assert not battle_map.are_in_hop_range(combatant1, combatant2, 3)
    assert battle_map.are_in_hop_range(combatant1, combatant2, 5)

def test_cartesian_distance_diagonal(battle_map, combatant1, combatant2):
    # Two large combatants
    combatant1.size = Size.LARGE
    combatant2.size = Size.LARGE
    combatant1_coords = CombatantCoords(np.array([0, 0]), combatant1.size)
    combatant2_coords = CombatantCoords(np.array([4, 4]), combatant2.size)
    battle_map.set_combatant_coordinates(combatant1, combatant1_coords)
    battle_map.set_combatant_coordinates(combatant2, combatant2_coords)
    assert battle_map.get_cartesian_distance(combatant1, combatant2) == pytest.approx(4.242, 0.001), "Incorrect distance between two large combatants"
    assert battle_map.get_cartesian_distance(combatant1_coords.get(), combatant2) == pytest.approx(4.242, 0.001), "Incorrect distance between two large combatants"
    assert battle_map.get_cartesian_distance(combatant1, combatant2_coords.get()) == pytest.approx(4.242, 0.001), "Incorrect distance between two large combatants"


def test_cartesian_distance_same_y(battle_map, combatant1, combatant2):
    combatant1.size = Size.LARGE
    combatant2.size = Size.LARGE
    combatant1_coords = CombatantCoords(np.array([0, 0]), combatant1.size)
    combatant2_coords = CombatantCoords(np.array([6, 0]), combatant2.size)
    battle_map.set_combatant_coordinates(combatant1, combatant1_coords)
    battle_map.set_combatant_coordinates(combatant2, combatant2_coords)
    assert battle_map.get_cartesian_distance(combatant1, combatant2) == 5, "Incorrect distance between two large combatants"
    assert battle_map.get_cartesian_distance(combatant1_coords.get(), combatant2) == 5, "Incorrect distance between two large combatants"
    assert battle_map.get_cartesian_distance(combatant1, combatant2_coords.get()) == 5, "Incorrect distance between two large combatants"


def test_cartesian_distance_same_x(battle_map, combatant1, combatant2):
    combatant1.size = Size.LARGE
    combatant2.size = Size.LARGE
    combatant1_coords = CombatantCoords(np.array([0, 0]), combatant1.size)
    combatant2_coords = CombatantCoords(np.array([0, 4]), combatant2.size)
    battle_map.set_combatant_coordinates(combatant1, combatant1_coords)
    battle_map.set_combatant_coordinates(combatant2, combatant2_coords)
    assert battle_map.get_cartesian_distance(combatant1, combatant2) == 3, "Incorrect distance between two large combatants"
    assert battle_map.get_cartesian_distance(combatant1_coords.get(), combatant2) == 3, "Incorrect distance between two large combatants"
    assert battle_map.get_cartesian_distance(combatant1, combatant2_coords.get()) == 3, "Incorrect distance between two large combatants"


def test_cartesian_distance_random(battle_map, combatant1, combatant2):
    combatant1.size = Size.LARGE
    combatant2.size = Size.LARGE
    combatant1_coords = CombatantCoords(np.array([0, 0]), combatant1.size)
    combatant2_coords = CombatantCoords(np.array([3, 5]), combatant2.size)
    battle_map.set_combatant_coordinates(combatant1, combatant1_coords)
    battle_map.set_combatant_coordinates(combatant2, combatant2_coords)
    assert battle_map.get_cartesian_distance(combatant1, combatant2) == pytest.approx(4.4721, 0.001), "Incorrect distance between two large combatants"
    assert battle_map.get_cartesian_distance(combatant1_coords.get(), combatant2) == pytest.approx(4.4721, 0.001), "Incorrect distance between two large combatants"
    assert battle_map.get_cartesian_distance(combatant1, combatant2_coords.get()) == pytest.approx(4.4721, 0.001), "Incorrect distance between two large combatants"


def test_build_combatant_adjacency_mask_medium(battle_map, combatant1):
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 12])))

    battle_map.place_circular_element(np.array([9, 13]),  Terrain.IMPASSABLE_TERRAIN, diameter=1)
    adj_mask = battle_map.build_combatant_adjacency_mask(combatant1)

    # Check that the obstacle's not inflated for medium size
    assert np.all(adj_mask[:, 8 * battle_map.size + 12])
    assert np.all(adj_mask[:, 8 * battle_map.size + 13])
    assert np.all(adj_mask[:, 8 * battle_map.size + 14])
    assert np.all(adj_mask[:, 9 * battle_map.size + 12])
    assert not np.any(adj_mask[:, 9 * battle_map.size + 13])
    assert np.all(adj_mask[:, 9 * battle_map.size + 14])
    assert np.all(adj_mask[:, 10 * battle_map.size + 12])
    assert np.all(adj_mask[:, 10 * battle_map.size + 13])
    assert np.all(adj_mask[:, 10 * battle_map.size + 14])


def test_build_combatant_adjacency_mask_large(battle_map, combatant1):
    combatant1.size = Size.LARGE
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 12]), combatant1.size))

    battle_map.place_circular_element(np.array([9, 13]),  Terrain.IMPASSABLE_TERRAIN, diameter=1)
    adj_mask = battle_map.build_combatant_adjacency_mask(combatant1)

    # Check the inflation of the obstacle
    assert not np.any(adj_mask[:, 8 * battle_map.size + 13])
    assert not np.any(adj_mask[:, 8 * battle_map.size + 12])
    assert not np.any(adj_mask[:, 9 * battle_map.size + 12])
    assert not np.any(adj_mask[:, 9 * battle_map.size + 13])

    # Test a corner case where the obstacle has nowhere to inflate to
    battle_map.place_circular_element(np.array([0, 0]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    adj_mask = battle_map.build_combatant_adjacency_mask(combatant1)
    assert not np.any(adj_mask[:, 0])
    # the other side's intact
    assert np.all(adj_mask[:, 1])
    assert np.all(adj_mask[:, battle_map.size])
    assert np.all(adj_mask[:, battle_map.size + 1])



def test_build_combatant_adjacency_mask_huge(battle_map, combatant1):
    combatant1.size = Size.HUGE
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([4, 11]), combatant1.size))

    battle_map.place_circular_element(np.array([9, 13]),  Terrain.IMPASSABLE_TERRAIN, diameter=1)
    adj_mask = battle_map.build_combatant_adjacency_mask(combatant1)

    # Check the inflation of the obstacle
    assert not np.any(adj_mask[:, 7 * battle_map.size + 11])
    assert not np.any(adj_mask[:, 7 * battle_map.size + 12])
    assert not np.any(adj_mask[:, 7 * battle_map.size + 13])
    assert not np.any(adj_mask[:, 8 * battle_map.size + 11])
    assert not np.any(adj_mask[:, 8 * battle_map.size + 12])
    assert not np.any(adj_mask[:, 8 * battle_map.size + 13])
    assert not np.any(adj_mask[:, 9 * battle_map.size + 11])
    assert not np.any(adj_mask[:, 9 * battle_map.size + 12])
    assert not np.any(adj_mask[:, 9 * battle_map.size + 13])

    # Test a corner case where the obstacle has nowhere to inflate to
    battle_map.place_circular_element(np.array([0, 0]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    adj_mask = battle_map.build_combatant_adjacency_mask(combatant1)
    assert not np.any(adj_mask[:, 0])
    # the other side's intact
    assert np.all(adj_mask[:, 1])
    assert np.all(adj_mask[:, battle_map.size])
    assert np.all(adj_mask[:, battle_map.size + 1])


def test_get_pam_eligible_combatants_medium_medium(battle_map, combatant1, combatant2, teams):
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    combatant1.add_ability(Passive.POLEARM_MASTER)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 7])))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([7, 7])))
    eligible_combatants = battle_map.get_pam_eligible_combatants(combatant2, np.array([-1, 0]))
    assert len(eligible_combatants) == 1
    assert eligible_combatants[0] is combatant1

def test_get_pam_eligible_combatants_medium_large(battle_map, combatant1, combatant2, teams):
    combatant1.add_ability(Passive.POLEARM_MASTER)
    combatant2.size = Size.LARGE
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 7])))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([7, 7]), combatant2.size))
    # we're moving the large one from the attack range of the medium one
    eligible_combatants = battle_map.get_pam_eligible_combatants(combatant2, np.array([-1, 0]))
    assert len(eligible_combatants) == 1
    assert eligible_combatants[0] is combatant1

def test_get_pam_eligible_combatants_large_medium(battle_map, combatant1, combatant2, teams):
    combatant1.add_ability(Passive.POLEARM_MASTER)
    combatant1.size = Size.LARGE
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 7]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([8, 7])))
    # we're moving the medium one from the attack range of the large one
    eligible_combatants = battle_map.get_pam_eligible_combatants(combatant2, np.array([-1, 0]))
    assert len(eligible_combatants) == 1
    assert eligible_combatants[0] is combatant1

def test_get_pam_eligible_combatants_large_large(battle_map, combatant1, combatant2, teams):
    combatant1.add_ability(Passive.POLEARM_MASTER)
    combatant1.size = Size.LARGE
    combatant2.size = Size.LARGE
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 7]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([8, 7]), combatant2.size))
    # we're moving the large one from the attack range of the other large one
    eligible_combatants = battle_map.get_pam_eligible_combatants(combatant2, np.array([-1, 0]))
    assert len(eligible_combatants) == 1
    assert eligible_combatants[0] is combatant1


def test_get_aoo_eligible_combatants_medium_medium_medium(battle_map, combatant1, combatant2, combatant3, teams):
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    teams.add_combatant_to_team(combatant3, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 7])))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([6, 7])))
    battle_map.set_combatant_coordinates(combatant3, CombatantCoords(np.array([5, 6])))
    eligible_combatants = battle_map.get_aoo_eligible_combatants(combatant2, np.array([1, 0]))
    assert len(eligible_combatants) == 2
    assert set(eligible_combatants) == {combatant1, combatant3}

def test_get_aoo_eligible_combatants_medium_large_medium(battle_map, combatant1, combatant2, combatant3, teams):
    combatant2.size = Size.LARGE
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    teams.add_combatant_to_team(combatant3, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 7])))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([6, 7]), combatant2.size))
    battle_map.set_combatant_coordinates(combatant3, CombatantCoords(np.array([5, 8])))
    # we're moving the large one from the attack range of the medium one
    eligible_combatants = battle_map.get_aoo_eligible_combatants(combatant2, np.array([1, 0]))
    assert len(eligible_combatants) == 2
    assert set(eligible_combatants) == {combatant1, combatant3}

def test_get_aoo_eligible_combatants_large_medium_medium(battle_map, combatant1, combatant2, combatant3, teams):
    combatant1.size = Size.LARGE
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 7]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([7, 7])))
    battle_map.set_combatant_coordinates(combatant3, CombatantCoords(np.array([7, 9])))
    # we're moving the medium one from the attack range of the large one
    eligible_combatants = battle_map.get_aoo_eligible_combatants(combatant2, np.array([1, 0]))
    assert len(eligible_combatants) == 1
    assert eligible_combatants[0] is combatant1
    eligible_combatants = battle_map.get_aoo_eligible_combatants(combatant3, np.array([1, 1]))
    assert len(eligible_combatants) == 1
    assert eligible_combatants[0] is combatant1

def test_get_aoo_eligible_combatants_large_large(battle_map, combatant1, combatant2, teams):
    combatant1.size = Size.LARGE
    combatant2.size = Size.LARGE
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 7]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([7, 9]), combatant2.size))
    # we're moving the large one from the attack range of the other large one
    eligible_combatants = battle_map.get_aoo_eligible_combatants(combatant2, np.array([1, 1]))
    assert len(eligible_combatants) == 1
    assert eligible_combatants[0] is combatant1

def test_get_free_adjacent_coords_medium(battle_map, combatant1):
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 7])))
    coords = battle_map.get_combatant_position(combatant1)
    adj = battle_map.get_free_adjacent_coords(coords)
    assert adj == {(4, 7), (6, 7), (4, 8), (5, 8), (6, 8), (4, 6), (5, 6), (6, 6)}

def test_get_free_adjacent_coords_large(battle_map, combatant1):
    combatant1.size = Size.LARGE
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 7]), combatant1.size))
    coords = battle_map.get_combatant_position(combatant1)
    adj = battle_map.get_free_adjacent_coords(coords)
    assert adj == {(4, 6), (4, 7), (4, 8), (4, 9), (5, 6), (5, 9), (6, 6), (6, 9), (7, 6), (7, 7), (7, 8), (7, 9)}

def test_get_free_adjacent_coords_large_corner(battle_map, combatant1):
    combatant1.size = Size.LARGE
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1]), combatant1.size))
    coords = battle_map.get_combatant_position(combatant1)
    adj = battle_map.get_free_adjacent_coords(coords)
    assert adj == {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (0, 3), (1, 3), (2, 3)}

def test_get_free_adjacent_coords_huge_with_terrain(battle_map, combatant1):
    combatant1.size = Size.HUGE
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([8, 2]), combatant1.size))
    coords = battle_map.get_combatant_position(combatant1)
    battle_map.place_circular_element(np.array([7, 3]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    adj = battle_map.get_free_adjacent_coords(coords)
    assert adj == {(7, 1), (7, 2), (7, 4), (7, 5), (8, 1), (8, 5), (9, 1), (9, 5), (10, 1), (10, 5), (11, 1), (11, 2), (11, 3), (11, 4), (11, 5)}


def test_get_adjacent_coords_medium(battle_map, combatant1, combatant2):
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 7])))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([6, 7])))
    coords = battle_map.get_combatant_position(combatant1)
    battle_map.place_circular_element(np.array([5, 6]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    adj = battle_map.get_adjacent_coords(coords)
    assert adj == {(4, 7), (6, 7), (4, 8), (5, 8), (6, 8), (4, 6), (6, 6)}

def test_get_adjacent_coords_large(battle_map, combatant1, combatant2):
    combatant1.size = Size.LARGE
    combatant2.size = Size.LARGE
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 7]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([5, 9]), combatant1.size))
    coords = battle_map.get_combatant_position(combatant1)
    adj = battle_map.get_adjacent_coords(coords)
    assert adj == {(4, 6), (4, 7), (4, 8), (4, 9), (5, 6), (5, 9), (6, 6), (6, 9), (7, 6), (7, 7), (7, 8), (7, 9)}

def test_get_adjacent_coords_large_corner(battle_map, combatant1):
    combatant1.size = Size.LARGE
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1]), combatant1.size))
    coords = battle_map.get_combatant_position(combatant1)
    battle_map.place_circular_element(np.array([2, 3]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    adj = battle_map.get_adjacent_coords(coords)
    assert adj == {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (0, 3), (1, 3)}

def test_get_adjacent_coords_huge_with_terrain(battle_map, combatant1, combatant2):
    combatant1.size = Size.HUGE
    combatant2.size = Size.LARGE
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([8, 2]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([11, 2]), combatant1.size))
    coords = battle_map.get_combatant_position(combatant1)
    battle_map.place_circular_element(np.array([7, 3]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([8, 5]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    adj = battle_map.get_adjacent_coords(coords)
    assert adj == {(7, 1), (7, 2), (7, 4), (7, 5), (8, 1), (9, 1), (9, 5), (10, 1), (10, 5), (11, 1), (11, 2), (11, 3), (11, 4),
                   (11, 5)}
def test_get_nearest_adjacent_coord(battle_map, combatant1):
    my_coords = CombatantCoords(np.array([1, 7]))
    combatant1.size = Size.LARGE
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 7]), combatant1.size))
    target_coords = battle_map.get_combatant_position(combatant1)
    nearest = battle_map.get_nearest_adjacent_coord(my_coords, target_coords)
    assert np.array_equal(nearest, np.array([4, 7]), equal_nan=False)

    my_coords = CombatantCoords(np.array([3, 9]))
    nearest = battle_map.get_nearest_adjacent_coord(my_coords, target_coords)
    assert np.array_equal(nearest, np.array([4, 9]), equal_nan=False)

    my_coords = CombatantCoords(np.array([8, 6]))
    nearest = battle_map.get_nearest_adjacent_coord(my_coords, target_coords)
    assert np.array_equal(nearest, np.array([7, 6]), equal_nan=False)

    my_coords = CombatantCoords(np.array([7, 11]))
    nearest = battle_map.get_nearest_adjacent_coord(my_coords, target_coords)
    assert np.array_equal(nearest, np.array([7, 9]), equal_nan=False)

def test_get_path_to_medium_to_medium(battle_map, combatant1, combatant2):
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1])))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([11, 3])))
    path = battle_map.get_path_to(combatant1, combatant2)
    assert np.array_equal(path, [np.array([1, 1]), np.array([1, 0]), np.array([1, 0]), np.array([1, 0]), np.array([1, 0]),
                                 np.array([1, 0]), np.array([1, 0]), np.array([1, 0]), np.array([1, 0]), np.array([1, 0])])

def test_get_path_to_large_to_large(battle_map, combatant1, combatant2):
    battle_map.build_adjacency_matrix()
    combatant1.size = Size.LARGE
    combatant2.size = Size.LARGE
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([5, 7]), combatant2.size))
    path = battle_map.get_path_to(combatant1, combatant2)
    assert np.array_equal(path, [np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([0, 1])])

def test_get_path_to_medium_to_large(battle_map, combatant1, combatant2):
    battle_map.build_adjacency_matrix()
    combatant2.size = Size.LARGE
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1])))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([5, 7]), combatant2.size))
    path = battle_map.get_path_to(combatant1, combatant2)
    assert np.array_equal(path, [np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([0, 1])]) or\
           np.array_equal(path, [np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([1, 1])])

def test_get_path_to_large_to_medium(battle_map, combatant1, combatant2):
    battle_map.build_adjacency_matrix()
    combatant1.size = Size.LARGE
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([5, 7])))
    path = battle_map.get_path_to(combatant1, combatant2)
    assert np.array_equal(path, [np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([0, 1])])

def test_get_path_to_huge_to_huge(battle_map, combatant1, combatant2):
    battle_map.build_adjacency_matrix()
    combatant1.size = Size.HUGE
    combatant2.size = Size.HUGE
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([5, 7]), combatant2.size))
    path = battle_map.get_path_to(combatant1, combatant2)
    assert np.array_equal(path, [np.array([1, 1]), np.array([1, 1]), np.array([0, 1])])


def test_move_combatant_by_increment_medium(teams, battle_map, combatant1):
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1])))
    assert np.array_equal(battle_map.get_combatant_position(combatant1).get(), np.array([[0, 1]]))
    battle_map.move_combatant_by_increment(combatant1, np.array([1, 1]))
    assert np.array_equal(battle_map.get_combatant_position(combatant1).get(), np.array([[1, 2]]))


def test_move_combatant_by_increment_medium_invalid(teams, battle_map, combatant1):
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1])))
    assert np.array_equal(battle_map.get_combatant_position(combatant1).get(), np.array([[0, 1]]))
    with pytest.raises(AssertionError):
        battle_map.move_combatant_by_increment(combatant1, np.array([-1, 0]))


def test_move_combatant_by_increment_large(teams, battle_map, combatant1):
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    combatant1.size = Size.LARGE
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1]), combatant1.size))
    assert np.array_equal(battle_map.get_combatant_position(combatant1).get(), np.array([[0, 1], [0, 2], [1, 1], [1, 2]]))
    battle_map.move_combatant_by_increment(combatant1, np.array([1, 1]))
    assert np.array_equal(battle_map.get_combatant_position(combatant1).get(), np.array([[1, 2], [1, 3], [2, 2], [2, 3]]))


def test_move_combatant_medium(teams, battle_map, combatant1):
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1])))
    assert np.array_equal(battle_map.get_combatant_position(combatant1).get(), np.array([[0, 1]]))
    battle_map.move_combatant(combatant1, CombatantCoords(np.array([14, 14])))
    assert np.array_equal(battle_map.get_combatant_position(combatant1).get(), np.array([[14, 14]]))

def test_move_combatant_medium_invalid(teams, battle_map, combatant1):
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1])))
    assert np.array_equal(battle_map.get_combatant_position(combatant1).get(), np.array([[0, 1]]))
    with pytest.raises(AssertionError):
        battle_map.move_combatant(combatant1, CombatantCoords(np.array([15, 15])))

def test_move_combatant_large(teams, battle_map, combatant1):
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    combatant1.size = Size.LARGE
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1]), combatant1.size))
    assert np.array_equal(battle_map.get_combatant_position(combatant1).get(), np.array([[0, 1], [0, 2], [1, 1], [1, 2]]))
    battle_map.move_combatant(combatant1, CombatantCoords(np.array([9, 9]), combatant1.size))
    assert np.array_equal(battle_map.get_combatant_position(combatant1).get(), np.array([[9, 9], [9, 10], [10, 9], [10, 10]]))


def test_get_nearest_hop(battle_map, teams, combatant1, combatant2,combatant3):
    combatant1.size = Size.LARGE
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([1, 2]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([1, 5])))
    battle_map.set_combatant_coordinates(combatant3, CombatantCoords(np.array([4, 5])))
    nearest, dist, _ = battle_map.get_nearest(combatant3, side=Side.ENEMY, dist_type=DistanceMetric.HOP)
    assert nearest is combatant1
    assert dist == 2
    nearest, dist, _ = battle_map.get_nearest(combatant1, side=Side.ALLY, dist_type=DistanceMetric.HOP)
    assert nearest is combatant2
    assert dist == 2

def test_get_nearest_cartesian(battle_map, teams, combatant1, combatant2,combatant3):
    combatant1.size = Size.LARGE
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([1, 2]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([1, 5])))
    battle_map.set_combatant_coordinates(combatant3, CombatantCoords(np.array([4, 5])))
    nearest, dist, _ = battle_map.get_nearest(combatant3, side=Side.ENEMY, dist_type=DistanceMetric.CARTESIAN)
    assert nearest is combatant1
    assert dist == pytest.approx(2.828, 0.001)
    nearest, dist, _ = battle_map.get_nearest(combatant1, side=Side.ALLY, dist_type=DistanceMetric.CARTESIAN)
    assert nearest is combatant2
    assert dist == pytest.approx(2.000, 0.001)


def test_is_enemy_adjacent(battle_map, teams, combatant1, combatant2):
    combatant1.size = Size.LARGE
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([1, 2]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([3, 4])))
    assert battle_map.is_enemy_adjacent(combatant1)
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([4, 5])))
    assert not battle_map.is_enemy_adjacent(combatant1)


def test_is_ally_adjacent_to_target(battle_map, teams, combatant1, combatant2, combatant3):
    combatant1.size = Size.LARGE
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([1, 2]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([1, 5])))
    battle_map.set_combatant_coordinates(combatant3, CombatantCoords(np.array([1, 4])))
    assert battle_map.is_ally_adjacent_to_target(combatant1, combatant3)
    combatant2.apply_condition(Conditions.INCAPACITATED)
    assert not battle_map.is_ally_adjacent_to_target(combatant1, combatant3)
    combatant2.remove_condition(Conditions.INCAPACITATED)
    battle_map.move_combatant(combatant2, CombatantCoords(np.array([1, 6])))
    assert not battle_map.is_ally_adjacent_to_target(combatant1, combatant3)


def test_get_free_coords_away_from_enemies(battle_map, teams, combatant1, combatant2, combatant3):

    combatant1.size = Size.LARGE
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([4, 5]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([8, 9])))
    coords = battle_map.get_free_coords_away_from_enemies(combatant1, 3, dist_type=DistanceMetric.HOP)
    assert np.array_equal(coords[0], np.array([1, 2]))

    teams.add_combatant_to_team(combatant3, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant3, CombatantCoords(np.array([8, 1])))
    assert np.array_equal(coords[0], np.array([1, 5]))