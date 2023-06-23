import pytest
from simulator.actions.action_types import Passive, Action
from simulator.battle_map import Terrain, CombatantCoords
from simulator.combatants.goblin import Goblin
from simulator.misc import DistanceMetric, Size, Side, Conditions
from simulator.spells.fireball import FireballFactory
from simulator.spells.spell import SpellStats
from simulator.teams import Teams
from simulator.test.fixtures import test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian, test_stone_giant, test_ogre, test_moon_druid, \
    teams, effect_tracker, battle_map
import numpy as np



def test_as_if_combatant_position(teams, battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)

    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([10, 7]))

    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5
    with battle_map.as_if_combatant_position(test_draconic_sorcerer_5lvl, np.array([9, 7])):
        assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin) == 1
    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5
    with battle_map.as_if_combatant_position(test_draconic_sorcerer_5lvl, np.array([0, 7])):
        assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin) == 10
    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5

def test_get_hop_distance_overlapping_medium_large(battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    with pytest.raises(AssertionError):
        battle_map.set_combatant_coordinates(test_goblin, np.array([6, 8]))


def test_get_hop_distance_overlapping_large_huge(battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    test_draconic_sorcerer_5lvl.size = Size.HUGE
    test_goblin.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    with pytest.raises(AssertionError):
        battle_map.set_combatant_coordinates(test_goblin, np.array([7, 8]))


def test_as_if_dist_from_combatant(teams, effect_tracker, battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    test_bugbear = Goblin(effect_tracker, "Goblin 2")
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)

    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([10, 7]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 7]))
    # establish baseline
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_bugbear) == 1
    # now test that new distance applies only to combatant 1 and 2 but 1 and 3 are unchanged
    with battle_map.as_if_dist_from_combatant(test_draconic_sorcerer_5lvl, test_goblin, 10, dist_type=DistanceMetric.HOP):
        assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin) == 10
        assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_bugbear) == 1
    # test return to previous state
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_bugbear) == 1
    # now test the combatant 1 and 3
    with battle_map.as_if_dist_from_combatant(test_draconic_sorcerer_5lvl, test_bugbear, 20, dist_type=DistanceMetric.HOP):
        assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5
        assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_bugbear) == 20
    # test return to previous state
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_bugbear) == 1

    # Now let's also test cartesian distance
    battle_map.set_combatant_coordinates(test_goblin, np.array([6, 8]))
    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin) == pytest.approx(1.41, 0.01)
    with battle_map.as_if_dist_from_combatant(test_draconic_sorcerer_5lvl, test_goblin, 5.5, dist_type=DistanceMetric.CARTESIAN):
        assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5.5
    # test return to previous state
    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin) == pytest.approx(1.41, 0.01)


def test_as_if_dist_mod_from_combatant(teams, effect_tracker, battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    test_bugbear = Goblin(effect_tracker, "Goblin 2")
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)

    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([10, 7]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 7]))
    # establish baseline
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_bugbear) == 1
    # now test that new distance applies only to combatant 1 and 2 but 1 and 3 are unchanged
    with battle_map.as_if_dist_mod_from_combatant(test_draconic_sorcerer_5lvl, test_goblin, 2):
        assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin) == 7
        assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin) == 7
        assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_bugbear) == 1
        assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_bugbear) == 1
    # test return to previous state
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_bugbear) == 1
    # now test the combatant 1 and 3
    with battle_map.as_if_dist_mod_from_combatant(test_draconic_sorcerer_5lvl, test_bugbear, -1):  # This closer
        assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5
        assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5
        assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_bugbear) == 1 # 1 is min
        assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_bugbear) == 1 # 1 is min
    # test return to previous state
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_bugbear) == 1
    with battle_map.as_if_dist_mod_from_combatant(test_draconic_sorcerer_5lvl, test_bugbear, 3):
        assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5
        assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5
        assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_bugbear) == 4 # 1 is min
        assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_bugbear) == 4 # 1 is min
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_bugbear) == 1
    

def test_hop_distance_diagonal(battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    # Two large combatants
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_goblin.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 0]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([4, 4]))
    test_draconic_sorcerer_5lvl_coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    test_goblin_coords = battle_map.get_combatant_position(test_goblin)
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin) == 3, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl_coords.get(), test_goblin) == 3, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin_coords.get()) == 3, "Incorrect distance between two large combatants"


def test_hop_distance_same_y(battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_goblin.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 0]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([6, 0]))
    test_draconic_sorcerer_5lvl_coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    test_goblin_coords = battle_map.get_combatant_position(test_goblin)
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl_coords.get(), test_goblin) == 5, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin_coords.get()) == 5, "Incorrect distance between two large combatants"


def test_hop_distance_same_x(battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_goblin.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 0]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([0, 4]))
    test_draconic_sorcerer_5lvl_coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    test_goblin_coords = battle_map.get_combatant_position(test_goblin)
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin) == 3, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl_coords.get(), test_goblin) == 3, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin_coords.get()) == 3, "Incorrect distance between two large combatants"


def test_hop_distance_random(battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_goblin.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 0]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([3, 5]))
    test_draconic_sorcerer_5lvl_coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    test_goblin_coords = battle_map.get_combatant_position(test_goblin)
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin) == 4, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl_coords.get(), test_goblin) == 4, "Incorrect distance between two large combatants"
    assert battle_map.get_hop_distance(test_draconic_sorcerer_5lvl, test_goblin_coords.get()) == 4, "Incorrect distance between two large combatants"


def test_are_in_hop_range_medium_medium(battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 0]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([3, 5]))
    assert battle_map.are_in_hop_range(test_draconic_sorcerer_5lvl, test_goblin, 5)
    assert not battle_map.are_in_hop_range(test_draconic_sorcerer_5lvl, test_goblin, 4)
    assert battle_map.are_in_hop_range(test_draconic_sorcerer_5lvl, test_goblin, 6)

def test_are_in_hop_range_medium_large(battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 0]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([3, 5]))
    assert battle_map.are_in_hop_range(test_draconic_sorcerer_5lvl, test_goblin, 4)
    assert not battle_map.are_in_hop_range(test_draconic_sorcerer_5lvl, test_goblin, 3)
    assert battle_map.are_in_hop_range(test_draconic_sorcerer_5lvl, test_goblin, 5)


def test_are_in_hop_range_medium_large(battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_goblin.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 0]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([3, 5]))
    assert battle_map.are_in_hop_range(test_draconic_sorcerer_5lvl, test_goblin, 4)
    assert not battle_map.are_in_hop_range(test_draconic_sorcerer_5lvl, test_goblin, 3)
    assert battle_map.are_in_hop_range(test_draconic_sorcerer_5lvl, test_goblin, 5)

def test_cartesian_distance_diagonal(battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    # Two large combatants
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_goblin.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 0]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([4, 4]))
    test_draconic_sorcerer_5lvl_coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    test_goblin_coords = battle_map.get_combatant_position(test_goblin)
    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin) == pytest.approx(4.242, 0.001), "Incorrect distance between two large combatants"
    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl_coords.get(), test_goblin) == pytest.approx(4.242, 0.001), "Incorrect distance between two large combatants"
    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin_coords.get()) == pytest.approx(4.242, 0.001), "Incorrect distance between two large combatants"


def test_cartesian_distance_same_y(battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_goblin.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 0]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([6, 0]))
    test_draconic_sorcerer_5lvl_coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    test_goblin_coords = battle_map.get_combatant_position(test_goblin)
    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin) == 5, "Incorrect distance between two large combatants"
    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl_coords.get(), test_goblin) == 5, "Incorrect distance between two large combatants"
    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin_coords.get()) == 5, "Incorrect distance between two large combatants"


def test_cartesian_distance_same_x(battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_goblin.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 0]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([0, 4]))
    test_draconic_sorcerer_5lvl_coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    test_goblin_coords = battle_map.get_combatant_position(test_goblin)
    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin) == 3, "Incorrect distance between two large combatants"
    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl_coords.get(), test_goblin) == 3, "Incorrect distance between two large combatants"
    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin_coords.get()) == 3, "Incorrect distance between two large combatants"


def test_cartesian_distance_random(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_goblin.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 0]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([3, 5]))
    test_draconic_sorcerer_5lvl_coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    test_goblin_coords = battle_map.get_combatant_position(test_goblin)
    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin) == pytest.approx(4.4721, 0.001), "Incorrect distance between two large combatants"
    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl_coords.get(), test_goblin) == pytest.approx(4.4721, 0.001), "Incorrect distance between two large combatants"
    assert battle_map.get_cartesian_distance(test_draconic_sorcerer_5lvl, test_goblin_coords.get()) == pytest.approx(4.4721, 0.001), "Incorrect distance between two large combatants"


def test_build_combatant_adjacency_mask_medium(battle_map, teams, test_draconic_sorcerer_5lvl):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 12]))

    battle_map.place_circular_element(np.array([9, 13]),  Terrain.IMPASSABLE_TERRAIN, radius=0)
    adj_mask = battle_map.build_combatant_adjacency_mask(test_draconic_sorcerer_5lvl)

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


def test_build_combatant_adjacency_mask_large(battle_map, teams, test_draconic_sorcerer_5lvl):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 12]))

    battle_map.place_circular_element(np.array([9, 13]),  Terrain.IMPASSABLE_TERRAIN, radius=0)
    adj_mask = battle_map.build_combatant_adjacency_mask(test_draconic_sorcerer_5lvl)

    # Check the inflation of the obstacle
    assert not np.any(adj_mask[:, 8 * battle_map.size + 13])
    assert not np.any(adj_mask[:, 8 * battle_map.size + 12])
    assert not np.any(adj_mask[:, 9 * battle_map.size + 12])
    assert not np.any(adj_mask[:, 9 * battle_map.size + 13])

    # Test a corner case where the obstacle has nowhere to inflate to
    battle_map.place_circular_element(np.array([0, 0]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    adj_mask = battle_map.build_combatant_adjacency_mask(test_draconic_sorcerer_5lvl)
    assert not np.any(adj_mask[:, 0])
    # the other side's intact
    assert np.all(adj_mask[:, 1])
    assert np.all(adj_mask[:, battle_map.size])
    assert np.all(adj_mask[:, battle_map.size + 1])



def test_build_combatant_adjacency_mask_huge(battle_map, teams, test_draconic_sorcerer_5lvl):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    test_draconic_sorcerer_5lvl.size = Size.HUGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([4, 11]))

    battle_map.place_circular_element(np.array([9, 13]),  Terrain.IMPASSABLE_TERRAIN, radius=0)
    adj_mask = battle_map.build_combatant_adjacency_mask(test_draconic_sorcerer_5lvl)

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
    battle_map.place_circular_element(np.array([0, 0]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    adj_mask = battle_map.build_combatant_adjacency_mask(test_draconic_sorcerer_5lvl)
    assert not np.any(adj_mask[:, 0])
    # the other side's intact
    assert np.all(adj_mask[:, 1])
    assert np.all(adj_mask[:, battle_map.size])
    assert np.all(adj_mask[:, battle_map.size + 1])


def test_get_pam_eligible_combatants_medium_medium(battle_map, test_draconic_sorcerer_5lvl, test_goblin, teams):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    test_draconic_sorcerer_5lvl.add_ability(Passive.POLEARM_MASTER)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([7, 7]))
    eligible_combatants = battle_map.get_pam_eligible_combatants(test_goblin, np.array([-1, 0]))
    assert len(eligible_combatants) == 1
    assert eligible_combatants[0] is test_draconic_sorcerer_5lvl

def test_get_pam_eligible_combatants_medium_large(battle_map, test_draconic_sorcerer_5lvl, test_goblin, teams):
    test_draconic_sorcerer_5lvl.add_ability(Passive.POLEARM_MASTER)
    test_goblin.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([7, 7]))
    # we're moving the large one from the attack range of the medium one
    eligible_combatants = battle_map.get_pam_eligible_combatants(test_goblin, np.array([-1, 0]))
    assert len(eligible_combatants) == 1
    assert eligible_combatants[0] is test_draconic_sorcerer_5lvl

def test_get_pam_eligible_combatants_large_medium(battle_map, test_draconic_sorcerer_5lvl, test_goblin, teams):
    test_draconic_sorcerer_5lvl.add_ability(Passive.POLEARM_MASTER)
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([8, 7]))
    # we're moving the medium one from the attack range of the large one
    eligible_combatants = battle_map.get_pam_eligible_combatants(test_goblin, np.array([-1, 0]))
    assert len(eligible_combatants) == 1
    assert eligible_combatants[0] is test_draconic_sorcerer_5lvl

def test_get_pam_eligible_combatants_large_large(battle_map, test_draconic_sorcerer_5lvl, test_goblin, teams):
    test_draconic_sorcerer_5lvl.add_ability(Passive.POLEARM_MASTER)
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_goblin.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([8, 7]))
    # we're moving the large one from the attack range of the other large one
    eligible_combatants = battle_map.get_pam_eligible_combatants(test_goblin, np.array([-1, 0]))
    assert len(eligible_combatants) == 1
    assert eligible_combatants[0] is test_draconic_sorcerer_5lvl


def test_get_aoo_eligible_combatants_medium_medium_medium(battle_map, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, teams):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([6, 7]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([5, 6]))
    eligible_combatants = battle_map.get_aoo_eligible_combatants(test_goblin, np.array([1, 0]))
    assert len(eligible_combatants) == 2
    assert set(eligible_combatants) == {test_draconic_sorcerer_5lvl, test_bugbear}

def test_get_aoo_eligible_combatants_medium_large_medium(battle_map, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, teams):
    test_goblin.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([6, 7]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([5, 8]))
    # we're moving the large one from the attack range of the medium one
    eligible_combatants = battle_map.get_aoo_eligible_combatants(test_goblin, np.array([1, 0]))
    assert len(eligible_combatants) == 2
    assert set(eligible_combatants) == {test_draconic_sorcerer_5lvl, test_bugbear}

def test_get_aoo_eligible_combatants_large_medium_medium(battle_map, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, teams):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([7, 7]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([7, 9]))
    # we're moving the medium one from the attack range of the large one
    eligible_combatants = battle_map.get_aoo_eligible_combatants(test_goblin, np.array([1, 0]))
    assert len(eligible_combatants) == 1
    assert eligible_combatants[0] is test_draconic_sorcerer_5lvl
    eligible_combatants = battle_map.get_aoo_eligible_combatants(test_bugbear, np.array([1, 1]))
    assert len(eligible_combatants) == 1
    assert eligible_combatants[0] is test_draconic_sorcerer_5lvl

def test_get_aoo_eligible_combatants_large_large(battle_map, test_draconic_sorcerer_5lvl, test_goblin, teams):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_goblin.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([7, 9]))
    # we're moving the large one from the attack range of the other large one
    eligible_combatants = battle_map.get_aoo_eligible_combatants(test_goblin, np.array([1, 1]))
    assert len(eligible_combatants) == 1
    assert eligible_combatants[0] is test_draconic_sorcerer_5lvl

def test_get_free_coords_in_hop_range_medium(battle_map, test_draconic_sorcerer_5lvl):
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    adj = battle_map.get_free_coords_in_hop_range(coords)
    assert adj == {(4, 7), (6, 7), (4, 8), (5, 8), (6, 8), (4, 6), (5, 6), (6, 6)}
    # same but including the combatant's own coord
    adj = battle_map.get_free_coords_in_hop_range(coords, combatant=test_draconic_sorcerer_5lvl)
    assert adj == {(4, 7), (5, 7), (6, 7), (4, 8), (5, 8), (6, 8), (4, 6), (5, 6), (6, 6)}

def test_get_free_coords_in_hop_range_large(battle_map, test_draconic_sorcerer_5lvl):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    adj = battle_map.get_free_coords_in_hop_range(coords)
    assert adj == {(4, 6), (4, 7), (4, 8), (4, 9), (5, 6), (5, 9), (6, 6), (6, 9), (7, 6), (7, 7), (7, 8), (7, 9)}
    # same but including the combatant's own coord
    adj = battle_map.get_free_coords_in_hop_range(coords, combatant=test_draconic_sorcerer_5lvl)
    assert adj == {(4, 6), (5, 7), (6, 7), (5, 8), (6, 8), (4, 7), (4, 8), (4, 9), (5, 6), (5, 9), (6, 6), (6, 9), (7, 6), (7, 7), (7, 8), (7, 9)}

def test_get_free_coords_in_hop_range_large_corner(battle_map, test_draconic_sorcerer_5lvl):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 1]))
    coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    adj = battle_map.get_free_coords_in_hop_range(coords)
    assert adj == {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (0, 3), (1, 3), (2, 3)}

def test_get_free_coords_in_hop_range_huge_with_terrain(battle_map, test_draconic_sorcerer_5lvl):
    test_draconic_sorcerer_5lvl.size = Size.HUGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([8, 2]))
    coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    battle_map.place_circular_element(np.array([7, 3]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    adj = battle_map.get_free_coords_in_hop_range(coords)
    assert adj == {(7, 1), (7, 2), (7, 4), (7, 5), (8, 1), (8, 5), (9, 1), (9, 5), (10, 1), (10, 5), (11, 1), (11, 2), (11, 3), (11, 4), (11, 5)}
    # same but including the combatant's own coord
    adj = battle_map.get_free_coords_in_hop_range(coords, combatant=test_draconic_sorcerer_5lvl)
    assert adj == {(7, 1), (7, 2), (7, 4), (7, 5), (8, 1), (8, 2), (9, 2), (10, 2), (8, 3), (9, 3), (10, 3),
                   (8, 4), (9, 4), (10, 4), (8, 5), (9, 1), (9, 5), (10, 1), (10, 5), (11, 1), (11, 2), (11, 3),
                   (11, 4), (11, 5)}


def test_get_free_coords_in_cartesian_range_medium(battle_map, teams, test_draconic_sorcerer_5lvl):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    free_coords = battle_map.get_free_coords_in_cartesian_range(coords, rng=1)
    # only directly above, below and to the sides
    assert free_coords == {(4, 7), (6, 7), (5, 8), (5, 6)}
    free_coords = battle_map.get_free_coords_in_cartesian_range(coords, rng=1, combatant=test_draconic_sorcerer_5lvl)
    # same but including the combatant's own coord
    assert free_coords == {(4, 7),(5, 7), (6, 7), (5, 8), (5, 6)}

    battle_map.move_combatant(test_draconic_sorcerer_5lvl, np.array([8, 13]))
    coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    free_coords = battle_map.get_free_coords_in_cartesian_range(coords, rng=2)
    assert free_coords == {(6, 13), (7, 13), (9, 13), (10, 13), (7, 14), (8, 14), (9, 14), (7, 12), (8, 12), (9, 12), (8, 11)}
    free_coords = battle_map.get_free_coords_in_cartesian_range(coords, rng=2, combatant=test_draconic_sorcerer_5lvl)
    # same but including the combatant's own coord
    assert free_coords == {(6, 13), (7, 13), (8, 13), (9, 13), (10, 13), (7, 14), (8, 14), (9, 14), (7, 12), (8, 12), (9, 12), (8, 11)}

    battle_map.move_combatant(test_draconic_sorcerer_5lvl, np.array([5, 5]))
    coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    free_coords = battle_map.get_free_coords_in_cartesian_range(coords, rng=4)
    assert (1, 1) not in free_coords and (2, 1) not in free_coords and (3, 1) not in free_coords and (4, 1) not in free_coords and (6, 1) not in free_coords
    assert (7, 1) not in free_coords and (8, 1) not in free_coords
    assert (1, 2) not in free_coords and (1, 3) not in free_coords and (1, 4) not in free_coords and (1, 6) not in free_coords and (1, 7) not in free_coords
    assert (1, 8) not in free_coords and (8, 8) not in free_coords
    assert (2, 8) not in free_coords and (8, 8) not in free_coords and (9, 8) not in free_coords
    assert (9, 5) in free_coords and (1, 5) in free_coords and (5, 1) in free_coords and (5, 9) in free_coords
    # same but including the combatant's own coord
    free_coords = battle_map.get_free_coords_in_cartesian_range(coords, rng=4, combatant=test_draconic_sorcerer_5lvl)
    assert (5, 5) in free_coords

def test_get_free_coords_in_cartesian_range_large(battle_map, teams, test_draconic_sorcerer_5lvl):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([2, 2]))
    coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    free_coords = battle_map.get_free_coords_in_cartesian_range(coords, rng=1)
    assert free_coords == {(2, 1), (3, 1), (1, 2), (4, 2), (1, 3), (4, 3), (2, 4), (3, 4)}
    free_coords = battle_map.get_free_coords_in_cartesian_range(coords, rng=1, combatant=test_draconic_sorcerer_5lvl)
    # same but including the combatant's own coord
    assert free_coords == {(2, 1), (2, 2), (3, 2), (2, 3), (3, 3), (3, 1), (1, 2), (4, 2), (1, 3), (4, 3), (2, 4), (3, 4)}

    battle_map.move_combatant(test_draconic_sorcerer_5lvl, np.array([6, 8]))
    coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    free_coords = battle_map.get_free_coords_in_cartesian_range(coords, rng=2)
    assert free_coords == {(6, 6), (7, 6), (5, 7), (6, 7), (7, 7), (8, 7), (4, 8), (5, 8), (8, 8), (9, 8), (4, 9), (5, 9), (8, 9), (9, 9), (5, 10), (6, 10), (7, 10), (8, 10), (6, 11), (7, 11)}
    free_coords = battle_map.get_free_coords_in_cartesian_range(coords, rng=2, combatant=test_draconic_sorcerer_5lvl)
    # same but including the combatant's own coord
    assert free_coords == {(6, 6), (6, 8), (7, 8), (6, 9), (7, 9), (7, 6), (5, 7), (6, 7), (7, 7), (8, 7), (4, 8), (5, 8), (8, 8), (9, 8), (4, 9), (5, 9), (8, 9), (9, 9), (5, 10), (6, 10), (7, 10), (8, 10), (6, 11), (7, 11)}

def test_get_adjacent_coords_medium(battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([6, 7]))
    coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    battle_map.place_circular_element(np.array([5, 6]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    adj = battle_map.get_adjacent_coords(coords)
    assert adj == {(4, 7), (6, 7), (4, 8), (5, 8), (6, 8), (4, 6), (6, 6)}

def test_get_adjacent_coords_large(battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_goblin.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 7]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([5, 9]))
    coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    adj = battle_map.get_adjacent_coords(coords)
    assert adj == {(4, 6), (4, 7), (4, 8), (4, 9), (5, 6), (5, 9), (6, 6), (6, 9), (7, 6), (7, 7), (7, 8), (7, 9)}

def test_get_adjacent_coords_large_corner(battle_map, test_draconic_sorcerer_5lvl):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 1]))
    coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    battle_map.place_circular_element(np.array([2, 3]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    adj = battle_map.get_adjacent_coords(coords)
    assert adj == {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (0, 3), (1, 3)}

def test_get_adjacent_coords_huge_with_terrain(battle_map, test_draconic_sorcerer_5lvl, test_goblin):
    test_draconic_sorcerer_5lvl.size = Size.HUGE
    test_goblin.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([8, 2]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([11, 2]))
    coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    battle_map.place_circular_element(np.array([7, 3]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([8, 5]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    adj = battle_map.get_adjacent_coords(coords)
    assert adj == {(7, 1), (7, 2), (7, 4), (7, 5), (8, 1), (9, 1), (9, 5), (10, 1), (10, 5), (11, 1), (11, 2), (11, 3), (11, 4),
                   (11, 5)}
def test_get_nearest_free_adjacent_coord(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin):
    battle_map.build_adjacency_matrix()
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    test_goblin.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 7]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([5, 7]))
    distances, _ = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    my_coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    target_coords = battle_map.get_combatant_position(test_goblin)
    nearest = battle_map.get_nearest_free_adjacent_coords(my_coords, target_coords, distances)
    assert np.array_equal(nearest, np.array([4, 7]), equal_nan=False)

    battle_map.move_combatant(test_draconic_sorcerer_5lvl, np.array([3, 9]))
    my_coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    nearest = battle_map.get_nearest_free_adjacent_coords(my_coords, target_coords, distances)
    assert np.array_equal(nearest, np.array([4, 9]), equal_nan=False)

    battle_map.move_combatant(test_draconic_sorcerer_5lvl, np.array([8, 6]))
    my_coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    nearest = battle_map.get_nearest_free_adjacent_coords(my_coords, target_coords, distances)
    assert np.array_equal(nearest, np.array([7, 6]), equal_nan=False)

    battle_map.move_combatant(test_draconic_sorcerer_5lvl, np.array([7, 11]))
    my_coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    nearest = battle_map.get_nearest_free_adjacent_coords(my_coords, target_coords, distances)
    assert np.array_equal(nearest, np.array([7, 9]), equal_nan=False)

def test_get_nearest_free_adjacent_coord_large_huge(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear):
    """
    Test resulting from debugging a specific scenario
    """
    battle_map.build_adjacency_matrix()
    test_draconic_sorcerer_5lvl.size = Size.HUGE
    test_goblin.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([4, 10]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([9, 10]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([9, 13]))
    distances, _ = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    my_coords = battle_map.get_combatant_position(test_draconic_sorcerer_5lvl)
    target_coords = battle_map.get_combatant_position(test_bugbear)
    nearest = battle_map.get_nearest_free_adjacent_coords(my_coords, target_coords, distances)
    assert not np.array_equal(nearest, np.array([7, 10]), equal_nan=False)


def test_get_path_to_combatant_medium_to_medium(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([11, 3]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_goblin)
    assert np.array_equal(path, [np.array([1, 1]), np.array([1, 0]), np.array([1, 0]), np.array([1, 0]), np.array([1, 0]),
                                 np.array([1, 0]), np.array([1, 0]), np.array([1, 0]), np.array([1, 0]), np.array([1, 0])])

def test_get_path_to_coord_medium_to_coord(battle_map, teams, test_draconic_sorcerer_5lvl):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 1]))
    path = battle_map.get_path_to_coord(test_draconic_sorcerer_5lvl, np.array([11, 3]))
    assert np.array_equal(path, [np.array([1, 1]), np.array([1,1]), np.array([1, 0]), np.array([1, 0]), np.array([1, 0]),
                                 np.array([1, 0]), np.array([1, 0]), np.array([1, 0]), np.array([1, 0]), np.array([1, 0]), np.array([1, 0])])

def test_get_path_to_combatant_large_to_large(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    battle_map.build_adjacency_matrix()
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_goblin.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([5, 7]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_goblin)
    assert np.array_equal(path, [np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([0, 1])])

def test_get_path_to_combatant_medium_to_large(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    battle_map.build_adjacency_matrix()
    test_goblin.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([5, 7]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_goblin)
    assert np.array_equal(path, [np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([0, 1])]) or\
           np.array_equal(path, [np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([1, 1])])

def test_get_path_to_combatant_large_to_medium(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    battle_map.build_adjacency_matrix()
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([5, 7]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_goblin)
    assert np.array_equal(path, [np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([0, 1])])

def test_get_path_to_combatant_large_to_medium2(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    battle_map.place_circular_element(np.array([7, 14]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([9, 14]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.build_adjacency_matrix()
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([4, 13]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([8, 14]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_goblin)
    assert np.array_equal(path, [np.array([1, 0]), np.array([1, 0])])

def test_get_path_to_combatant_huge_to_huge(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    battle_map.build_adjacency_matrix()
    test_draconic_sorcerer_5lvl.size = Size.HUGE
    test_goblin.size = Size.HUGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([5, 7]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_goblin)
    assert np.array_equal(path, [np.array([1, 1]), np.array([1, 1]), np.array([0, 1])])


def test_move_combatant_by_increment_medium(teams, battle_map, test_draconic_sorcerer_5lvl):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 1]))
    assert np.array_equal(battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get(), np.array([[0, 1]]))
    battle_map.move_combatant_by_increment(test_draconic_sorcerer_5lvl, np.array([1, 1]))
    assert np.array_equal(battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get(), np.array([[1, 2]]))


def test_move_combatant_by_increment_medium_invalid(teams, battle_map, test_draconic_sorcerer_5lvl):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 1]))
    assert np.array_equal(battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get(), np.array([[0, 1]]))
    with pytest.raises(AssertionError):
        battle_map.move_combatant_by_increment(test_draconic_sorcerer_5lvl, np.array([-1, 0]))


def test_move_combatant_by_increment_large(teams, battle_map, test_draconic_sorcerer_5lvl):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 1]))
    assert np.array_equal(battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get(), np.array([[0, 1], [0, 2], [1, 1], [1, 2]]))
    battle_map.move_combatant_by_increment(test_draconic_sorcerer_5lvl, np.array([1, 1]))
    assert np.array_equal(battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get(), np.array([[1, 2], [1, 3], [2, 2], [2, 3]]))


def test_move_combatant_medium(teams, battle_map, test_draconic_sorcerer_5lvl):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 1]))
    assert np.array_equal(battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get(), np.array([[0, 1]]))
    battle_map.move_combatant(test_draconic_sorcerer_5lvl, np.array([14, 14]))
    assert np.array_equal(battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get(), np.array([[14, 14]]))

def test_move_combatant_medium_invalid(teams, battle_map, test_draconic_sorcerer_5lvl):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 1]))
    assert np.array_equal(battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get(), np.array([[0, 1]]))
    with pytest.raises(AssertionError):
        battle_map.move_combatant(test_draconic_sorcerer_5lvl, np.array([15, 15]))

def test_move_combatant_large(teams, battle_map, test_draconic_sorcerer_5lvl):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 1]))
    assert np.array_equal(battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get(), np.array([[0, 1], [0, 2], [1, 1], [1, 2]]))
    battle_map.move_combatant(test_draconic_sorcerer_5lvl, np.array([9, 9]))
    assert np.array_equal(battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get(), np.array([[9, 9], [9, 10], [10, 9], [10, 10]]))


def test_get_nearest_hop(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin,test_bugbear):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 2]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([1, 5]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 5]))
    nearest, dist, _ = battle_map.get_nearest(test_bugbear, side=Side.ENEMY, dist_type=DistanceMetric.HOP)
    assert nearest is test_draconic_sorcerer_5lvl
    assert dist == 2
    nearest, dist, _ = battle_map.get_nearest(test_draconic_sorcerer_5lvl, side=Side.ALLY, dist_type=DistanceMetric.HOP)
    assert nearest is test_goblin
    assert dist == 2

def test_get_nearest_cartesian(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin,test_bugbear):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 2]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([1, 5]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 5]))
    nearest, dist, _ = battle_map.get_nearest(test_bugbear, side=Side.ENEMY, dist_type=DistanceMetric.CARTESIAN)
    assert nearest is test_draconic_sorcerer_5lvl
    assert dist == pytest.approx(2.828, 0.001)
    nearest, dist, _ = battle_map.get_nearest(test_draconic_sorcerer_5lvl, side=Side.ALLY, dist_type=DistanceMetric.CARTESIAN)
    assert nearest is test_goblin
    assert dist == pytest.approx(2.000, 0.001)


def test_is_enemy_adjacent(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 2]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([3, 4]))
    assert battle_map.is_enemy_adjacent(test_draconic_sorcerer_5lvl)
    battle_map.set_combatant_coordinates(test_goblin, np.array([4, 5]))
    assert not battle_map.is_enemy_adjacent(test_draconic_sorcerer_5lvl)


def test_is_ally_adjacent_to_target(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 2]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([1, 5]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([1, 4]))
    assert battle_map.is_ally_adjacent_to_target(test_draconic_sorcerer_5lvl, test_bugbear)
    test_goblin.apply_condition(Conditions.INCAPACITATED, None)
    assert not battle_map.is_ally_adjacent_to_target(test_draconic_sorcerer_5lvl, test_bugbear)
    test_goblin.remove_condition(Conditions.INCAPACITATED)
    battle_map.move_combatant(test_goblin, np.array([1, 6]))
    assert not battle_map.is_ally_adjacent_to_target(test_draconic_sorcerer_5lvl, test_bugbear)


def test_get_free_coords_away_from_enemies(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([4, 5]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([8, 9]))
    coords = battle_map.get_free_coords_at_distance_sorted_by_dist_to_enemies(test_draconic_sorcerer_5lvl, 3, dist_type=DistanceMetric.HOP)
    assert np.array_equal(coords[0][0], np.array([1, 2]))

    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_bugbear, np.array([8, 1]))
    coords = battle_map.get_free_coords_at_distance_sorted_by_dist_to_enemies(test_draconic_sorcerer_5lvl, 3, dist_type=DistanceMetric.CARTESIAN)
    assert np.array_equal(coords[0][0], np.array([1, 5]))


def test_get_free_coords_at_distance_from_target_medium_medium(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin):
    battle_map.build_adjacency_matrix()
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([4, 5]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([8, 9]))
    coords = battle_map.get_free_coords_at_distance_from_target(test_draconic_sorcerer_5lvl, test_goblin, 2)
    assert np.array_equal(np.array(coords[0:8]), np.array([[7, 8], [7, 9], [7, 10], [8, 8], [8, 10], [9, 8], [9, 9], [9, 10]]))

    battle_map.move_combatant(test_goblin, np.array([13, 9]))
    # now test the range between 2 and 3
    coords = battle_map.get_free_coords_at_distance_from_target(test_draconic_sorcerer_5lvl, test_goblin, 2, 3)
    assert np.array_equal(np.array(coords[0:6]), np.array([[7, 3], [7, 4], [7, 5], [7, 6], [7, 7], [7, 8]]))

    battle_map.move_combatant(test_goblin, np.array([5, 5]))
    # now test adjacent initial position
    coords = battle_map.get_free_coords_at_distance_from_target(test_draconic_sorcerer_5lvl, test_goblin, 3, 3)
    assert np.array_equal(np.array(coords[0:5]), np.array([[7, 3], [7, 4], [7, 5], [7, 6], [7, 7]]))


def test_get_free_coords_at_distance_from_target_large_medium(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.build_adjacency_matrix()
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([4, 5]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([4, 7]))
    coords = battle_map.get_free_coords_at_distance_from_target(test_draconic_sorcerer_5lvl, test_goblin, 3)
    assert np.array_equal(np.array(coords[0:5]), np.array([[2, 9], [3, 9], [4, 9], [5, 9], [6, 9]]))


def test_get_free_coords_at_distance_from_target_large_huge(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_goblin.size = Size.HUGE
    battle_map.build_adjacency_matrix()
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([4, 5]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([1, 7]))
    coords = battle_map.get_free_coords_at_distance_from_target(test_draconic_sorcerer_5lvl, test_goblin, 2, 2)
    assert np.array_equal(np.array(coords[0:3]), np.array([[0, 6], [0, 7], [0, 8]]))


def test_remove_combatant(battle_map, test_draconic_sorcerer_5lvl):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([4, 5]))
    battle_map.remove_combatant(test_draconic_sorcerer_5lvl)
    assert battle_map.get_combatant_position(test_draconic_sorcerer_5lvl) is None
    assert battle_map.grid[4, 5].combatant is None
    assert battle_map.grid[5, 5].combatant is None
    assert battle_map.grid[4, 6].combatant is None
    assert battle_map.grid[5, 6].combatant is None


def test_reset(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin):
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_goblin.size = Size.HUGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    test_draconic_sorcerer_5lvl_initial_position = CombatantCoords(np.array([4, 5]), test_draconic_sorcerer_5lvl)
    test_goblin_initial_position = CombatantCoords(np.array([1, 7]), test_goblin)
    initial_positions = {test_draconic_sorcerer_5lvl: test_draconic_sorcerer_5lvl_initial_position.get()[0], test_goblin: test_goblin_initial_position.get()[0]}
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, test_draconic_sorcerer_5lvl_initial_position.get()[0])
    battle_map.set_combatant_coordinates(test_goblin, test_goblin_initial_position.get()[0])
    assert np.array_equal(test_draconic_sorcerer_5lvl_initial_position.get(), battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get())
    assert np.array_equal(test_goblin_initial_position.get(), battle_map.get_combatant_position(test_goblin).get())
    battle_map.move_combatant(test_draconic_sorcerer_5lvl, np.array([5, 6]))
    battle_map.move_combatant(test_goblin, np.array([2, 8]))
    assert np.array_equal(CombatantCoords(np.array([5, 6]), test_draconic_sorcerer_5lvl).get(), battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get())
    assert np.array_equal(CombatantCoords(np.array([2, 8]), test_goblin).get(), battle_map.get_combatant_position(test_goblin).get())
    battle_map.reset(initial_positions)
    assert np.array_equal(test_draconic_sorcerer_5lvl_initial_position.get(), battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get())
    assert np.array_equal(test_goblin_initial_position.get(), battle_map.get_combatant_position(test_goblin).get())
    assert battle_map.grid[6, 7].combatant is None
    assert battle_map.grid[4, 12].combatant is None


def test_find_best_placement_harmful_circular(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian):
    test_goblin.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([4, 4]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([10, 5]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([6, 7]))
    # Fireball-like
    fireball_factory = FireballFactory(1, Action.FIREBALL, test_draconic_sorcerer_5lvl)
    coord, score = battle_map.find_best_placement_harmful_circular(test_draconic_sorcerer_5lvl, FireballFactory.range, 4, fireball_factory)
    assert np.array_equal(coord, np.array([[7, 3]]))
    assert score == 28.0

    #Now move the ally in between the targets so that only one can be hit
    battle_map.move_combatant(test_totem_barbarian,  np.array([6, 4]))
    coord, score = battle_map.find_best_placement_harmful_circular(test_draconic_sorcerer_5lvl, FireballFactory.range, 4, fireball_factory)
    assert score == 14.0


def test_find_best_placement_harmful_square(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian, test_stone_giant):
    # test_goblin.size = Size.LARGE
    test_stone_giant.size = Size.MEDIUM  # downsize the giant for the sake of this test
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([4, 4]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([10, 5]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([6, 7]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([5, 5]))
    # 10ft square
    coord, score, affected = battle_map.find_best_placement_harmful_square(test_draconic_sorcerer_5lvl, 20, 2)
    assert np.array_equal(coord, np.array([[4, 4]]))
    assert score == 2
    assert test_goblin in affected
    assert test_bugbear not in affected
    assert test_totem_barbarian not in affected
    assert test_stone_giant in affected

    # Now move the ally in between the targets so that only one can be hit
    battle_map.move_combatant(test_totem_barbarian, np.array([5, 4]))
    coord, score, affected = battle_map.find_best_placement_harmful_square(test_draconic_sorcerer_5lvl, 20, 2)
    assert score == 1
    assert test_goblin in affected or test_bugbear in affected or test_stone_giant in affected
    assert test_totem_barbarian not in affected

def test_get_combatants_affected_by_aoe_sphere(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian):
    test_goblin.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([4, 4]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([10, 5]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([6, 7]))
    combatants = battle_map.get_combatants_affected_by_aoe(test_draconic_sorcerer_5lvl, SpellStats.Target.RADIUS_20, SpellStats.Type.HARMFUL, np.array([7, 3]))
    assert test_draconic_sorcerer_5lvl not in combatants
    assert test_goblin in combatants
    assert test_bugbear in combatants
    assert test_totem_barbarian not in combatants

def test_get_combatants_affected_by_aoe_square(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian, test_stone_giant, test_ogre):
    test_goblin.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([8, 5]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([10, 5]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([11, 4]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([10, 6]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([5, 3]))
    combatants = battle_map.get_combatants_affected_by_aoe(test_draconic_sorcerer_5lvl, SpellStats.Target.BOX_20, SpellStats.Type.HARMFUL, np.array([7, 3]))
    assert test_draconic_sorcerer_5lvl not in combatants
    assert test_goblin in combatants
    assert test_bugbear in combatants
    assert test_totem_barbarian not in combatants
    assert test_stone_giant in combatants
    assert test_ogre not in combatants

def test_get_enemies_within_radius_sorted_by_distance(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian):
    test_goblin.size = Size.LARGE
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([7, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([4, 4]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([10, 5]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([6, 7]))
    enemies, _ = battle_map.get_enemies_within_radius_sorted_by_distance(test_draconic_sorcerer_5lvl, 4)
    assert enemies == [test_goblin, test_bugbear]


def test_get_free_coords_sorted_by_distance_from_enemies(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian):
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([7, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([5, 11]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([10, 12]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([11, 6]))
    free_coords = battle_map.get_free_coords_sorted_by_distance_from_enemies(test_draconic_sorcerer_5lvl)
    assert np.array_equal(free_coords[0], np.array([0, 0]))

    battle_map.move_combatant(test_bugbear, np.array([0, 0]))
    free_coords = battle_map.get_free_coords_sorted_by_distance_from_enemies(test_draconic_sorcerer_5lvl)
    assert np.array_equal(free_coords[0], np.array([14, 14])) or np.array_equal(free_coords[0], np.array([13, 14]))


def test_find_wildshaped_coordinate_large_two_options(battle_map, teams, test_moon_druid):
    """
    We create a cavity surrounded bv impassable terrain and place a druid in it. The druid wants to wildshape into a large creature.
    The cavity is large enough for two possible placements of the large creature. But it picks the closer one.
    """
    battle_map.place_circular_element(np.array([2, 6]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([5, 4]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([5, 9]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([7, 6]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([7, 7]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([5, 7]))
    _, shortest_paths = battle_map.calc_dijkstra(test_moon_druid)
    test_moon_druid.shortest_paths_cache = shortest_paths
    coord = battle_map.find_wildshaped_coordinate(test_moon_druid, Size.LARGE)
    assert np.array_equal(coord, np.array([5, 6]))

def test_find_wildshaped_coordinate_huge_one_options(battle_map, teams, test_moon_druid):
    """
    We create a cavity surrounded bv impassable terrain and place a druid in it. The druid wants to wildshape into a huge creature.
    There's only one option how the huge creature can be placed and that it's two hops away from the druid.
    """
    battle_map.place_circular_element(np.array([1, 4]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([4, 1]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([2, 2]))
    _, shortest_paths = battle_map.calc_dijkstra(test_moon_druid)
    test_moon_druid.shortest_paths_cache = shortest_paths
    coord = battle_map.find_wildshaped_coordinate(test_moon_druid, Size.HUGE)
    assert np.array_equal(coord, np.array([0, 0]))

def test_find_wildshaped_coordinate_huge_three_options_variant_1(battle_map, teams, test_moon_druid):
    """
    The druid wants to wildshape into a huge creature. The druid's at the top edge of the map and they're in open terrain there's three
    options how the huge creature can be placed and that it's two hops away from the druid. But only the closest one will be picked.
    """
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([9, 14]))
    _, shortest_paths = battle_map.calc_dijkstra(test_moon_druid)
    test_moon_druid.shortest_paths_cache = shortest_paths
    coord = battle_map.find_wildshaped_coordinate(test_moon_druid, Size.HUGE)
    assert np.array_equal(coord, np.array([9, 12]))


def test_find_wildshaped_coordinate_huge_three_options_variant_2(battle_map, teams, test_moon_druid):
    """
    The druid wants to wildshape into a huge creature. The druid's at the right edge of the map and they're in open terrain there's three
    options how the huge creature can be placed and that it's two hops away from the druid. But only the closest one will be picked.
    """
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([14, 8]))
    _, shortest_paths = battle_map.calc_dijkstra(test_moon_druid)
    test_moon_druid.shortest_paths_cache = shortest_paths
    coord = battle_map.find_wildshaped_coordinate(test_moon_druid, Size.HUGE)
    assert np.array_equal(coord, np.array([12, 8]))

def test_find_wildshaped_coordinate_huge_four_options(battle_map, teams, test_moon_druid):
    """
    The druid wants to wildshape into a huge creature. The druid's near the top right edge of the map and they're in open terrain there's four
    options how the huge creature can be placed and that it's two hops away from the druid. But only the closest one will be picked.
    """
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([13, 13]))
    _, shortest_paths = battle_map.calc_dijkstra(test_moon_druid)
    test_moon_druid.shortest_paths_cache = shortest_paths
    coord = battle_map.find_wildshaped_coordinate(test_moon_druid, Size.HUGE)
    assert np.array_equal(coord, np.array([12, 12]))


def test_find_wildshaped_coordinate_huge_nine_options(battle_map, teams, test_moon_druid):
    """
    The druid wants to wildshape into a huge creature. The druid's out in open terrain there's nine
    options how the huge creature can be placed and that it's two hops away from the druid. But only the closest one will be picked.
    """
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([4, 12]))
    _, shortest_paths = battle_map.calc_dijkstra(test_moon_druid)
    test_moon_druid.shortest_paths_cache = shortest_paths
    coord = battle_map.find_wildshaped_coordinate(test_moon_druid, Size.HUGE)
    assert np.array_equal(coord, np.array([4, 12]))
