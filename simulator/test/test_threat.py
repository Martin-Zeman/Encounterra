import copy

import numpy as np
import pytest
from simulator.action_types import Action
from simulator.battle_map import CombatantCoords
from simulator.misc import Size
from simulator.spells.hunger_of_hadar import HungerOfHadarFactory
from simulator.teams import Teams
from simulator.test.fixtures import combatant1, combatant2, combatant3, combatant4, teams, effect_tracker, battle_map
from simulator.threat import accumulate_threat_along_path


def test_get_path_to_medium_to_medium_one_aoe(battle_map, teams, combatant1, combatant2, effect_tracker):
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    hohf = HungerOfHadarFactory(15, Action.HUNGER_OF_HADAR, combatant2)
    hoh = hohf.create(np.array([7, 3]))
    effect_tracker.add(hoh, hoh.factory.caster)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([1, 3])))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([13, 3])))
    path = battle_map.get_path_to(combatant1, combatant2)
    threat = accumulate_threat_along_path(battle_map, path, combatant1)
    assert threat == pytest.approx(-9.1, 0.1)


def test_get_path_to_large_to_medium_one_aoe(battle_map, teams, combatant1, combatant2, effect_tracker):
    """
    Make it so that the large combatant is only hit by the AoE due to its size. The moving combatant is of size large. Make sure the
    threat is only added once per AoE.
    """
    combatant1.size = Size.LARGE
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    hohf = HungerOfHadarFactory(15, Action.HUNGER_OF_HADAR, combatant2)
    hoh = hohf.create(np.array([4, 6]))
    effect_tracker.add(hoh, hoh.factory.caster)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([1, 1]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([7, 1])))
    path = battle_map.get_path_to(combatant1, combatant2)
    threat = accumulate_threat_along_path(battle_map, path, combatant1)
    assert threat == pytest.approx(-9.1, 0.1)


def test_get_path_to_large_to_medium_avoided_aoe(battle_map, teams, combatant1, combatant2, effect_tracker):
    """
    Make it so that the large combatant just narrowly skirts the outside of the AoE
    """
    combatant1.size = Size.LARGE
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    hohf = HungerOfHadarFactory(15, Action.HUNGER_OF_HADAR, combatant2)
    hoh = hohf.create(np.array([4, 7]))
    effect_tracker.add(hoh, hoh.factory.caster)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([1, 1]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([7, 1])))
    path = battle_map.get_path_to(combatant1, combatant2)
    threat = accumulate_threat_along_path(battle_map, path, combatant1)
    assert threat == 0


def test_get_path_to_medium_to_medium_two_overlapping_aoe(battle_map, teams, combatant1, combatant2, effect_tracker):
    """
    Two overlapping AoEs. Make sure the threats are added up.
    """
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    hohf = HungerOfHadarFactory(15, Action.HUNGER_OF_HADAR, combatant2)
    hoh = hohf.create(np.array([7, 3]))
    effect_tracker.add(hoh, hoh.factory.caster)
    hoh = hohf.create(np.array([6, 3]))
    effect_tracker.add(hoh, hoh.factory.caster)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([1, 3])))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([13, 3])))
    path = battle_map.get_path_to(combatant1, combatant2)
    threat = accumulate_threat_along_path(battle_map, path, combatant1)
    assert threat == pytest.approx(-18.2, 0.1)

def test_get_path_to_large_to_medium_two_overlapping_aoe(battle_map, teams, combatant1, combatant2, effect_tracker):
    """
    Two overlapping AoEs. Make sure the threats are added up. The moving combatant is of size large. Make sure the
    threat is only added once per AoE.
    """
    combatant1.size = Size.LARGE
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    hohf = HungerOfHadarFactory(15, Action.HUNGER_OF_HADAR, combatant2)
    hoh = hohf.create(np.array([7, 3]))
    effect_tracker.add(hoh, hoh.factory.caster)
    hoh = hohf.create(np.array([6, 3]))
    effect_tracker.add(hoh, hoh.factory.caster)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 3]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([13, 3])))
    path = battle_map.get_path_to(combatant1, combatant2)
    threat = accumulate_threat_along_path(battle_map, path, combatant1)
    assert threat == pytest.approx(-18.2, 0.1)


def test_get_path_to_large_to_medium_starting_inside_aoe(battle_map, teams, combatant1, combatant2, effect_tracker):
    """
    The large combatant starts already inside the AoE. No threat should be accumulated.
    """
    combatant1.size = Size.LARGE
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    hohf = HungerOfHadarFactory(15, Action.HUNGER_OF_HADAR, combatant2)
    hoh = hohf.create(np.array([7, 3]))
    effect_tracker.add(hoh, hoh.factory.caster)
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([5, 3]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([13, 3])))
    path = battle_map.get_path_to(combatant1, combatant2)
    threat = accumulate_threat_along_path(battle_map, path, combatant1)
    assert threat == 0


def test_get_path_to_medium_to_medium_pass_by_one_aoo(battle_map, teams, combatant1, combatant2,combatant3, effect_tracker):
    """
    Basic AoO test. Combatant passes by one enemy on a way to another. All are of medium size.
    """
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([1, 3])))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([13, 3])))
    battle_map.set_combatant_coordinates(combatant3, CombatantCoords(np.array([6, 4])))
    path = battle_map.get_path_to(combatant1, combatant2)
    threat = accumulate_threat_along_path(battle_map, path, combatant1)
    assert threat == pytest.approx(-5.39, 0.1)


def test_get_path_to_medium_to_medium_pass_by_two_aoo(battle_map, teams, combatant1, combatant2, combatant3, effect_tracker):
    """
    Same as the basic AoO test but this time the combatant passes by two enemies the way to another. All are of medium size.
    """
    combatant4 = copy.deepcopy(combatant3)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(combatant4, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([1, 3])))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([13, 3])))
    battle_map.set_combatant_coordinates(combatant3, CombatantCoords(np.array([6, 4])))
    battle_map.set_combatant_coordinates(combatant4, CombatantCoords(np.array([7, 4])))
    path = battle_map.get_path_to(combatant1, combatant2)
    threat = accumulate_threat_along_path(battle_map, path, combatant1)
    assert threat == pytest.approx(2*-5.39, 0.1)


def test_get_path_to_large_to_medium_pass_by_two_aoo(battle_map, teams, combatant1, combatant2, combatant3, effect_tracker):
    """
    Same as the basic AoO test but this time the combatant passes by two enemies the way to another. The moving combatant is of size large.
    Make sure the AoO threat is only added once per enemy.
    """
    combatant1.size = Size.LARGE
    combatant4 = copy.deepcopy(combatant3)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(combatant4, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([1, 2]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([13, 3])))
    battle_map.set_combatant_coordinates(combatant3, CombatantCoords(np.array([6, 4])))
    battle_map.set_combatant_coordinates(combatant4, CombatantCoords(np.array([7, 4])))
    path = battle_map.get_path_to(combatant1, combatant2)
    threat = accumulate_threat_along_path(battle_map, path, combatant1)
    assert threat == pytest.approx(2*-5.39, 0.1)


def test_get_path_to_medium_stepping_away_from_medium_aoo(battle_map, teams, combatant1, combatant2, effect_tracker):
    """
    Starts with two adjacent combatants who are enemies. Calculates the threat of one stepping away from the other.
    """
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([3, 3])))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([3, 2])))
    path = battle_map.get_path_to(combatant1, np.array([3, 5]))
    threat = accumulate_threat_along_path(battle_map, path, combatant1)
    assert threat == pytest.approx(-2.64, 0.1)


def test_get_path_to_large_stepping_away_from_huge_aoo(battle_map, teams, combatant1, combatant2, effect_tracker):
    """
    Starts with two adjacent combatants who are enemies. Calculates the threat of one stepping away from the other. The moving combatant
    is large and the stationary one is huge.
    """
    combatant1.size = Size.LARGE
    combatant2.size = Size.HUGE
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([1, 4]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([1, 1]), combatant2.size))
    path = battle_map.get_path_to(combatant1, np.array([1, 5]))
    threat = accumulate_threat_along_path(battle_map, path, combatant1)
    assert threat == pytest.approx(-2.64, 0.1)

def test_get_path_to_large_stepping_away_from_two_medium_aoo(battle_map, teams, combatant1, combatant2, combatant3, effect_tracker):
    """
    Starts with three adjacent combatant. One large and his two medium enemies. Calculates the threat of one stepping away from the other two.
    """
    combatant1.size = Size.LARGE
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([3, 3]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([3, 2])))
    battle_map.set_combatant_coordinates(combatant3, CombatantCoords(np.array([4, 2])))
    path = battle_map.get_path_to(combatant1, np.array([3, 5]))
    threat = accumulate_threat_along_path(battle_map, path, combatant1)
    assert threat == pytest.approx(-2.64 - 5.39, 0.1)


def test_get_path_to_large_to_medium_pass_between_two_aoo_arrive_by_third(battle_map, teams, combatant1, combatant2, combatant3, combatant4, effect_tracker):
    """
    Same as the basic AoO test but this time the combatant passes by two enemies on either side the way to another. The moving combatant is of size large.
    Make sure the AoO threat is only added once per enemy and that the last enemy doesn't incur any threat
    """
    combatant1.size = Size.LARGE
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(combatant4, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([2, 1]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([1, 4])))
    battle_map.set_combatant_coordinates(combatant3, CombatantCoords(np.array([4, 4])))
    battle_map.set_combatant_coordinates(combatant4, CombatantCoords(np.array([2, 8])))
    path = battle_map.get_path_to(combatant1, combatant4)
    threat = accumulate_threat_along_path(battle_map, path, combatant1)
    assert threat == pytest.approx(-2.64 - 5.39, 0.1)


def test_get_path_to_large_to_medium_pass_between_two_aoo_through_aoe_arrive_by_third(battle_map, teams, combatant1, combatant2, combatant3, combatant4, effect_tracker):
    """
    This test combines AoE and AoO.
    Same as the basic AoO test but this time the combatant passes by two enemies on either side the way to another. The moving combatant is of size large.
    Make sure the AoO threat is only added once per enemy and that the last enemy doesn't incur any threat. Additionally, make sure the threat
    from the AoE is included.
    """
    combatant1.size = Size.LARGE
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(combatant4, Teams.Color.RED)  # For the log coloring...
    battle_map.build_adjacency_matrix()
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([2, 1]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([1, 4])))
    battle_map.set_combatant_coordinates(combatant3, CombatantCoords(np.array([4, 4])))
    battle_map.set_combatant_coordinates(combatant4, CombatantCoords(np.array([2, 8])))
    hohf = HungerOfHadarFactory(15, Action.HUNGER_OF_HADAR, combatant2)
    hoh = hohf.create(np.array([3, 8]))
    effect_tracker.add(hoh, hoh.factory.caster)
    path = battle_map.get_path_to(combatant1, combatant4)
    threat = accumulate_threat_along_path(battle_map, path, combatant1)
    assert threat == pytest.approx(-2.64 - 5.39 - 9.1, 0.1)
