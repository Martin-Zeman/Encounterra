import copy
import numpy as np
import pytest

from simulator.action_resolver import ActionResolver
from simulator.actions.movement import MovementIncrement
from simulator.battle_map import Terrain
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.misc import Conditions
from simulator.spells.fireball import Fireball
from simulator.spells.firebolt import Firebolt
from simulator.spells.spell import SpellStats
from simulator.spells.twinned_firebolt import TwinnedFirebolt
from simulator.teams import Teams
from simulator.test.fixtures import combatant1, combatant2, combatant3, test_totem_barbarian, combatant5, combatant6, teams, effect_tracker, battle_map
from simulator.actions.action_selector import get_best_actions, get_action


def test_error_case_1(battle_map, teams, effect_tracker, combatant1, combatant3):
    """
    This test case is based on a scenario encountered during fuzzy testing. We make sure that combatant1 doesn't hit
    itself with a fireball.
    """
    CustomLogger(LogLevel.WARNING)
    battle_map.place_circular_element(np.array([7, 10]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([10, 2]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([3, 2]), Terrain.DIFFICULT_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([5, 4]), Terrain.DIFFICULT_TERRAIN, diameter=1)
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(combatant1, np.array([3, 14]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(combatant3, np.array([4, 13]))  # Have to set it for fireball placement

    distances, shortest_paths = battle_map.calc_dijkstra(combatant1)
    best_actions = get_best_actions(combatant1, battle_map, distances, shortest_paths)
    new_coord = copy.copy(battle_map.get_combatant_position(combatant1).get())
    for ba in best_actions:
        new_coord += ba.increment if isinstance(ba, MovementIncrement) else np.array([[0, 0]])
    fireball = best_actions[0] if isinstance(best_actions[0], Fireball) else best_actions[1]
    # Staying still is actually preferable here
    assert battle_map.get_cartesian_distance(battle_map.get_combatant_position(combatant1).get(), np.array([fireball.coord])) > SpellStats.TRANSLATE_RADIUS[fireball.factory.target]
    assert isinstance(best_actions[0], Fireball) or isinstance(best_actions[0], Firebolt)
    assert isinstance(best_actions[1], Fireball) or isinstance(best_actions[1], Firebolt)

def test_error_case_2(battle_map, teams, effect_tracker, combatant1, combatant3):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    combatant4 = copy.deepcopy(combatant3)
    battle_map.place_circular_element(np.array([6, 2]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([14, 0]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([13, 14]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([14, 14]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([9, 4]), Terrain.DIFFICULT_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([7, 14]), Terrain.DIFFICULT_TERRAIN, diameter=1)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)
    teams.add_combatant_to_team(combatant4, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, np.array([0, 8]))
    battle_map.set_combatant_coordinates(combatant3, np.array([1, 9]))
    battle_map.set_combatant_coordinates(combatant4, np.array([2, 9]))
    battle_map.build_adjacency_matrix()

    distances, shortest_paths = battle_map.calc_dijkstra(combatant1)
    best_actions = get_best_actions(combatant1, battle_map, distances, shortest_paths)
    fireball = best_actions[0] if isinstance(best_actions[0], Fireball) else best_actions[1]
    assert battle_map.get_cartesian_distance(battle_map.get_combatant_position(combatant1).get(), np.array([fireball.coord])) > SpellStats.TRANSLATE_RADIUS[fireball.factory.target]
    assert battle_map.get_cartesian_distance(combatant3, np.array([fireball.coord])) <= SpellStats.TRANSLATE_RADIUS[fireball.factory.target]
    assert battle_map.get_cartesian_distance(combatant4, np.array([fireball.coord])) <= SpellStats.TRANSLATE_RADIUS[fireball.factory.target]
    assert isinstance(best_actions[0], Fireball) or isinstance(best_actions[1], Fireball)
    assert isinstance(best_actions[0], TwinnedFirebolt) or isinstance(best_actions[1], TwinnedFirebolt)


def test_error_case_3(battle_map, teams, effect_tracker, combatant1, combatant3, test_totem_barbarian, combatant5, combatant6):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    combatant7 = copy.deepcopy(combatant3)
    battle_map.place_circular_element(np.array([6, 2]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([14, 8]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([1, 3]), Terrain.DIFFICULT_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([1, 8]), Terrain.DIFFICULT_TERRAIN, diameter=1)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant1, combatant3, test_totem_barbarian, combatant5, combatant6, combatant7]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.RED)  # Faurung
    teams.add_combatant_to_team(combatant3, Teams.Color.BLUE)  # Bugbear 1
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # TotemBarbarian5Lvl
    teams.add_combatant_to_team(combatant5, Teams.Color.RED)  # StoneGiant
    teams.add_combatant_to_team(combatant6, Teams.Color.BLUE)  # Ogre
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # Bugbear 2
    battle_map.set_combatant_coordinates(combatant1, np.array([14, 13]))
    battle_map.set_combatant_coordinates(combatant3, np.array([3, 11]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([3, 12]))
    battle_map.set_combatant_coordinates(combatant5, np.array([0, 11]))
    battle_map.set_combatant_coordinates(combatant6, np.array([3, 9]))
    battle_map.set_combatant_coordinates(combatant7, np.array([9, 12]))
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
        actoid2 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid2, combatant1)
        actoid3 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid3, combatant1)
        actoid4 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid4, combatant1)
        actoid5 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid5, combatant1)
        actoid6 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid6, combatant1)
        actoid7 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid7, combatant1)
        actoid8 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid8, combatant1)
        actoid9 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid9, combatant1)
    except Exception as e:
        assert False, f"Raised an exception {e}"

def test_error_case_4(battle_map, teams, effect_tracker, combatant1, test_totem_barbarian, combatant5):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    combatant6 = copy.deepcopy(combatant1)
    battle_map.place_circular_element(np.array([2, 13]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([3, 7]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([4, 5]), Terrain.DIFFICULT_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([5, 1]), Terrain.DIFFICULT_TERRAIN, diameter=1)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant1, test_totem_barbarian, combatant5, combatant6]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # Faurung 1
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # TotemBarbarian5Lvl
    teams.add_combatant_to_team(combatant5, Teams.Color.RED)  # StoneGiant
    teams.add_combatant_to_team(combatant6, Teams.Color.RED)  # Faurung 2
    battle_map.set_combatant_coordinates(combatant1, np.array([9, 13]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([10, 9]))
    battle_map.set_combatant_coordinates(combatant5, np.array([4, 8]))
    battle_map.set_combatant_coordinates(combatant6, np.array([7, 8]))
    battle_map.build_adjacency_matrix()

    try:
        # The Danger Zone of the Stone Giant spans the whole map so it doesn't pay off to move and suffer the AoO
        actoid1 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
        actoid2 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid2, combatant1)
        actoid3 = get_action(combatant1, battle_map)
        assert actoid3 is None
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_5(battle_map, teams, effect_tracker, combatant1, combatant2, test_totem_barbarian, combatant5, combatant6):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    combatant7 = copy.deepcopy(combatant1)
    battle_map.place_circular_element(np.array([4, 13]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([8, 10]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([13, 8]), Terrain.DIFFICULT_TERRAIN, diameter=2)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant1, combatant2, test_totem_barbarian, combatant5, combatant6, combatant7]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # Faurung 1
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # Goblin
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)  # TotemBarbarian5Lvl
    teams.add_combatant_to_team(combatant5, Teams.Color.RED)  # StoneGiant
    teams.add_combatant_to_team(combatant6, Teams.Color.RED)  # Ogre
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # Faurung 2
    battle_map.set_combatant_coordinates(combatant1, np.array([14, 14]))  # Faurung 1
    battle_map.set_combatant_coordinates(combatant2, np.array([9, 14]))  # Goblin
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([10, 13]))  # TotemBarbarian5Lvl
    battle_map.set_combatant_coordinates(combatant5, np.array([0, 8]))  # StoneGiant
    battle_map.set_combatant_coordinates(combatant6, np.array([10, 10]))   # Ogre
    battle_map.set_combatant_coordinates(combatant7, np.array([7, 8]))  # Faurung 2
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
        actoid2 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid2, combatant1)
        actoid3 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid3, combatant1)
        actoid4 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid4, combatant1)
        actoid5 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid5, combatant1)
        actoid6 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid6, combatant1)
        actoid7 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid7, combatant1)
        actoid8 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid8, combatant1)
    except Exception as e:
        assert False, f"Raised an exception {e}"

def test_error_case_6(battle_map, teams, effect_tracker, combatant1, combatant3, test_totem_barbarian, combatant6):
    """
    This test case is based on a scenario encountered during fuzzy testing. The purpose of this test is to make sure we don't enter
    into an endless recursion via the Barbarian's Reckless Attack.
    """
    CustomLogger(LogLevel.WARNING)
    combatant7 = copy.deepcopy(test_totem_barbarian)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant3, test_totem_barbarian, combatant6, combatant7]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # Faurung
    teams.add_combatant_to_team(combatant3, Teams.Color.BLUE)  # Bugbear
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)  # TotemBarbarian5Lvl 1
    teams.add_combatant_to_team(combatant6, Teams.Color.BLUE)  # Ogre
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # TotemBarbarian5Lvl 2
    battle_map.set_combatant_coordinates(combatant1, np.array([5, 5]))  # Bugbear
    battle_map.set_combatant_coordinates(combatant3, np.array([14, 14]))  # Bugbear
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([9, 14]))  # TotemBarbarian5Lvl 1
    battle_map.set_combatant_coordinates(combatant6, np.array([10, 13]))  # Ogre
    battle_map.set_combatant_coordinates(combatant7, np.array([0, 8]))  # TotemBarbarian5Lvl 2
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid1, test_totem_barbarian)
        actoid2 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid2, test_totem_barbarian)
        actoid3 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid3, test_totem_barbarian)
        actoid4 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid4, test_totem_barbarian)
        actoid5 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid5, test_totem_barbarian)
        actoid6 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid6, test_totem_barbarian)
        actoid7 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid7, test_totem_barbarian)
        actoid8 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid8, test_totem_barbarian)
        actoid9 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid9, test_totem_barbarian)
        actoid10 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid10, test_totem_barbarian)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_7(battle_map, teams, effect_tracker, combatant1, combatant2, test_totem_barbarian):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    combatant6 = copy.deepcopy(combatant1)
    battle_map.place_circular_element(np.array([0, 6]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([11, 13]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([13, 1]), Terrain.DIFFICULT_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([10, 12]), Terrain.DIFFICULT_TERRAIN, diameter=1)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant1, test_totem_barbarian, combatant5, combatant6]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # Faurung 1
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # Goblin
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # TotemBarbarian5Lvl
    battle_map.set_combatant_coordinates(combatant1, np.array([9, 13]))
    battle_map.set_combatant_coordinates(combatant2, np.array([10, 9]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([4, 8]))
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(combatant2, battle_map)
        action_resolver.resolve_action(actoid1, combatant2)
        actoid2 = get_action(combatant2, battle_map)
        action_resolver.resolve_action(actoid2, combatant2)
        actoid3 = get_action(combatant2, battle_map)
        action_resolver.resolve_action(actoid3, combatant2)
        actoid4 = get_action(combatant2, battle_map)
        action_resolver.resolve_action(actoid4, combatant2)
        actoid5 = get_action(combatant2, battle_map)
        action_resolver.resolve_action(actoid5, combatant2)
        actoid6 = get_action(combatant2, battle_map)
        action_resolver.resolve_action(actoid6, combatant2)

        actoid1 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
        actoid2 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid2, combatant1)
        actoid3 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid3, combatant1)
        actoid4 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid4, combatant1)
        actoid5 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid5, combatant1)
        actoid6 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid6, combatant1)
        actoid7 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid7, combatant1)
        actoid8 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid8, combatant1)

        actoid1 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid1, test_totem_barbarian)
        actoid2 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid2, test_totem_barbarian)
        actoid3 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid3, test_totem_barbarian)
        actoid4 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid4, test_totem_barbarian)
        actoid5 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid5, test_totem_barbarian)
        actoid6 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid6, test_totem_barbarian)
        actoid7 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid7, test_totem_barbarian)
        actoid8 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid8, test_totem_barbarian)
        actoid9 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid9, test_totem_barbarian)
        actoid10 = get_action(test_totem_barbarian, battle_map)
        action_resolver.resolve_action(actoid10, test_totem_barbarian)
    except Exception as e:
        assert False, f"Raised an exception {e}"

def test_error_case_8(battle_map, teams, effect_tracker, combatant1, combatant5, combatant6):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    combatant7 = copy.deepcopy(combatant1)
    battle_map.place_circular_element(np.array([4, 12]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([0, 1]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([6, 12]), Terrain.DIFFICULT_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([14, 13]), Terrain.DIFFICULT_TERRAIN, diameter=2)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant1, combatant5, combatant6, combatant7]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # Faurung 1
    teams.add_combatant_to_team(combatant5, Teams.Color.RED)  # StoneGiant
    teams.add_combatant_to_team(combatant6, Teams.Color.RED)  # Ogre
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # Faurung 2
    battle_map.set_combatant_coordinates(combatant1, np.array([10, 10]))  # Faurung 1
    battle_map.set_combatant_coordinates(combatant5, np.array([0, 12]))  # StoneGiant
    battle_map.set_combatant_coordinates(combatant6, np.array([9, 13]))   # Ogre
    battle_map.set_combatant_coordinates(combatant7, np.array([8, 13]))  # Faurung 2
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(combatant7, battle_map)
        action_resolver.resolve_action(actoid1, combatant7)
        actoid2 = get_action(combatant7, battle_map)
        action_resolver.resolve_action(actoid2, combatant7)
        actoid3 = get_action(combatant7, battle_map)
        action_resolver.resolve_action(actoid3, combatant7)
        actoid4 = get_action(combatant7, battle_map)
        action_resolver.resolve_action(actoid4, combatant7)
        actoid5 = get_action(combatant7, battle_map)
        action_resolver.resolve_action(actoid5, combatant7)
        actoid6 = get_action(combatant7, battle_map)
        action_resolver.resolve_action(actoid6, combatant7)
        actoid7 = get_action(combatant7, battle_map)
        action_resolver.resolve_action(actoid7, combatant7)
        actoid8 = get_action(combatant7, battle_map)
        action_resolver.resolve_action(actoid8, combatant7)
    except Exception as e:
        assert False, f"Raised an exception {e}"

def test_error_case_9(battle_map, teams, effect_tracker, combatant1, combatant5, combatant6):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    combatant7 = copy.deepcopy(combatant5)
    combatant8 = copy.deepcopy(combatant6)
    battle_map.place_circular_element(np.array([10, 10]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([13, 14]), Terrain.DIFFICULT_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([6, 0]), Terrain.DIFFICULT_TERRAIN, diameter=2)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant1, combatant5, combatant6, combatant7, combatant8]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # Faurung 1
    teams.add_combatant_to_team(combatant5, Teams.Color.BLUE)  # StoneGiant 1
    teams.add_combatant_to_team(combatant6, Teams.Color.BLUE)  # Ogre 1
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # Stone Giant 2
    teams.add_combatant_to_team(combatant8, Teams.Color.RED)  # Ogre 2
    battle_map.set_combatant_coordinates(combatant1, np.array([3, 5]))  # Faurung 1
    battle_map.set_combatant_coordinates(combatant5, np.array([12, 10]))  # StoneGiant 1
    battle_map.set_combatant_coordinates(combatant6, np.array([1, 10]))   # Ogre 1
    battle_map.set_combatant_coordinates(combatant7, np.array([3, 8]))  # Stone Giant 2
    battle_map.set_combatant_coordinates(combatant8, np.array([12, 8]))  # Ogre 2
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(combatant5, battle_map)
        action_resolver.resolve_action(actoid1, combatant5)
        actoid2 = get_action(combatant5, battle_map)
        action_resolver.resolve_action(actoid2, combatant5)

        actoid3 = get_action(combatant7, battle_map)
        action_resolver.resolve_action(actoid3, combatant7)

        actoid4 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid4, combatant1)
        actoid5 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid5, combatant1)

    except Exception as e:
        assert False, f"Raised an exception {e}"

def test_error_case_10(battle_map, teams, effect_tracker, combatant1, combatant2, combatant5):
    """
    This test case is based on a scenario encountered during fuzzy testing. Here the sorcerer is out of 3rd level spellslots.
    """
    CustomLogger(LogLevel.WARNING)
    battle_map.place_circular_element(np.array([3, 3]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([4, 13]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([5, 4]), Terrain.DIFFICULT_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([13, 1]), Terrain.DIFFICULT_TERRAIN, diameter=2)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant1, combatant5]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # Faurung 1
    teams.add_combatant_to_team(combatant5, Teams.Color.RED)  # StoneGiant 1
    battle_map.set_combatant_coordinates(combatant1, np.array([0, 3]))  # Faurung 1
    battle_map.set_combatant_coordinates(combatant5, np.array([3, 6]))   # Stone Giant 1
    battle_map.build_adjacency_matrix()
    combatant5.curr_hp = 52
    combatant1.spellslots.use_spellslot(3)
    combatant1.spellslots.use_spellslot(1)
    combatant1.spellslots.use_spellslot(1)
    combatant1.spellslots.use_spellslot(3)
    combatant1.curr_sorcery_points -= 4

    try:
        actoid1 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
        actoid2 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid2, combatant1)
        actoid3 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid3, combatant1)
        actoid4 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid4, combatant1)
        actoid5 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid5, combatant1)
        actoid6 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid6, combatant1)
        actoid7 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid7, combatant1)
        actoid8 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid8, combatant1)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_11(battle_map, teams, effect_tracker, combatant1, test_totem_barbarian, combatant5, combatant6):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    combatant7 = copy.deepcopy(combatant1)
    combatant8 = copy.deepcopy(combatant5)
    battle_map.place_circular_element(np.array([2, 4]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([7, 3]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([4, 1]), Terrain.DIFFICULT_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([9, 9]), Terrain.DIFFICULT_TERRAIN, diameter=2)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant1, test_totem_barbarian, combatant5, combatant6, combatant7, combatant8]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # Faurung 1
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # TotemBarbarian5Lvl 1
    teams.add_combatant_to_team(combatant5, Teams.Color.BLUE)  # StoneGiant 1
    teams.add_combatant_to_team(combatant6, Teams.Color.BLUE)  # Ogre 1
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # Faurung 2
    teams.add_combatant_to_team(combatant8, Teams.Color.RED)  # StoneGiant 2
    battle_map.set_combatant_coordinates(combatant1, np.array([7, 8]))  # Faurung 1
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([6, 12]))   # TotemBarbarian5Lvl 1
    battle_map.set_combatant_coordinates(combatant5, np.array([9, 9]))   # StoneGiant 1
    battle_map.set_combatant_coordinates(combatant6, np.array([6, 10]))   # Ogre 1
    battle_map.set_combatant_coordinates(combatant7, np.array([9, 12]))   # Faurung 2
    battle_map.set_combatant_coordinates(combatant8, np.array([3, 10]))   # StoneGiant 2
    battle_map.build_adjacency_matrix()

    test_totem_barbarian.curr_rage_uses -= 1
    combatant6.curr_hp -= 32
    combatant7.curr_hp -= 4
    combatant7.spellslots.use_spellslot(3)
    combatant7.curr_sorcery_points -= 5

    try:
        actoid1 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_12(battle_map, teams, effect_tracker, combatant1, test_totem_barbarian, combatant5, combatant6):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    combatant7 = copy.deepcopy(test_totem_barbarian)
    battle_map.place_circular_element(np.array([0, 7]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([7, 14]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([1, 10]), Terrain.DIFFICULT_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([6, 7]), Terrain.DIFFICULT_TERRAIN, diameter=1)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant1, test_totem_barbarian, combatant5, combatant6, combatant7]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # Faurung 1
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)  # TotemBarbarian5Lvl 1
    teams.add_combatant_to_team(combatant5, Teams.Color.RED)  # StoneGiant 1
    teams.add_combatant_to_team(combatant6, Teams.Color.BLUE)  # Ogre 1
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # TotemBarbarian5Lvl 2
    battle_map.set_combatant_coordinates(combatant1, np.array([7, 13]))  # Faurung 1
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([6, 11]))   # TotemBarbarian5Lvl 1
    battle_map.set_combatant_coordinates(combatant5, np.array([7, 10]))   # StoneGiant 1
    battle_map.set_combatant_coordinates(combatant6, np.array([10, 9]))   # Ogre 1
    battle_map.set_combatant_coordinates(combatant7, np.array([6, 12]))   # TotemBarbarian5Lvl 2
    battle_map.build_adjacency_matrix()

    test_totem_barbarian.curr_hp = 61

    combatant1.curr_hp = 7
    combatant1.spellslots.use_spellslot(3)
    combatant1.spellslots.use_spellslot(3)
    combatant1.spellslots.use_spellslot(1)
    combatant1.spellslots.use_spellslot(1)
    combatant1.curr_sorcery_points -= 5
    combatant1.apply_condition(Conditions.PRONE)

    combatant5.ammo[combatant5.rock[1].name] = 0
    combatant5.curr_hp = 46
    combatant6.curr_hp = 45
    combatant7.curr_hp = 36

    try:
        actoid1 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
        actoid2 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid2, combatant1)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_13(battle_map, teams, effect_tracker, combatant1, test_totem_barbarian, combatant5):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    combatant6 = copy.deepcopy(combatant5)
    battle_map.place_circular_element(np.array([1, 3]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([12, 14]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([3, 12]), Terrain.DIFFICULT_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([9, 11]), Terrain.DIFFICULT_TERRAIN, diameter=1)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant1, test_totem_barbarian, combatant5, combatant6]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # Faurung 1
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # TotemBarbarian5Lvl 1
    teams.add_combatant_to_team(combatant5, Teams.Color.BLUE)  # StoneGiant 1
    teams.add_combatant_to_team(combatant6, Teams.Color.RED)  # StoneGiant 2
    battle_map.set_combatant_coordinates(combatant1, np.array([5, 5]))  # Faurung 1
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([4, 6]))   # TotemBarbarian5Lvl 1
    battle_map.set_combatant_coordinates(combatant5, np.array([1, 10]))   # StoneGiant 1
    battle_map.set_combatant_coordinates(combatant6, np.array([8, 8]))   # TotemBarbarian5Lvl 2
    battle_map.build_adjacency_matrix()

    combatant1.curr_hp = 43
    combatant1.spellslots.use_spellslot(3)
    combatant1.spellslots.use_spellslot(3)
    combatant1.spellslots.use_spellslot(1)
    combatant1.curr_sorcery_points = 0

    try:
        actoid1 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
        actoid2 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid2, combatant1)
        actoid3 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid3, combatant1)
        actoid4 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid4, combatant1)
        actoid5 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid5, combatant1)
        actoid6 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid6, combatant1)
        actoid7 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid7, combatant1)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_14(battle_map, teams, effect_tracker, combatant1, combatant5, combatant6):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    battle_map.place_circular_element(np.array([4, 11]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([13, 10]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([10, 13]), Terrain.DIFFICULT_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([10, 2]), Terrain.DIFFICULT_TERRAIN, diameter=1)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant1, combatant5, combatant6]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.RED)  # Faurung 1
    teams.add_combatant_to_team(combatant5, Teams.Color.BLUE)  # StoneGiant 1
    teams.add_combatant_to_team(combatant6, Teams.Color.BLUE)  # Ogre 1
    battle_map.set_combatant_coordinates(combatant1, np.array([0, 14]))  # Faurung 1
    battle_map.set_combatant_coordinates(combatant5, np.array([0, 10]))   # StoneGiant 1
    battle_map.set_combatant_coordinates(combatant6, np.array([1, 13]))   # TotemBarbarian5Lvl 2
    battle_map.build_adjacency_matrix()

    combatant1.spellslots.use_spellslot(3)
    combatant1.spellslots.use_spellslot(1)
    combatant1.curr_sorcery_points = 2

    try:
        actoid1 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
        actoid2 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid2, combatant1)
        actoid3 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid3, combatant1)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_15(battle_map, teams, effect_tracker, combatant1, combatant2, test_totem_barbarian, combatant5, combatant6):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    # TODO Why is this not failing?
    CustomLogger(LogLevel.WARNING)
    battle_map.place_circular_element(np.array([0, 12]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([7, 10]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([10, 12]), Terrain.DIFFICULT_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([13, 6]), Terrain.DIFFICULT_TERRAIN, diameter=1)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant1, combatant2, test_totem_barbarian, combatant5, combatant6]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.RED)  # Faurung 1
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # Goblin 1
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)  # TotemBarbarian5Lvl 1
    teams.add_combatant_to_team(combatant5, Teams.Color.RED)  # StoneGiant 1
    teams.add_combatant_to_team(combatant6, Teams.Color.RED)  # Ogre 1
    battle_map.set_combatant_coordinates(combatant1, np.array([7, 8]))  # Faurung 1
    battle_map.set_combatant_coordinates(combatant2, np.array([0, 9]))  # Goblin 1
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([8, 7]))  # TotemBarbarian5Lvl 1
    battle_map.set_combatant_coordinates(combatant5, np.array([8, 12]))   # StoneGiant 1
    battle_map.set_combatant_coordinates(combatant6, np.array([9, 8]))   # Ogre 2
    battle_map.build_adjacency_matrix()

    combatant5.haste_action_factories = [1]  # Simulates that haste factories are not empty
    combatant1.spellslots.use_spellslot(3)
    combatant1.spellslots.use_spellslot(3)
    combatant1.spellslots.use_spellslot(1)
    combatant1.curr_sorcery_points = 0

    try:
        actoid1 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
        actoid2 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid2, combatant1)
        actoid3 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid3, combatant1)
        actoid4 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid4, combatant1)
        actoid5 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid5, combatant1)
        actoid6 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid6, combatant1)
        actoid7 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid7, combatant1)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_16(battle_map, teams, effect_tracker, combatant1, combatant2, combatant5, combatant6):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    battle_map.place_circular_element(np.array([7, 8]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([6, 13]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([8, 8]), Terrain.DIFFICULT_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([10, 11]), Terrain.DIFFICULT_TERRAIN, diameter=2)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant1, combatant5, combatant6]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.RED)  # Faurung 1
    teams.add_combatant_to_team(combatant5, Teams.Color.BLUE)  # StoneGiant 1
    teams.add_combatant_to_team(combatant6, Teams.Color.RED)  # Ogre 1
    battle_map.set_combatant_coordinates(combatant1, np.array([0, 2]))  # Faurung 1
    battle_map.set_combatant_coordinates(combatant5, np.array([11, 8]))   # StoneGiant 1
    battle_map.set_combatant_coordinates(combatant6, np.array([9, 10]))   # Ogre 2
    battle_map.build_adjacency_matrix()

    combatant1.spellslots.use_spellslot(3)
    combatant1.spellslots.use_spellslot(3)
    combatant1.curr_sorcery_points = 0
    combatant1.apply_condition(Conditions.PRONE)

    try:
        actoid1 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
        actoid2 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid2, combatant1)
        actoid3 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid3, combatant1)
        actoid4 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid4, combatant1)
        actoid5 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid5, combatant1)
        actoid6 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid6, combatant1)
        actoid7 = get_action(combatant1, battle_map)
        action_resolver.resolve_action(actoid7, combatant1)
    except Exception as e:
        assert False, f"Raised an exception {e}"
