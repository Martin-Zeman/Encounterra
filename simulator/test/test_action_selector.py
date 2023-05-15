import copy
import pstats
from functools import reduce

import numpy as np
import pytest

from simulator.action_resolver import ActionResolver
from simulator.actions.action_fsms import generate_action_fsm
from simulator.actions.movement import MovementGenerator, MovementIncrement
from simulator.battle_map import Terrain
from simulator.combatant_coords import CombatantCoords
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.misc import Conditions
from simulator.spells.fireball import Fireball
from simulator.spells.firebolt import Firebolt
from simulator.spells.spell import SpellStats
from simulator.spells.twinned_firebolt import TwinnedFirebolt
from simulator.teams import Teams
from simulator.test.fixtures import combatant1, combatant2, combatant3,combatant4, combatant5, combatant6, teams, effect_tracker, battle_map
from simulator.actions.action_selector import get_best_actions, build_action_dag
from simulator.threat import get_aoe_and_aoo_threat_for_increment
import types
import cProfile


def test_build_action_dag_misty_step_and_firebolt(battle_map, teams, effect_tracker, combatant1, combatant2, combatant3):
    CustomLogger(LogLevel.WARNING)
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(combatant1, np.array([1, 3]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(combatant2, np.array([10, 10]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(combatant3, np.array([3, 4]))  # Have to set it for fireball placement

    # fsm, transition_mapping, _ = generate_action_fsm(combatant1, battle_map)
    # assert fsm.state == '0'
    # fsm.get_graph().draw('state_diagram_faurung_pre_coords.png', prog='dot')
    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(combatant1)
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    fsm, transition_name_to_action, misty_step_state = generate_action_fsm(combatant1, battle_map)
    dag = build_action_dag(combatant1, battle_map, fsm, transition_name_to_action, shortest_paths, misty_step_state)
    # dfs.get_graph().draw('state_diagram_faurung_with_coords',format='svg', prog='dot')

    # Tests the Misty Step movement + Firebolt
    assert dag.state == '0'
    transitions = dag.get_available_transitions()
    assert "Dodge of Faurung" in transitions
    assert "Disengage of Faurung" in transitions
    assert "ms_(7, 3)" in transitions
    assert "ms_(2, 3)" in transitions
    assert "m_(7, 3)" in transitions
    dag.trigger("ms_(2, 3)")
    transitions = dag.get_available_transitions()
    assert "Staff of Defence on Goblin" not in transitions  # Test that Misty Step actions are also prepended with movement
    assert "Firebolt on Goblin" in transitions
    assert "Dodge of Faurung" not in transitions # Even though it's possible, we don't support dodge after Misty Step, as it's very niche
    assert "Disengage of Faurung" not in transitions # Even though it's possible, we don't support dodge after Misty Step, as it's very niche
    dag.trigger("Firebolt on Goblin")
    assert len(dag.get_available_transitions()) == 0

def test_build_action_dag_movement_and_quickened_fireball(battle_map, teams, effect_tracker, combatant1, combatant2, combatant3):
        battle_map.build_adjacency_matrix()
        battle_map.set_effect_tracker(effect_tracker)
        effect_tracker.set_battle_map(battle_map)
        teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
        teams.add_combatant_to_team(combatant2, Teams.Color.RED)
        # teams.add_combatant_to_team(combatant3, Teams.Color.RED)
        battle_map.set_combatant_coordinates(combatant1, np.array([1, 3]))
        battle_map.set_combatant_coordinates(combatant2, np.array([10, 10]))
        # battle_map.set_combatant_coordinates(combatant3, np.array([2, 3]))

        # Pre-calculate Dijkstra for the combatant
        distances, shortest_paths = battle_map.calc_dijkstra(combatant1)
        get_aoe_and_aoo_threat_for_increment.cache_clear()
        fsm, transition_name_to_action, misty_step_state = generate_action_fsm(combatant1, battle_map)
        dag = build_action_dag(combatant1, battle_map, fsm, transition_name_to_action, shortest_paths, misty_step_state)
        # Tests regular movement + quickened fireball
        assert dag.state == '0'
        dag.trigger("m_(2, 3)")
        transitions = dag.get_available_transitions()
        # Check that we have all the action (except for the Staff attack) available
        assert 'Quickened Fireball at [ 6 10]' in transitions
        assert 'Quickened Firebolt on Goblin' in transitions
        assert 'Quickened Haste on Faurung' in transitions
        assert 'Fireball at [ 6 10]' in transitions
        assert 'Firebolt on Goblin' in transitions
        assert 'Haste on Faurung' in transitions
        assert 'Dodge of Faurung' not in transitions  # Once you do a regular move, Dodge should not be available
        assert 'Disengage of Faurung' not in transitions  # Once you do a regular move, Disengage should not be available
        dag.trigger("Quickened Fireball at [ 6 10]")
        transitions = dag.get_available_transitions()
        # For the second action, coordinates are not taken into account, but Dodge is included
        assert 'Staff of Defence on Goblin' in transitions
        assert 'Firebolt on Goblin' in transitions
        assert 'Dodge of Faurung' in transitions
        assert 'Disengage of Faurung' in transitions

def test_build_action_dag_movement_and_fireball(battle_map, teams, effect_tracker, combatant1, combatant2, combatant3):
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    # teams.add_combatant_to_team(combatant3, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, np.array([1, 3]))
    battle_map.set_combatant_coordinates(combatant2, np.array([10, 10]))
    # battle_map.set_combatant_coordinates(combatant3, np.array([2, 3]))  # Have to set it for fireball placement

    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(combatant1)
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    fsm, transition_name_to_action, misty_step_state = generate_action_fsm(combatant1, battle_map)
    dag = build_action_dag(combatant1, battle_map, fsm, transition_name_to_action, shortest_paths, misty_step_state)
    # Tests regular movement + fireball
    assert dag.state == '0'
    dag.trigger("m_(2, 3)")
    transitions = dag.get_available_transitions()
    # Check that we have all the action (except for the Staff attack) available
    assert 'Quickened Fireball at [ 6 10]' in transitions
    assert 'Quickened Firebolt on Goblin' in transitions
    assert 'Quickened Haste on Faurung' in transitions
    assert 'Fireball at [ 6 10]' in transitions
    assert 'Firebolt on Goblin' in transitions
    assert 'Haste on Faurung' in transitions
    assert 'Dodge of Faurung' not in transitions  # Once you do a regular move, Dodge should not be available
    assert 'Disengage of Faurung' not in transitions  # Once you do a regular move, Disengage should not be available
    dag.trigger("Fireball at [ 6 10]")
    transitions = dag.get_available_transitions()
    # For the second action, coordinates are not taken into account
    assert 'Quickened Firebolt on Goblin' in transitions

def test_build_action_dag_movement_and_staff_attack(battle_map, teams, effect_tracker, combatant1, combatant2, combatant3):
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    # teams.add_combatant_to_team(combatant3, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, np.array([1, 3]))
    battle_map.set_combatant_coordinates(combatant2, np.array([10, 10]))
    # battle_map.set_combatant_coordinates(combatant3, np.array([2, 3]))

    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(combatant1)
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    fsm, transition_name_to_action, misty_step_state = generate_action_fsm(combatant1, battle_map)
    dag = build_action_dag(combatant1, battle_map, fsm, transition_name_to_action, shortest_paths, misty_step_state)
    # Tests regular movement + staff of defence attack
    assert dag.state == '0'
    dag.trigger("m_(9, 10)")
    transitions = dag.get_available_transitions()
    # Check that we have all the action (except for the Staff attack) available
    assert 'Quickened Fireball at [ 6 10]' in transitions
    assert 'Quickened Firebolt on Goblin' in transitions
    assert 'Quickened Haste on Faurung' in transitions
    assert 'Fireball at [ 6 10]' in transitions
    assert 'Firebolt on Goblin' in transitions
    assert 'Haste on Faurung' in transitions
    assert 'Staff of Defence on Goblin' in transitions
    assert 'Dodge of Faurung' not in transitions  # Once you do a regular move, Dodge should not be available
    assert 'Disengage of Faurung' not in transitions  # Once you do a regular move, Disengage should not be available
    dag.trigger("Staff of Defence on Goblin")
    transitions = dag.get_available_transitions()
    # For the second action, coordinates are not taken into account, but Dodge is included
    assert 'Quickened Fireball at [ 6 10]' in transitions
    assert 'Quickened Firebolt on Goblin' in transitions
    assert 'Quickened Haste on Faurung' in transitions

def test_build_action_dag_misty_step_and_staff_attack(battle_map, teams, effect_tracker, combatant1, combatant2,
                                                      combatant3):
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    # teams.add_combatant_to_team(combatant3, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, np.array([1, 3]))
    battle_map.set_combatant_coordinates(combatant2, np.array([10, 10]))
    # battle_map.set_combatant_coordinates(combatant3, np.array([2, 3]))

    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(combatant1)
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    fsm, transition_name_to_action, misty_step_state = generate_action_fsm(combatant1, battle_map)
    dag = build_action_dag(combatant1, battle_map, fsm, transition_name_to_action, shortest_paths, misty_step_state)
    # Tests Misty Step movement + staff of defence attack
    assert dag.state == '0'
    dag.trigger("ms_(9, 10)")
    transitions = dag.get_available_transitions()
    # Check that we have all the action (except for the Staff attack) available
    assert "Staff of Defence on Goblin" in transitions  # Test that Misty Step actions are also prepended with movement
    assert "Firebolt on Goblin" in transitions
    dag.trigger("Staff of Defence on Goblin")
    assert len(dag.get_available_transitions()) == 0

def test_build_action_dag_dodge_and_movement_and_quickened_spell(battle_map, teams, effect_tracker, combatant1, combatant2, combatant3):
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    # teams.add_combatant_to_team(combatant3, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, np.array([1, 3]))
    battle_map.set_combatant_coordinates(combatant2, np.array([10, 10]))
    # battle_map.set_combatant_coordinates(combatant3, np.array([2, 3]))

    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(combatant1)
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    fsm, transition_name_to_action, misty_step_state = generate_action_fsm(combatant1, battle_map)
    dag = build_action_dag(combatant1, battle_map, fsm, transition_name_to_action, shortest_paths, misty_step_state)
    # Tests Dodge + movement + a quickened spell
    assert dag.state == '0'
    dag.trigger("Dodge of Faurung")
    assert dag.state == 'Dodged'
    transitions = dag.get_available_transitions()
    assert "do_(7, 3)" in transitions
    assert "ms_(2, 3)" not in transitions  # Even though it's possible, we don't support Misty Step after Dodge, as it's very niche
    dag.trigger("do_(7, 3)")
    assert dag.state == "do_(7, 3)"
    transitions = dag.get_available_transitions()
    assert 'Quickened Fireball at [ 6 10]' in transitions
    assert 'Quickened Firebolt on Goblin' in transitions
    assert 'Quickened Haste on Faurung' in transitions
    dag.trigger("Quickened Haste on Faurung")
    assert len(dag.get_available_transitions()) == 0

def test_build_action_dag_disengage_and_movement_and_quickened_spell(battle_map, teams, effect_tracker, combatant1, combatant2, combatant3):
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)
    # teams.add_combatant_to_team(combatant3, Teams.Color.RED)
    battle_map.set_combatant_coordinates(combatant1, np.array([1, 3]))
    battle_map.set_combatant_coordinates(combatant2, np.array([10, 10]))
    # battle_map.set_combatant_coordinates(combatant3, np.array([2, 3]))

    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(combatant1)
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    fsm, transition_name_to_action, misty_step_state = generate_action_fsm(combatant1, battle_map)
    dag = build_action_dag(combatant1, battle_map, fsm, transition_name_to_action, shortest_paths, misty_step_state)
    # Tests Disengage + movement + a quickened spell
    assert dag.state == '0'
    dag.trigger("Disengage of Faurung")
    assert dag.state == 'Disengaged'
    transitions = dag.get_available_transitions()
    assert "di_(5, 3)" in transitions
    assert "ms_(2, 3)" not in transitions  # Even though it's possible, we don't support Misty Step after Dodge, as it doesn't make muche sense
    dag.trigger("di_(5, 3)")
    assert dag.state == "di_(5, 3)"
    transitions = dag.get_available_transitions()
    assert 'Quickened Fireball at [ 6 10]' in transitions
    assert 'Quickened Firebolt on Goblin' in transitions
    assert 'Quickened Haste on Faurung' in transitions
    dag.trigger("Quickened Firebolt on Goblin")
    assert len(dag.get_available_transitions()) == 0


def test_get_best_actions_twin_firebolt_and_fireball(battle_map, teams, effect_tracker, combatant1, combatant2, combatant3):
    CustomLogger(LogLevel.WARNING)
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(combatant1, np.array([1, 3]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(combatant2, np.array([10, 10]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(combatant3, np.array([2, 4]))  # Have to set it for fireball placement

    distances, shortest_paths = battle_map.calc_dijkstra(combatant1)
    # from simulator.actions.action_selector import get_best_actions
    # cProfile.runctx('get_best_actions(combatant1, battle_map, distances, shortest_paths)', None, locals(), filename="get_best_actions_stats")
    # p = pstats.Stats("select_best_action_stats")
    # p.strip_dirs().sort_stats("cumtime").print_stats()
    best_actions = get_best_actions(combatant1, battle_map, distances, shortest_paths)
    new_coord = copy.copy(battle_map.get_combatant_position(combatant1).get())
    for ba in best_actions:
        new_coord += ba.increment if isinstance(ba, MovementIncrement) else np.array([[0, 0]])
    assert battle_map.get_hop_distance(new_coord, combatant3) > (combatant3.speed + combatant3.danger_zone_attack[1].range)
    assert isinstance(best_actions[-2], Fireball) or isinstance(best_actions[-2], TwinnedFirebolt)
    assert isinstance(best_actions[-1], Fireball) or isinstance(best_actions[-1], TwinnedFirebolt)


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
    fireball = best_actions[-2] if isinstance(best_actions[-2], Fireball) else best_actions[-1]
    assert battle_map.get_cartesian_distance(new_coord, np.array([fireball.coord])) > SpellStats.TRANSLATE_RADIUS[fireball.factory.target]
    assert battle_map.get_hop_distance(new_coord, combatant3) > (combatant3.speed + combatant3.danger_zone_attack[1].range)
    assert isinstance(best_actions[-2], Fireball) or isinstance(best_actions[-2], Firebolt)
    assert isinstance(best_actions[-1], Fireball) or isinstance(best_actions[-1], Firebolt)

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
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(combatant4, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(combatant1, np.array([0, 8]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(combatant3, np.array([1, 9]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(combatant4, np.array([2, 9]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()

    distances, shortest_paths = battle_map.calc_dijkstra(combatant1)
    best_actions = get_best_actions(combatant1, battle_map, distances, shortest_paths)
    new_coord = copy.copy(battle_map.get_combatant_position(combatant1).get())
    for ba in best_actions:
        new_coord += ba.increment if isinstance(ba, MovementIncrement) else np.array([[0, 0]])
    fireball = best_actions[-2] if isinstance(best_actions[-2], Fireball) else best_actions[-1]
    assert battle_map.get_cartesian_distance(new_coord, np.array([fireball.coord])) > SpellStats.TRANSLATE_RADIUS[fireball.factory.target]
    assert battle_map.get_cartesian_distance(combatant3, np.array([fireball.coord])) <= SpellStats.TRANSLATE_RADIUS[fireball.factory.target]
    assert battle_map.get_cartesian_distance(combatant4, np.array([fireball.coord])) <= SpellStats.TRANSLATE_RADIUS[fireball.factory.target]
    assert battle_map.get_hop_distance(new_coord, combatant3) > (combatant3.speed + combatant3.danger_zone_attack[1].range)
    assert battle_map.get_hop_distance(new_coord, combatant4) > (combatant4.speed + combatant4.danger_zone_attack[1].range)
    assert isinstance(best_actions[-2], Fireball) or isinstance(best_actions[-2], TwinnedFirebolt)
    assert isinstance(best_actions[-1], Fireball) or isinstance(best_actions[-1], TwinnedFirebolt)


def test_error_case_3(battle_map, teams, effect_tracker, combatant1, combatant3, combatant4, combatant5, combatant6):
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
    combatants = [combatant1, combatant3, combatant4, combatant5, combatant6, combatant7]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.RED)  # Faurung
    teams.add_combatant_to_team(combatant3, Teams.Color.BLUE)  # Bugbear 1
    teams.add_combatant_to_team(combatant4, Teams.Color.RED)  # TotemBarbarian5Lvl
    teams.add_combatant_to_team(combatant5, Teams.Color.RED)  # StoneGiant
    teams.add_combatant_to_team(combatant6, Teams.Color.BLUE)  # Ogre
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # Bugbear 2
    battle_map.set_combatant_coordinates(combatant1, np.array([14, 13]))
    battle_map.set_combatant_coordinates(combatant3, np.array([3, 11]))
    battle_map.set_combatant_coordinates(combatant4, np.array([3, 12]))
    battle_map.set_combatant_coordinates(combatant5, np.array([0, 11]))
    battle_map.set_combatant_coordinates(combatant6, np.array([3, 9]))
    battle_map.set_combatant_coordinates(combatant7, np.array([9, 12]))
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
        actoid2 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid2, combatant1)
        actoid3 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid3, combatant1)
        actoid4 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid4, combatant1)
        actoid5 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid5, combatant1)
        actoid6 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid6, combatant1)
        actoid7 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid7, combatant1)
        actoid8 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid8, combatant1)
        actoid9 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid9, combatant1)
    except Exception as e:
        assert False, f"Raised an exception {e}"

def test_error_case_4(battle_map, teams, effect_tracker, combatant1, combatant4, combatant5):
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
    combatants = [combatant1, combatant4, combatant5, combatant6]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # Faurung 1
    teams.add_combatant_to_team(combatant4, Teams.Color.RED)  # TotemBarbarian5Lvl
    teams.add_combatant_to_team(combatant5, Teams.Color.RED)  # StoneGiant
    teams.add_combatant_to_team(combatant6, Teams.Color.RED)  # Faurung 2
    battle_map.set_combatant_coordinates(combatant1, np.array([9, 13]))
    battle_map.set_combatant_coordinates(combatant4, np.array([10, 9]))
    battle_map.set_combatant_coordinates(combatant5, np.array([4, 8]))
    battle_map.set_combatant_coordinates(combatant6, np.array([7, 8]))
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
        actoid2 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid2, combatant1)
        actoid3 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid3, combatant1)
        actoid4 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid4, combatant1)
        actoid5 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid5, combatant1)
        actoid6 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid6, combatant1)
        actoid7 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid7, combatant1)
        actoid8 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid8, combatant1)
        assert battle_map.get_cartesian_distance(battle_map.get_combatant_position(combatant1).get(), np.array([actoid8.coord])) > SpellStats.TRANSLATE_RADIUS[actoid8.factory.target]
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_5(battle_map, teams, effect_tracker, combatant1, combatant2, combatant4, combatant5, combatant6):
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
    combatants = [combatant1, combatant2, combatant4, combatant5, combatant6, combatant7]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # Faurung 1
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # Goblin
    teams.add_combatant_to_team(combatant4, Teams.Color.BLUE)  # TotemBarbarian5Lvl
    teams.add_combatant_to_team(combatant5, Teams.Color.RED)  # StoneGiant
    teams.add_combatant_to_team(combatant6, Teams.Color.RED)  # Ogre
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # Faurung 2
    battle_map.set_combatant_coordinates(combatant1, np.array([14, 14]))  # Faurung 1
    battle_map.set_combatant_coordinates(combatant2, np.array([9, 14]))  # Goblin
    battle_map.set_combatant_coordinates(combatant4, np.array([10, 13]))  # TotemBarbarian5Lvl
    battle_map.set_combatant_coordinates(combatant5, np.array([0, 8]))  # StoneGiant
    battle_map.set_combatant_coordinates(combatant6, np.array([10, 10]))   # Ogre
    battle_map.set_combatant_coordinates(combatant7, np.array([7, 8]))  # Faurung 2
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
        actoid2 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid2, combatant1)
        actoid3 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid3, combatant1)
        actoid4 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid4, combatant1)
        actoid5 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid5, combatant1)
        actoid6 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid6, combatant1)
        actoid7 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid7, combatant1)
        actoid8 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid8, combatant1)
    except Exception as e:
        assert False, f"Raised an exception {e}"

def test_error_case_6(battle_map, teams, effect_tracker, combatant1, combatant3, combatant4, combatant6):
    """
    This test case is based on a scenario encountered during fuzzy testing. The purpose of this test is to make sure we don't enter
    into an endless recursion via the Barbarian's Reckless Attack.
    """
    CustomLogger(LogLevel.WARNING)
    combatant7 = copy.deepcopy(combatant4)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant3, combatant4, combatant6, combatant7]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # Faurung
    teams.add_combatant_to_team(combatant3, Teams.Color.BLUE)  # Bugbear
    teams.add_combatant_to_team(combatant4, Teams.Color.BLUE)  # TotemBarbarian5Lvl 1
    teams.add_combatant_to_team(combatant6, Teams.Color.BLUE)  # Ogre
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # TotemBarbarian5Lvl 2
    battle_map.set_combatant_coordinates(combatant1, np.array([5, 5]))  # Bugbear
    battle_map.set_combatant_coordinates(combatant3, np.array([14, 14]))  # Bugbear
    battle_map.set_combatant_coordinates(combatant4, np.array([9, 14]))  # TotemBarbarian5Lvl 1
    battle_map.set_combatant_coordinates(combatant6, np.array([10, 13]))  # Ogre
    battle_map.set_combatant_coordinates(combatant7, np.array([0, 8]))  # TotemBarbarian5Lvl 2
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = combatant4.get_action(battle_map)
        action_resolver.resolve_action(actoid1, combatant4)
        actoid2 = combatant4.get_action(battle_map)
        action_resolver.resolve_action(actoid2, combatant4)
        actoid3 = combatant4.get_action(battle_map)
        action_resolver.resolve_action(actoid3, combatant4)
        actoid4 = combatant4.get_action(battle_map)
        action_resolver.resolve_action(actoid4, combatant4)
        actoid5 = combatant4.get_action(battle_map)
        action_resolver.resolve_action(actoid5, combatant4)
        actoid6 = combatant4.get_action(battle_map)
        action_resolver.resolve_action(actoid6, combatant4)
        actoid7 = combatant4.get_action(battle_map)
        action_resolver.resolve_action(actoid7, combatant4)
        actoid8 = combatant4.get_action(battle_map)
        action_resolver.resolve_action(actoid8, combatant4)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_7(battle_map, teams, effect_tracker, combatant1, combatant2, combatant4):
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
    combatants = [combatant1, combatant4, combatant5, combatant6]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # Faurung 1
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # Goblin
    teams.add_combatant_to_team(combatant4, Teams.Color.RED)  # TotemBarbarian5Lvl
    battle_map.set_combatant_coordinates(combatant1, np.array([9, 13]))
    battle_map.set_combatant_coordinates(combatant2, np.array([10, 9]))
    battle_map.set_combatant_coordinates(combatant4, np.array([4, 8]))
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = combatant2.get_action(battle_map)
        action_resolver.resolve_action(actoid1, combatant2)
        actoid2 = combatant2.get_action(battle_map)
        action_resolver.resolve_action(actoid2, combatant2)
        actoid3 = combatant2.get_action(battle_map)
        action_resolver.resolve_action(actoid3, combatant2)
        actoid4 = combatant2.get_action(battle_map)
        action_resolver.resolve_action(actoid4, combatant2)
        actoid5 = combatant2.get_action(battle_map)
        action_resolver.resolve_action(actoid5, combatant2)
        actoid6 = combatant2.get_action(battle_map)
        action_resolver.resolve_action(actoid6, combatant2)

        actoid1 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
        actoid2 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid2, combatant1)
        actoid3 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid3, combatant1)
        actoid4 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid4, combatant1)
        actoid5 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid5, combatant1)
        actoid6 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid6, combatant1)
        actoid7 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid7, combatant1)
        actoid8 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid8, combatant1)

        actoid1 = combatant4.get_action(battle_map)
        action_resolver.resolve_action(actoid1, combatant4)
        actoid2 = combatant4.get_action(battle_map)
        action_resolver.resolve_action(actoid2, combatant4)
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
        actoid1 = combatant7.get_action(battle_map)
        action_resolver.resolve_action(actoid1, combatant7)
        actoid2 = combatant7.get_action(battle_map)
        action_resolver.resolve_action(actoid2, combatant7)
        actoid3 = combatant7.get_action(battle_map)
        action_resolver.resolve_action(actoid3, combatant7)
        actoid4 = combatant7.get_action(battle_map)
        action_resolver.resolve_action(actoid4, combatant7)
        actoid5 = combatant7.get_action(battle_map)
        action_resolver.resolve_action(actoid5, combatant7)
        actoid6 = combatant7.get_action(battle_map)
        action_resolver.resolve_action(actoid6, combatant7)
        actoid7 = combatant7.get_action(battle_map)
        action_resolver.resolve_action(actoid7, combatant7)
        actoid8 = combatant7.get_action(battle_map)
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
        actoid1 = combatant5.get_action(battle_map)
        action_resolver.resolve_action(actoid1, combatant5)
        actoid2 = combatant5.get_action(battle_map)
        action_resolver.resolve_action(actoid2, combatant5)

        actoid3 = combatant7.get_action(battle_map)
        action_resolver.resolve_action(actoid3, combatant7)

        actoid4 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid4, combatant1)
        actoid5 = combatant1.get_action(battle_map)
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
        actoid1 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
        actoid2 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid2, combatant1)
        actoid3 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid3, combatant1)
        actoid4 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid4, combatant1)
        actoid5 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid5, combatant1)
        actoid6 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid6, combatant1)
        actoid7 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid7, combatant1)
        actoid8 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid8, combatant1)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_11(battle_map, teams, effect_tracker, combatant1, combatant4, combatant5, combatant6):
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
    combatants = [combatant1, combatant4, combatant5, combatant6, combatant7, combatant8]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # Faurung 1
    teams.add_combatant_to_team(combatant4, Teams.Color.RED)  # TotemBarbarian5Lvl 1
    teams.add_combatant_to_team(combatant5, Teams.Color.BLUE)  # StoneGiant 1
    teams.add_combatant_to_team(combatant6, Teams.Color.BLUE)  # Ogre 1
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # Faurung 2
    teams.add_combatant_to_team(combatant8, Teams.Color.RED)  # StoneGiant 2
    battle_map.set_combatant_coordinates(combatant1, np.array([7, 8]))  # Faurung 1
    battle_map.set_combatant_coordinates(combatant4, np.array([6, 12]))   # TotemBarbarian5Lvl 1
    battle_map.set_combatant_coordinates(combatant5, np.array([9, 9]))   # StoneGiant 1
    battle_map.set_combatant_coordinates(combatant6, np.array([6, 10]))   # Ogre 1
    battle_map.set_combatant_coordinates(combatant7, np.array([9, 12]))   # Faurung 2
    battle_map.set_combatant_coordinates(combatant8, np.array([3, 10]))   # StoneGiant 2
    battle_map.build_adjacency_matrix()

    combatant4.curr_rage_uses -= 1
    combatant6.curr_hp -= 32
    combatant7.curr_hp -= 4
    combatant7.spellslots.use_spellslot(3)
    combatant7.curr_sorcery_points -= 5

    try:
        actoid1 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_12(battle_map, teams, effect_tracker, combatant1, combatant4, combatant5, combatant6):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(LogLevel.WARNING)
    combatant7 = copy.deepcopy(combatant4)
    battle_map.place_circular_element(np.array([0, 7]), Terrain.IMPASSABLE_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([7, 14]), Terrain.IMPASSABLE_TERRAIN, diameter=1)
    battle_map.place_circular_element(np.array([1, 10]), Terrain.DIFFICULT_TERRAIN, diameter=2)
    battle_map.place_circular_element(np.array([6, 7]), Terrain.DIFFICULT_TERRAIN, diameter=1)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant1, combatant4, combatant5, combatant6, combatant7]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # Faurung 1
    teams.add_combatant_to_team(combatant4, Teams.Color.BLUE)  # TotemBarbarian5Lvl 1
    teams.add_combatant_to_team(combatant5, Teams.Color.RED)  # StoneGiant 1
    teams.add_combatant_to_team(combatant6, Teams.Color.BLUE)  # Ogre 1
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)  # TotemBarbarian5Lvl 2
    battle_map.set_combatant_coordinates(combatant1, np.array([7, 13]))  # Faurung 1
    battle_map.set_combatant_coordinates(combatant4, np.array([6, 11]))   # TotemBarbarian5Lvl 1
    battle_map.set_combatant_coordinates(combatant5, np.array([7, 10]))   # StoneGiant 1
    battle_map.set_combatant_coordinates(combatant6, np.array([10, 9]))   # Ogre 1
    battle_map.set_combatant_coordinates(combatant7, np.array([6, 12]))   # TotemBarbarian5Lvl 2
    battle_map.build_adjacency_matrix()

    combatant4.curr_hp = 61

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
        actoid1 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid1, combatant1)
        actoid2 = combatant1.get_action(battle_map)
        action_resolver.resolve_action(actoid2, combatant1)
    except Exception as e:
        assert False, f"Raised an exception {e}"
