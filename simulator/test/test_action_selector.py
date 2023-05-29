import copy
import pstats
import numpy as np
import pytest

from simulator.action_resolver import ActionResolver
from simulator.actions.action_fsms import generate_action_fsm
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.misc import Conditions
from simulator.spells.fireball import Fireball
from simulator.spells.twinned_firebolt import TwinnedFirebolt
from simulator.teams import Teams
from simulator.test.fixtures import combatant1, combatant2, combatant3, test_totem_barbarian, combatant5, combatant6, teams, effect_tracker, battle_map
from simulator.actions.action_selector import get_best_actions, build_action_dag, get_action
from simulator.threat_utils import get_aoe_and_aoo_threat_for_increment
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
    dag = build_action_dag(combatant1, battle_map, fsm, transition_name_to_action, distances, shortest_paths, misty_step_state)
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
        dag = build_action_dag(combatant1, battle_map, fsm, transition_name_to_action, distances, shortest_paths, misty_step_state)
        transitions = dag.get_available_transitions()
        # Tests regular movement + quickened fireball
        assert dag.state == '0'
        assert 'Dodge of Faurung' in transitions
        assert 'Disengage of Faurung' in transitions
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
        assert 'Dodge of Faurung' not in transitions
        assert 'Disengage of Faurung' not in transitions

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
    dag = build_action_dag(combatant1, battle_map, fsm, transition_name_to_action, distances, shortest_paths, misty_step_state)
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
    dag = build_action_dag(combatant1, battle_map, fsm, transition_name_to_action, distances, shortest_paths, misty_step_state)
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
    dag = build_action_dag(combatant1, battle_map, fsm, transition_name_to_action, distances, shortest_paths, misty_step_state)
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
    dag = build_action_dag(combatant1, battle_map, fsm, transition_name_to_action, distances, shortest_paths, misty_step_state)
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
    dag = build_action_dag(combatant1, battle_map, fsm, transition_name_to_action, distances, shortest_paths, misty_step_state)
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
    # for ba in best_actions:
    #     new_coord += ba.increment if isinstance(ba, MovementIncrement) else np.array([[0, 0]])
    # assert battle_map.get_hop_distance(new_coord, combatant3) > (combatant3.speed + combatant3.danger_zone_attack[1].range)
    # Staying still is actually preferable here
    assert isinstance(best_actions[0], Fireball) or isinstance(best_actions[0], TwinnedFirebolt)
    assert isinstance(best_actions[1], Fireball) or isinstance(best_actions[1], TwinnedFirebolt)


def test_rage_before_attack(battle_map, teams, effect_tracker, combatant3, test_totem_barbarian):
    """
    We assert that the barbarian rages before doing anything else.
    """
    CustomLogger(LogLevel.WARNING)

    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant3, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(combatant3, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([13, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant3, test_totem_barbarian]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)

    try:
        actoid1 = get_action(test_totem_barbarian, battle_map)
        assert str(actoid1) == 'TotemRage of TotemBarbarian5Lvl'
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
        assert str(actoid10) == 'RecklessAttack at Bugbear'
        action_resolver.resolve_action(actoid10, test_totem_barbarian)
        actoid11 = get_action(test_totem_barbarian, battle_map)
        assert str(actoid11) == 'RecklessAttack at Bugbear'
        action_resolver.resolve_action(actoid11, test_totem_barbarian)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_bugbear_going_into_melee(battle_map, teams, effect_tracker, combatant3, test_totem_barbarian):
    """
    It had occured during testing that the bugbear would opt for staying at range and throw javelins rather than go in melee range
    which is not desirable.
    """
    CustomLogger(LogLevel.WARNING)

    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant3, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(combatant3, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([11, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant3, test_totem_barbarian]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)

    try:
        actoid1 = get_action(combatant3, battle_map)
        action_resolver.resolve_action(actoid1, combatant3)
        actoid2 = get_action(combatant3, battle_map)
        action_resolver.resolve_action(actoid2, combatant3)
        actoid3 = get_action(combatant3, battle_map)
        action_resolver.resolve_action(actoid3, combatant3)
        actoid4 = get_action(combatant3, battle_map)
        action_resolver.resolve_action(actoid4, combatant3)
        actoid5 = get_action(combatant3, battle_map)
        action_resolver.resolve_action(actoid5, combatant3)
        actoid6 = get_action(combatant3, battle_map)
        action_resolver.resolve_action(actoid6, combatant3)
        actoid7 = get_action(combatant3, battle_map)
        assert str(actoid7) == "Morningstar on TotemBarbarian5Lvl"
    except Exception as e:
        assert False, f"Raised an exception {e}"

def test_goblin_using_cunning_disengage(battle_map, teams, effect_tracker, combatant2, combatant3):
    """
    We assert that the goblin first uses his cunning disengage to first get away and then shoots his bow.
    """
    CustomLogger(LogLevel.WARNING)
    combatant4 = copy.deepcopy(combatant3)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant2, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(combatant4, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(combatant2, np.array([6, 4]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(combatant3, np.array([7, 4]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(combatant4, np.array([8, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant2, combatant3, combatant4]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)

    try:
        actoid1 = get_action(combatant2, battle_map)
        assert str(actoid1) == "Cunning Disengage of Goblin"
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
        actoid7 = get_action(combatant2, battle_map)
        action_resolver.resolve_action(actoid7, combatant2)
        actoid8 = get_action(combatant2, battle_map)
        assert str(actoid8) == "Shortbow on Bugbear"
    except Exception as e:
        assert False, f"Raised an exception {e}"
