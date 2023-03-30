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
    assert threat < 0

# def test_get_path_to_large_to_large(battle_map, combatant1, combatant2):
#     battle_map.build_adjacency_matrix()
#     combatant1.size = Size.LARGE
#     combatant2.size = Size.LARGE
#     battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1]), combatant1.size))
#     battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([5, 7]), combatant2.size))
#     path = battle_map.get_path_to(combatant1, combatant2)
#     assert np.array_equal(path, [np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([0, 1])])
#
# def test_get_path_to_medium_to_large(battle_map, combatant1, combatant2):
#     battle_map.build_adjacency_matrix()
#     combatant2.size = Size.LARGE
#     battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1])))
#     battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([5, 7]), combatant2.size))
#     path = battle_map.get_path_to(combatant1, combatant2)
#     assert np.array_equal(path, [np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([0, 1])]) or\
#            np.array_equal(path, [np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([1, 1])])
#
# def test_get_path_to_large_to_medium(battle_map, combatant1, combatant2):
#     battle_map.build_adjacency_matrix()
#     combatant1.size = Size.LARGE
#     battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1]), combatant1.size))
#     battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([5, 7])))
#     path = battle_map.get_path_to(combatant1, combatant2)
#     assert np.array_equal(path, [np.array([1, 1]), np.array([1, 1]), np.array([1, 1]), np.array([0, 1])])
#
# def test_get_path_to_large_to_medium2(battle_map, combatant1, combatant2):
#     battle_map.place_circular_element(np.array([7, 14]), Terrain.DIFFICULT_TERRAIN, diameter=1)
#     battle_map.place_circular_element(np.array([9, 14]), Terrain.DIFFICULT_TERRAIN, diameter=1)
#     battle_map.build_adjacency_matrix()
#     combatant1.size = Size.LARGE
#     battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([4, 13]), combatant1.size))
#     battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([8, 14])))
#     path = battle_map.get_path_to(combatant1, combatant2)
#     assert np.array_equal(path, [np.array([1, 0]), np.array([1, 0])])
#
# def test_get_path_to_huge_to_huge(battle_map, combatant1, combatant2):
#     battle_map.build_adjacency_matrix()
#     combatant1.size = Size.HUGE
#     combatant2.size = Size.HUGE
#     battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([0, 1]), combatant1.size))
#     battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([5, 7]), combatant2.size))
#     path = battle_map.get_path_to(combatant1, combatant2)
#     assert np.array_equal(path, [np.array([1, 1]), np.array([1, 1]), np.array([0, 1])])