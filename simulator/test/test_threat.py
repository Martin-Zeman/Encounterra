import copy

import numpy as np
import pytest
from simulator.actions.action_types import Action
from simulator.actions.action_selector import decode_ms_path_to_actions
from simulator.actions.movement import MovementIncrement
from simulator.misc import Size
from simulator.spells.cloud_of_daggers import CloudOfDaggersFactory
from simulator.spells.firebolt import FireboltFactory
from simulator.spells.hunger_of_hadar import HungerOfHadarFactory
from simulator.spells.misty_step import MistyStepFactory, MistyStep
from simulator.spells.spike_growth import SpikeGrowthFactory
from simulator.teams import Teams
from simulator.threat_utils import accumulate_threat_along_path, calc_threat_for_path_with_misty_step, \
    DZ_CONSTANT, get_aoe_and_aoo_threat_for_increment
from simulator.test.fixtures import test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian, teams, effect_tracker, battle_map


def test_get_path_to_combatant_medium_to_medium_one_full_spike_growth(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, effect_tracker):
    """
    Tests the threat_on_move_within and threat_on_enter using Spike Growth where the combatant gets the full brunt of it
    """
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    sgf = SpikeGrowthFactory(Action.SPIKE_GROWTH, test_goblin, test_goblin.spellslots)
    sg = sgf.create(np.array([7, 3]))
    effect_tracker.add(sg)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([13, 3]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_goblin)
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[-1] == pytest.approx(9 * -5.0 - 2.925 * DZ_CONSTANT, 0.001)  # Getting the full brunt of the spike growth, plus danger zone


def test_get_path_to_combatant_medium_to_medium_one_partial_spike_growth(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, effect_tracker):
    """
    Tests the threat_on_move_within and threat_on_enter using Spike Growth where the combatant through a part of it
    """
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    sgf = SpikeGrowthFactory(Action.SPIKE_GROWTH, test_goblin, test_goblin.spellslots)
    sg = sgf.create(np.array([7, 6]))
    effect_tracker.add(sg)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([13, 3]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_goblin)
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[-1] == pytest.approx(5 * -5.0 - 2.925 * DZ_CONSTANT, 0.001)


def test_get_path_to_combatant_large_to_medium_one_aoe(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, effect_tracker):
    """
    Make it so that the large combatant is only hit by the AoE due to its size. The moving combatant is of size large. Make sure the
    threat is only added once per AoE. Tests the threat_on_enter using Cloud of Daggers.
    """
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    codf = CloudOfDaggersFactory(Action.CLOUD_OF_DAGGERS, test_goblin, test_goblin.spellslots)
    cod = codf.create(np.array([4, 2]))
    effect_tracker.add(cod)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([7, 1]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_goblin)
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[-1] == pytest.approx(-10.0 - 2.925 * DZ_CONSTANT, 0.001)


def test_get_path_to_combatant_large_to_medium_avoided_aoe(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, effect_tracker):
    """
    Make it so that the large combatant just narrowly skirts the outside of the AoE
    """
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    hohf = HungerOfHadarFactory(15, Action.HUNGER_OF_HADAR, test_goblin, test_goblin.spellslots)
    hoh = hohf.create(np.array([4, 7]))
    effect_tracker.add(hoh)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([7, 1]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_goblin)
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[-1] == pytest.approx(-2.925 * DZ_CONSTANT, 0.001) # Just danger zone


def test_get_path_to_combatant_medium_to_medium_two_overlapping_aoe(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, effect_tracker):
    """
    Two overlapping AoEs. Make sure the threats are added up.
    """
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    codf = CloudOfDaggersFactory(Action.CLOUD_OF_DAGGERS, test_goblin, test_goblin.spellslots)
    cod = codf.create(np.array([7, 3]))
    effect_tracker.add(cod)
    cod2 = codf.create(np.array([7, 3]))
    effect_tracker.add(cod2)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([13, 3]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_goblin)
    effect_to_coords = {e: e.get_affected_coords() for e in effect_tracker.get_aoe_effects()}
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[-1] == pytest.approx(-20.0 - 2.925 * DZ_CONSTANT, 0.0001)


def test_get_path_to_combatant_large_to_medium_two_overlapping_aoe(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, effect_tracker):
    """
    Two overlapping AoEs. Make sure the threats are added up. The moving combatant is of size large. Make sure the
    threat is only added once per AoE.
    """
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    codf = CloudOfDaggersFactory(Action.CLOUD_OF_DAGGERS, test_goblin, test_goblin.spellslots)
    cod = codf.create(np.array([7, 3]))
    effect_tracker.add(cod)
    hoh = codf.create(np.array([7, 4]))  # Should still be hit due to combatant's size
    effect_tracker.add(hoh)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([13, 3]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_goblin)
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[-1] == pytest.approx(-20.0 - 2.925 * DZ_CONSTANT, 0.0001)


def test_get_path_to_combatant_large_to_medium_starting_inside_aoe(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, effect_tracker):
    """
    The large combatant starts already inside the AoE. No threat should be accumulated.
    """
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    codf = CloudOfDaggersFactory(Action.CLOUD_OF_DAGGERS, test_goblin, test_goblin.spellslots)
    cod = codf.create(np.array([6, 3]))
    effect_tracker.add(cod)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([13, 3]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_goblin)
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[-1] == pytest.approx(-2.925 * DZ_CONSTANT, 0.001)  # Just danger zone


def test_get_path_to_combatant_medium_to_medium_pass_by_one_aoo(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, effect_tracker):
    """
    Basic AoO test. Combatant passes by one enemy on a way to another. All are of medium size.
    """
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([13, 3]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([6, 4]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_goblin)
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    battle_map.clear_caches()
    assert threat[-1] == pytest.approx(-5.95 - 5.95 * DZ_CONSTANT - 2.925 * DZ_CONSTANT, 0.01)  # includes danger zone
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords, disengaged=True)
    assert threat[-1] == pytest.approx(-2.925 * DZ_CONSTANT - 5.95 * DZ_CONSTANT, 0.01)  # includes danger zone


def test_get_path_to_combatant_medium_to_medium_pass_by_two_aoo(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, effect_tracker):
    """
    Same as the basic AoO test but this time the combatant passes by two enemies on the way to another. All are of medium size.
    """
    test_bugbear_2 = copy.deepcopy(test_bugbear)
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear_2, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([13, 3]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([6, 4]))
    battle_map.set_combatant_coordinates(test_bugbear_2, np.array([7, 4]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_goblin)
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[-1] == pytest.approx(2 * -5.95 - 2 * 5.95 * DZ_CONSTANT - 2.925 * DZ_CONSTANT, 0.001)  # includes danger zone
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords, disengaged=True)
    assert threat[-1] == pytest.approx(-2.925 * DZ_CONSTANT - 2 * 5.95 * DZ_CONSTANT, 0.001)  # includes danger zone


def test_get_path_to_combatant_large_to_medium_pass_by_two_aoo(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, effect_tracker):
    """
    Same as the basic AoO test but this time the combatant passes by two enemies the way to another. The moving combatant is of size large.
    Make sure the AoO threat is only added once per enemy.
    """
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_bugbear_2 = copy.deepcopy(test_bugbear)
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear_2, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 2]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([13, 3]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([6, 4]))
    battle_map.set_combatant_coordinates(test_bugbear_2, np.array([7, 4]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_goblin)
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[-1] == pytest.approx(2 * -5.95 - 2 * 5.95 * DZ_CONSTANT - 2.925 * DZ_CONSTANT, 0.01)  # includes danger zone
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords, disengaged=True)
    assert threat[-1] == pytest.approx(-2.925 * DZ_CONSTANT - 2 * 5.95 * DZ_CONSTANT, 0.01)  # includes danger zone


def test_get_path_to_coord_medium_stepping_away_from_medium_aoo(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, effect_tracker):
    """
    Starts with two adjacent combatants who are enemies. Calculates the threat of one stepping away from the other.
    """
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([3, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([3, 2]))
    path = battle_map.get_path_to_coord(test_draconic_sorcerer_5lvl, np.array([3, 5]))
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[-1] == pytest.approx(-2.925 - 2.925 * DZ_CONSTANT, 0.001)
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords, disengaged=True)
    assert threat[-1] == pytest.approx(-2.925 * DZ_CONSTANT, 0.001)


def test_get_path_to_coord_large_stepping_away_from_huge_aoo(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, effect_tracker):
    """
    Starts with two adjacent combatants who are enemies. Calculates the threat of one stepping away from the other. The moving combatant
    is large and the stationary one is huge.
    """
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    test_goblin.size = Size.HUGE
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 4]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([1, 1]))
    path = battle_map.get_path_to_coord(test_draconic_sorcerer_5lvl, np.array([1, 5]))
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[-1] == pytest.approx(-2.925 - 2.925 * DZ_CONSTANT, 0.001)
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords, disengaged=True)
    assert threat[-1] == pytest.approx(-2.925 * DZ_CONSTANT, 0.001)


def test_get_path_to_cord_large_stepping_away_from_two_medium_aoo(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, effect_tracker):
    """
    Starts with three adjacent combatant. One large and his two medium enemies. Calculates the threat of one stepping away from the other two.
    """
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([3, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([3, 2]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 2]))
    path = battle_map.get_path_to_coord(test_draconic_sorcerer_5lvl, np.array([3, 5]))
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[-1] == pytest.approx(-2.925 - 2.925 * DZ_CONSTANT - 5.95 - 5.95 * DZ_CONSTANT, 0.001)  # includes danger zone
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords, disengaged=True)
    assert threat[-1] == pytest.approx(-2.925 * DZ_CONSTANT - 5.95 * DZ_CONSTANT, 0.001)  # includes danger zone


def test_get_path_to_combatant_large_to_medium_pass_between_two_aoo_arrive_by_third(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian, effect_tracker):
    """
    Same as the basic AoO test but this time the combatant passes by two enemies on either side the way to another. The moving combatant is of size large.
    Make sure the AoO threat is only added once per enemy and that the last enemy doesn't incur any threat
    """
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([2, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([1, 4]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 4]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([2, 8]))
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_totem_barbarian)
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[-1] == pytest.approx(-2.925 - 2.925 * DZ_CONSTANT - 5.95 - 5.95 * DZ_CONSTANT - 7.149 * DZ_CONSTANT, 0.001)  # includes danger zone
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords, disengaged=True)
    assert threat[-1] == pytest.approx(-2.925 * DZ_CONSTANT - 5.95 * DZ_CONSTANT - 7.149 * DZ_CONSTANT, 0.001)  # includes danger zone


def test_get_path_to_combatant_large_to_medium_pass_between_two_aoo_through_aoe_arrive_by_third(battle_map, teams, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian, effect_tracker):
    """
    This test combines AoE and AoO.
    Same as the basic AoO test but this time the combatant passes by two enemies on either side the way to another. The
    moving combatant is of size large. Make sure the AoO threat is only added once per enemy and that the last enemy
    doesn't incur any threat. Additionally, make sure the threat from the AoE is included. It also includes the threat
    for staying at the coord since the AoE is at the final destination.
    """
    test_draconic_sorcerer_5lvl.size = Size.LARGE
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([2, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([1, 4]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 4]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([2, 8]))
    codf = CloudOfDaggersFactory(Action.CLOUD_OF_DAGGERS, test_goblin, test_goblin.spellslots)
    cod = codf.create(np.array([2, 7]))
    effect_tracker.add(cod)
    path = battle_map.get_path_to_combatant(test_draconic_sorcerer_5lvl, test_totem_barbarian)
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[-1] == pytest.approx(-2.925 - 2.925 * DZ_CONSTANT - 5.95 - 5.95 * DZ_CONSTANT - 20.0 - 7.149 * DZ_CONSTANT, 0.001)  # the -20 is composed of -10 for entering and -10 for staying plus danger zone
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords, disengaged=True)
    assert threat[-1] == pytest.approx(-20.0 - 2.925 * DZ_CONSTANT - 5.95 * DZ_CONSTANT - 7.149 * DZ_CONSTANT, 0.001)  # the -20 is composed of -10 for entering and -10 for staying plus danger zone


def test_get_path_to_combatant_medium_getting_out_of_danger_zone(battle_map, teams, test_draconic_sorcerer_5lvl, test_bugbear, effect_tracker):
    """
    Tests that the there is no threat when there's no AoE, AoO and the combatant gets out of the danger zone
    """
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([12, 1]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([14, 1]))
    path = battle_map.get_path_to_coord(test_draconic_sorcerer_5lvl, np.array([6, 1]))
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat = accumulate_threat_along_path(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[-1] == 0


def test_calc_threat_for_path_with_misty_step_scenario_1(battle_map, teams, test_draconic_sorcerer_5lvl, test_bugbear, effect_tracker):
    """
    Simple scenario with two combatants starting adjacent. We test that Misty Step lets us avoid the AoO.
    It tests calc_threat_for_path_with_misty_step as well as decode_ms_path_to_actions.
    """
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 5]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([5, 6]))
    path = battle_map.get_path_to_coord(test_draconic_sorcerer_5lvl, np.array([0, 14]))
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat, max_threat_path = calc_threat_for_path_with_misty_step(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[0] == 0

    actions = []
    ms_factory = MistyStepFactory(test_draconic_sorcerer_5lvl, test_draconic_sorcerer_5lvl.spellslots)
    decode_ms_path_to_actions(test_draconic_sorcerer_5lvl, battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get()[0], max_threat_path, actions, ms_factory)
    assert isinstance(actions[0], MovementIncrement)
    assert isinstance(actions[1], MistyStep)
    assert isinstance(actions[2], MovementIncrement)
    assert isinstance(actions[3], MovementIncrement)
    assert isinstance(actions[4], MovementIncrement)
    assert isinstance(actions[5], MovementIncrement)


def test_calc_threat_for_path_with_misty_step_scenario_2(battle_map, teams, test_draconic_sorcerer_5lvl, test_bugbear, effect_tracker):
    """
    A scenario with two combatants starting a bit apart from each other. One needs to move to a coord farther behind the other.
    The destination is directly within reach of Misty Step and so that's the only action the combatant takes.
    """
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 5]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([8, 5]))
    path = battle_map.get_path_to_coord(test_draconic_sorcerer_5lvl, np.array([11, 5]))
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat, max_threat_path = calc_threat_for_path_with_misty_step(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[0] == pytest.approx(-5.95 * DZ_CONSTANT, 0.001)  # Just for the danger zone

    actions = []
    ms_factory = MistyStepFactory(test_draconic_sorcerer_5lvl, test_draconic_sorcerer_5lvl.spellslots)
    decode_ms_path_to_actions(test_draconic_sorcerer_5lvl, battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get()[0], max_threat_path, actions, ms_factory)
    assert len(actions) == 1
    assert isinstance(actions[0], MistyStep)
    assert np.array_equal(actions[0].coord, np.array([11, 5]), equal_nan=False)


def test_calc_threat_for_path_with_misty_step_scenario_3(battle_map, teams, test_draconic_sorcerer_5lvl, test_bugbear, effect_tracker):
    """
    A scenario with two combatants starting a bit apart from each other. One needs to move to a coord farther behind the other.
    The destination just within reach if the combatant uses all its movement plus Misty Step.
    """
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([2, 5]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([5, 5]))
    path = battle_map.get_path_to_coord(test_draconic_sorcerer_5lvl, np.array([14, 5]))
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    threat, max_threat_path = calc_threat_for_path_with_misty_step(path, test_draconic_sorcerer_5lvl, effect_to_coords)
    assert threat[0] == 0  # Out of the danger zone

    actions = []
    ms_factory = MistyStepFactory(test_draconic_sorcerer_5lvl, test_draconic_sorcerer_5lvl.spellslots)
    decode_ms_path_to_actions(test_draconic_sorcerer_5lvl, battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get()[0], max_threat_path, actions, ms_factory)
    # Many different combinations are valid we just assert that Misty Step is used exactly once and the length of the path checks out
    assert sum(1 for a in actions if isinstance(a, MistyStep)) == 1
    assert len(actions) == 7


def test_ranged_spell_with_enemy_adjacent(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_bugbear):
    """
    This test case asserts that a ranged spell causes a lower threat whenever there's an enemy adjacent
    """
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([3, 14]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 13]))

    ff = FireboltFactory(6, Action.FIREBOLT, test_draconic_sorcerer_5lvl, test_draconic_sorcerer_5lvl.spellslots)
    firebolt = ff.create(test_bugbear)
    threat_enemy_adjacent = firebolt.calculate_threat()
    battle_map.move_combatant(test_draconic_sorcerer_5lvl, np.array([2, 14]))
    firebolt.clear_cache()
    threat_no_enemy_adjacent = firebolt.calculate_threat()
    assert threat_no_enemy_adjacent > threat_enemy_adjacent


def test_ranged_attack_with_enemy_adjacent(battle_map, teams, effect_tracker, test_goblin, test_bugbear):
    """
    This test case asserts that a ranged attack causes a lower threat whenever there's an enemy adjacent
    """
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_goblin, np.array([3, 14]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 13]))

    shortbow = test_goblin.shortbow[1].create(test_bugbear)
    threat_enemy_adjacent = shortbow.calculate_threat()
    battle_map.move_combatant(test_goblin, np.array([2, 14]))
    # shortbow.clear_cache()
    threat_no_enemy_adjacent = shortbow.calculate_threat()
    assert threat_no_enemy_adjacent > threat_enemy_adjacent

