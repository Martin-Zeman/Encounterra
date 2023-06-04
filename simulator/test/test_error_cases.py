import copy
import numpy as np
import pytest

from simulator.action_resolver import ActionResolver
from simulator.actions.action_types import BonusAction
from simulator.actions.movement import MovementIncrement
from simulator.battle_map import Terrain
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.misc import Conditions
from simulator.spells.fireball import Fireball
from simulator.spells.firebolt import Firebolt
from simulator.spells.spell import SpellStats
from simulator.spells.twinned_firebolt import TwinnedFirebolt
from simulator.teams import Teams
from simulator.test.fixtures import test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian, test_stone_giant,\
    test_ogre, test_moon_druid, teams, effect_tracker, battle_map
from simulator.actions.action_selector import get_best_actions, get_action
from simulator.utils.utils import preallocate_wildshape_forms


def test_error_case_1(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_bugbear):
    """
    This test case is based on a scenario encountered during fuzzy testing. We make sure that test_draconic_sorcerer_5lvl doesn't hit
    itself with a fireball.
    """
    CustomLogger(LogLevel.WARNING)
    battle_map.place_circular_element(np.array([7, 10]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([10, 2]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([3, 2]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([5, 4]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([3, 14]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 13]))  # Have to set it for fireball placement

    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    best_actions = get_best_actions(test_draconic_sorcerer_5lvl, battle_map, distances, shortest_paths)
    new_coord = copy.copy(battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get())
    for ba in best_actions:
        new_coord += ba.increment if isinstance(ba, MovementIncrement) else np.array([[0, 0]])
    fireball = best_actions[0] if isinstance(best_actions[0], Fireball) else best_actions[1]
    # Staying still is actually preferable here
    assert battle_map.get_cartesian_distance(battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get(), np.array([fireball.coord])) > SpellStats.TRANSLATE_RADIUS[fireball.factory.target]
    assert isinstance(best_actions[0], Fireball) or isinstance(best_actions[0], Firebolt)
    assert isinstance(best_actions[1], Fireball) or isinstance(best_actions[1], Firebolt)

def test_error_case_2(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_bugbear):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    test_bugbear_2 = copy.deepcopy(test_bugbear)
    battle_map.place_circular_element(np.array([6, 2]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([14, 0]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([13, 14]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([14, 14]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([9, 4]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([7, 14]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    teams.add_combatant_to_team(test_bugbear_2, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 8]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([1, 9]))
    battle_map.set_combatant_coordinates(test_bugbear_2, np.array([2, 9]))
    battle_map.build_adjacency_matrix()

    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    best_actions = get_best_actions(test_draconic_sorcerer_5lvl, battle_map, distances, shortest_paths)
    fireball = best_actions[0] if isinstance(best_actions[0], Fireball) else best_actions[1]
    assert battle_map.get_cartesian_distance(battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get(), np.array([fireball.coord])) > SpellStats.TRANSLATE_RADIUS[fireball.factory.target]
    assert battle_map.get_cartesian_distance(test_bugbear, np.array([fireball.coord])) <= SpellStats.TRANSLATE_RADIUS[fireball.factory.target]
    assert battle_map.get_cartesian_distance(test_bugbear_2, np.array([fireball.coord])) <= SpellStats.TRANSLATE_RADIUS[fireball.factory.target]
    assert isinstance(best_actions[0], Fireball) or isinstance(best_actions[1], Fireball)
    assert isinstance(best_actions[0], TwinnedFirebolt) or isinstance(best_actions[1], TwinnedFirebolt)


def test_error_case_3(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_bugbear, test_totem_barbarian, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    combatant7 = copy.deepcopy(test_bugbear)
    battle_map.place_circular_element(np.array([6, 2]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([14, 8]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([1, 3]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([1, 8]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_draconic_sorcerer_5lvl, test_bugbear, test_totem_barbarian, test_stone_giant, test_ogre, combatant7]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.RED)  # DraconicSorcerer5Lvl
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)  # Bugbear 1
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # TotemBarbarian5Lvl
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)  # StoneGiant
    teams.add_combatant_to_team(test_ogre, Teams.Color.BLUE)  # Ogre
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # Bugbear 2
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([14, 13]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([3, 11]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([3, 12]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([0, 11]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([3, 9]))
    battle_map.set_combatant_coordinates(combatant7, np.array([9, 12]))
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
        actoid4 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)
        actoid6 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid6, test_draconic_sorcerer_5lvl)
        actoid7 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid7, test_draconic_sorcerer_5lvl)
        actoid8 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid8, test_draconic_sorcerer_5lvl)
        actoid9 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid9, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"

def test_error_case_4(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    test_draconic_sorcerer_5lvl_2 = copy.deepcopy(test_draconic_sorcerer_5lvl)
    battle_map.place_circular_element(np.array([2, 13]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([3, 7]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([4, 5]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([5, 1]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant, test_draconic_sorcerer_5lvl_2]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # DraconicSorcerer5Lvl 1
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # TotemBarbarian5Lvl
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)  # StoneGiant
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl_2, Teams.Color.RED)  # DraconicSorcerer5Lvl 2
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([9, 13]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([10, 9]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([4, 8]))
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl_2, np.array([7, 8]))
    battle_map.build_adjacency_matrix()

    try:
        # The Danger Zone of the Stone Giant spans the whole map so it doesn't pay off to move and suffer the AoO
        actoid1 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        assert actoid3 is None
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_5(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_totem_barbarian, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    test_draconic_sorcerer_5lvl_2 = copy.deepcopy(test_draconic_sorcerer_5lvl)
    battle_map.place_circular_element(np.array([4, 13]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([8, 10]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([13, 8]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_draconic_sorcerer_5lvl, test_goblin, test_totem_barbarian, test_stone_giant, test_ogre, test_draconic_sorcerer_5lvl_2]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # DraconicSorcerer5Lvl 1
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # Goblin
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)  # TotemBarbarian5Lvl
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)  # StoneGiant
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)  # Ogre
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl_2, Teams.Color.RED)  # DraconicSorcerer5Lvl 2
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([14, 14]))  # DraconicSorcerer5Lvl 1
    battle_map.set_combatant_coordinates(test_goblin, np.array([9, 14]))  # Goblin
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([10, 13]))  # TotemBarbarian5Lvl
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([0, 8]))  # StoneGiant
    battle_map.set_combatant_coordinates(test_ogre, np.array([10, 10]))   # Ogre
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl_2, np.array([7, 8]))  # DraconicSorcerer5Lvl 2
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
        actoid4 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)
        actoid6 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid6, test_draconic_sorcerer_5lvl)
        actoid7 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid7, test_draconic_sorcerer_5lvl)
        actoid8 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid8, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"

def test_error_case_6(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_bugbear, test_totem_barbarian, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing. The purpose of this test is to make sure we don't enter
    into an endless recursion via the Barbarian's Reckless Attack.
    """
    CustomLogger(LogLevel.WARNING)
    combatant7 = copy.deepcopy(test_totem_barbarian)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_bugbear, test_totem_barbarian, test_ogre, combatant7]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # DraconicSorcerer5Lvl
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)  # Bugbear
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)  # TotemBarbarian5Lvl 1
    teams.add_combatant_to_team(test_ogre, Teams.Color.BLUE)  # Ogre
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # TotemBarbarian5Lvl 2
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 5]))  # Bugbear
    battle_map.set_combatant_coordinates(test_bugbear, np.array([14, 14]))  # Bugbear
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([9, 14]))  # TotemBarbarian5Lvl 1
    battle_map.set_combatant_coordinates(test_ogre, np.array([10, 13]))  # Ogre
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


def test_error_case_7(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_totem_barbarian):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    test_draconic_sorcerer_5lvl_2 = copy.deepcopy(test_draconic_sorcerer_5lvl)
    battle_map.place_circular_element(np.array([0, 6]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([11, 13]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([13, 1]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([10, 12]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant, test_draconic_sorcerer_5lvl_2]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # DraconicSorcerer5Lvl 1
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # Goblin
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # TotemBarbarian5Lvl
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([9, 13]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([10, 9]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([4, 8]))
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(test_goblin, battle_map)
        action_resolver.resolve_action(actoid1, test_goblin)
        actoid2 = get_action(test_goblin, battle_map)
        action_resolver.resolve_action(actoid2, test_goblin)
        actoid3 = get_action(test_goblin, battle_map)
        action_resolver.resolve_action(actoid3, test_goblin)
        actoid4 = get_action(test_goblin, battle_map)
        action_resolver.resolve_action(actoid4, test_goblin)
        actoid5 = get_action(test_goblin, battle_map)
        action_resolver.resolve_action(actoid5, test_goblin)
        actoid6 = get_action(test_goblin, battle_map)
        action_resolver.resolve_action(actoid6, test_goblin)

        actoid1 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
        actoid4 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)
        actoid6 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid6, test_draconic_sorcerer_5lvl)
        actoid7 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid7, test_draconic_sorcerer_5lvl)
        actoid8 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid8, test_draconic_sorcerer_5lvl)

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

def test_error_case_8(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    combatant7 = copy.deepcopy(test_draconic_sorcerer_5lvl)
    battle_map.place_circular_element(np.array([4, 12]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([0, 1]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([6, 12]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([14, 13]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_draconic_sorcerer_5lvl, test_stone_giant, test_ogre, combatant7]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # DraconicSorcerer5Lvl 1
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)  # StoneGiant
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)  # Ogre
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # DraconicSorcerer5Lvl 2
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([10, 10]))  # DraconicSorcerer5Lvl 1
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([0, 12]))  # StoneGiant
    battle_map.set_combatant_coordinates(test_ogre, np.array([9, 13]))   # Ogre
    battle_map.set_combatant_coordinates(combatant7, np.array([8, 13]))  # DraconicSorcerer5Lvl 2
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

def test_error_case_9(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    combatant7 = copy.deepcopy(test_stone_giant)
    combatant8 = copy.deepcopy(test_ogre)
    battle_map.place_circular_element(np.array([10, 10]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([13, 14]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([6, 0]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_draconic_sorcerer_5lvl, test_stone_giant, test_ogre, combatant7, combatant8]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # DraconicSorcerer5Lvl 1
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.BLUE)  # StoneGiant 1
    teams.add_combatant_to_team(test_ogre, Teams.Color.BLUE)  # Ogre 1
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # Stone Giant 2
    teams.add_combatant_to_team(combatant8, Teams.Color.RED)  # Ogre 2
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([3, 5]))  # DraconicSorcerer5Lvl 1
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([12, 10]))  # StoneGiant 1
    battle_map.set_combatant_coordinates(test_ogre, np.array([1, 10]))   # Ogre 1
    battle_map.set_combatant_coordinates(combatant7, np.array([3, 8]))  # Stone Giant 2
    battle_map.set_combatant_coordinates(combatant8, np.array([12, 8]))  # Ogre 2
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(test_stone_giant, battle_map)
        action_resolver.resolve_action(actoid1, test_stone_giant)
        actoid2 = get_action(test_stone_giant, battle_map)
        action_resolver.resolve_action(actoid2, test_stone_giant)

        actoid3 = get_action(combatant7, battle_map)
        action_resolver.resolve_action(actoid3, combatant7)

        actoid4 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)

    except Exception as e:
        assert False, f"Raised an exception {e}"

def test_error_case_10(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_stone_giant):
    """
    This test case is based on a scenario encountered during fuzzy testing. Here the sorcerer is out of 3rd level spellslots.
    """
    CustomLogger(LogLevel.WARNING)
    battle_map.place_circular_element(np.array([3, 3]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([4, 13]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([5, 4]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([13, 1]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_draconic_sorcerer_5lvl, test_stone_giant]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # DraconicSorcerer5Lvl 1
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)  # StoneGiant 1
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 3]))  # DraconicSorcerer5Lvl 1
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([3, 6]))   # Stone Giant 1
    battle_map.build_adjacency_matrix()
    test_stone_giant.curr_hp = 52
    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(3)
    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(1)
    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(1)
    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(3)
    test_draconic_sorcerer_5lvl.curr_sorcery_points -= 4

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
        actoid4 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)
        actoid6 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid6, test_draconic_sorcerer_5lvl)
        actoid7 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid7, test_draconic_sorcerer_5lvl)
        actoid8 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid8, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_11(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    combatant7 = copy.deepcopy(test_draconic_sorcerer_5lvl)
    combatant8 = copy.deepcopy(test_stone_giant)
    battle_map.place_circular_element(np.array([2, 4]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([7, 3]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([4, 1]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([9, 9]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant, test_ogre, combatant7, combatant8]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # DraconicSorcerer5Lvl 1
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # TotemBarbarian5Lvl 1
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.BLUE)  # StoneGiant 1
    teams.add_combatant_to_team(test_ogre, Teams.Color.BLUE)  # Ogre 1
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # DraconicSorcerer5Lvl 2
    teams.add_combatant_to_team(combatant8, Teams.Color.RED)  # StoneGiant 2
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([7, 8]))  # DraconicSorcerer5Lvl 1
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([6, 12]))   # TotemBarbarian5Lvl 1
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([9, 9]))   # StoneGiant 1
    battle_map.set_combatant_coordinates(test_ogre, np.array([6, 10]))   # Ogre 1
    battle_map.set_combatant_coordinates(combatant7, np.array([9, 12]))   # DraconicSorcerer5Lvl 2
    battle_map.set_combatant_coordinates(combatant8, np.array([3, 10]))   # StoneGiant 2
    battle_map.build_adjacency_matrix()

    test_totem_barbarian.curr_rage_uses -= 1
    test_ogre.curr_hp -= 32
    combatant7.curr_hp -= 4
    combatant7.spellslots.use_spellslot(3)
    combatant7.curr_sorcery_points -= 5

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_12(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    combatant7 = copy.deepcopy(test_totem_barbarian)
    battle_map.place_circular_element(np.array([0, 7]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([7, 14]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([1, 10]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([6, 7]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant, test_ogre, combatant7]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # DraconicSorcerer5Lvl 1
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)  # TotemBarbarian5Lvl 1
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)  # StoneGiant 1
    teams.add_combatant_to_team(test_ogre, Teams.Color.BLUE)  # Ogre 1
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # TotemBarbarian5Lvl 2
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([7, 13]))  # DraconicSorcerer5Lvl 1
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([6, 11]))   # TotemBarbarian5Lvl 1
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([7, 10]))   # StoneGiant 1
    battle_map.set_combatant_coordinates(test_ogre, np.array([10, 9]))   # Ogre 1
    battle_map.set_combatant_coordinates(combatant7, np.array([6, 12]))   # TotemBarbarian5Lvl 2
    battle_map.build_adjacency_matrix()

    test_totem_barbarian.curr_hp = 61

    test_draconic_sorcerer_5lvl.curr_hp = 7
    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(3)
    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(3)
    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(1)
    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(1)
    test_draconic_sorcerer_5lvl.curr_sorcery_points -= 5
    test_draconic_sorcerer_5lvl.apply_condition(Conditions.PRONE)

    test_stone_giant.ammo[test_stone_giant.rock[1].name] = 0
    test_stone_giant.curr_hp = 46
    test_ogre.curr_hp = 45
    combatant7.curr_hp = 36

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_13(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    test_stone_giant_2 = copy.deepcopy(test_stone_giant)
    battle_map.place_circular_element(np.array([1, 3]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([12, 14]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([3, 12]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([9, 11]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant, test_stone_giant_2]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # DraconicSorcerer5Lvl 1
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # TotemBarbarian5Lvl 1
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.BLUE)  # StoneGiant 1
    teams.add_combatant_to_team(test_stone_giant_2, Teams.Color.RED)  # StoneGiant 2
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 5]))  # DraconicSorcerer5Lvl 1
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([4, 6]))   # TotemBarbarian5Lvl 1
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([1, 10]))   # StoneGiant 1
    battle_map.set_combatant_coordinates(test_stone_giant_2, np.array([8, 8]))   # TotemBarbarian5Lvl 2
    battle_map.build_adjacency_matrix()

    test_draconic_sorcerer_5lvl.curr_hp = 43
    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(3)
    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(3)
    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(1)
    test_draconic_sorcerer_5lvl.curr_sorcery_points = 0

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
        actoid4 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)
        actoid6 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid6, test_draconic_sorcerer_5lvl)
        actoid7 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid7, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_14(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    battle_map.place_circular_element(np.array([4, 11]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([13, 10]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([10, 13]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([10, 2]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_draconic_sorcerer_5lvl, test_stone_giant, test_ogre]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.RED)  # DraconicSorcerer5Lvl 1
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.BLUE)  # StoneGiant 1
    teams.add_combatant_to_team(test_ogre, Teams.Color.BLUE)  # Ogre 1
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 14]))  # DraconicSorcerer5Lvl 1
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([0, 10]))   # StoneGiant 1
    battle_map.set_combatant_coordinates(test_ogre, np.array([1, 13]))   # TotemBarbarian5Lvl 2
    battle_map.build_adjacency_matrix()

    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(3)
    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(1)
    test_draconic_sorcerer_5lvl.curr_sorcery_points = 2

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_15(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_totem_barbarian, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    # TODO Why is this not failing?
    CustomLogger(LogLevel.WARNING)
    battle_map.place_circular_element(np.array([0, 12]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([7, 10]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([10, 12]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([13, 6]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_draconic_sorcerer_5lvl, test_goblin, test_totem_barbarian, test_stone_giant, test_ogre]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.RED)  # DraconicSorcerer5Lvl 1
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # Goblin 1
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)  # TotemBarbarian5Lvl 1
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)  # StoneGiant 1
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)  # Ogre 1
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([7, 8]))  # DraconicSorcerer5Lvl 1
    battle_map.set_combatant_coordinates(test_goblin, np.array([0, 9]))  # Goblin 1
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([8, 7]))  # TotemBarbarian5Lvl 1
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([8, 12]))   # StoneGiant 1
    battle_map.set_combatant_coordinates(test_ogre, np.array([9, 8]))   # Ogre 2
    battle_map.build_adjacency_matrix()

    test_stone_giant.haste_action_factories = [1]  # Simulates that haste factories are not empty
    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(3)
    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(3)
    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(1)
    test_draconic_sorcerer_5lvl.curr_sorcery_points = 0

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
        actoid4 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)
        actoid6 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid6, test_draconic_sorcerer_5lvl)
        actoid7 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid7, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_16(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    battle_map.place_circular_element(np.array([7, 8]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([6, 13]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([8, 8]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([10, 11]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_draconic_sorcerer_5lvl, test_stone_giant, test_ogre]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.RED)  # DraconicSorcerer5Lvl 1
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.BLUE)  # StoneGiant 1
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)  # Ogre 1
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 2]))  # DraconicSorcerer5Lvl 1
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([11, 8]))   # StoneGiant 1
    battle_map.set_combatant_coordinates(test_ogre, np.array([9, 10]))   # Ogre 2
    battle_map.build_adjacency_matrix()

    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(3)
    test_draconic_sorcerer_5lvl.spellslots.use_spellslot(3)
    test_draconic_sorcerer_5lvl.curr_sorcery_points = 0
    test_draconic_sorcerer_5lvl.apply_condition(Conditions.PRONE)

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
        actoid4 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)
        actoid6 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid6, test_draconic_sorcerer_5lvl)
        actoid7 = get_action(test_draconic_sorcerer_5lvl, battle_map)
        action_resolver.resolve_action(actoid7, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_17(battle_map, teams, effect_tracker, test_moon_druid, test_totem_barbarian, test_goblin, test_draconic_sorcerer_5lvl):
    """
    This test case is based on a scenario encountered during fuzzy testing. It makes sure that find_wildshaped_coordinate does its job.
    """
    CustomLogger(LogLevel.WARNING)
    test_totem_barbarian_2 = copy.deepcopy(test_totem_barbarian)
    battle_map.place_circular_element(np.array([6, 14]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([0, 5]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([4, 8]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([10, 1]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_moon_druid, test_totem_barbarian, test_goblin, test_draconic_sorcerer_5lvl, test_totem_barbarian_2]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(test_totem_barbarian_2, Teams.Color.RED)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([4, 13]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([6, 10]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([0, 13]))
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 10]))
    battle_map.set_combatant_coordinates(test_totem_barbarian_2, np.array([3, 11]))

    battle_map.build_adjacency_matrix()

    test_moon_druid.has_haste_action = True

    try:
        actoid1 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid4, test_moon_druid)
        actoid5 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid5, test_moon_druid)
        actoid6 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid6, test_moon_druid)
    except Exception as e:
        assert False, f"Raised an exception {e}"
