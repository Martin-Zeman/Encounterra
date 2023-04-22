import numpy as np
import pytest

from simulator.actions.action_fsms import generate_action_fsm
from simulator.combatant_coords import CombatantCoords
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.teams import Teams
from simulator.test.fixtures import combatant1, combatant2, combatant3, teams, effect_tracker, battle_map
from simulator.actions.action_selector import select_best_action


def test_select_best_action_misty_step_and_firebolt(battle_map, teams, effect_tracker, combatant1, combatant2, combatant3):
    CustomLogger(LogLevel.WARNING)
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    # teams.add_combatant_to_team(combatant3, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(combatant1, np.array([1, 3]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(combatant2, np.array([10, 10]))  # Have to set it for fireball placement
    # battle_map.set_combatant_coordinates(combatant3, np.array([2, 3]))  # Have to set it for fireball placement

    # fsm, transition_mapping, _ = generate_action_fsm(combatant1, battle_map)
    # assert fsm.state == '0'
    # fsm.get_graph().draw('state_diagram_faurung_pre_coords.png', prog='dot')
    dfs = select_best_action(combatant1, battle_map)
    # dfs.get_graph().draw('state_diagram_faurung_with_coords',format='svg', prog='dot')

    # Tests the Misty Step movement + Firebolt
    assert dfs.state == '0'
    transitions = dfs.get_available_transitions()
    assert "Dodge of Faurung" in transitions
    assert "Disengage of Faurung" in transitions
    assert "ms_(7, 3)" in transitions
    assert "ms_(2, 3)" in transitions
    assert "m_(7, 3)" in transitions
    dfs.trigger("ms_(2, 3)")
    transitions = dfs.get_available_transitions()
    assert "Staff of Defence on Goblin" not in transitions  # Test that Misty Step actions are also prepended with movement
    assert "Firebolt on Goblin" in transitions
    assert "Dodge of Faurung" not in transitions # Even though it's possible, we don't support dodge after Misty Step, as it's very niche
    assert "Disengage of Faurung" not in transitions # Even though it's possible, we don't support dodge after Misty Step, as it's very niche
    dfs.trigger("Firebolt on Goblin")
    assert len(dfs.get_available_transitions()) == 0
#
# def test_select_best_action_movement_and_quickened_fireball(battle_map, teams, effect_tracker, combatant1, combatant2, combatant3):
#         battle_map.build_adjacency_matrix()
#         battle_map.set_effect_tracker(effect_tracker)
#         effect_tracker.set_battle_map(battle_map)
#         teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
#         teams.add_combatant_to_team(combatant2, Teams.Color.RED)
#         # teams.add_combatant_to_team(combatant3, Teams.Color.RED)
#         battle_map.set_combatant_coordinates(combatant1, np.array([1, 3]))
#         battle_map.set_combatant_coordinates(combatant2, np.array([10, 10]))
#         # battle_map.set_combatant_coordinates(combatant3, np.array([2, 3]))
#
#         dfs = select_best_action(combatant1, battle_map)
#         # Tests regular movement + quickened fireball
#         assert dfs.state == '0'
#         dfs.trigger("m_(2, 3)")
#         transitions = dfs.get_available_transitions()
#         # Check that we have all the action (except for the Staff attack) available
#         assert 'Quickened Fireball at [ 6 10]' in transitions
#         assert 'Quickened Firebolt on Goblin' in transitions
#         assert 'Quickened Haste on Faurung' in transitions
#         assert 'Fireball at [ 6 10]' in transitions
#         assert 'Firebolt on Goblin' in transitions
#         assert 'Haste on Faurung' in transitions
#         assert 'Dodge of Faurung' not in transitions  # Once you do a regular move, Dodge should not be available
#         assert 'Disengage of Faurung' not in transitions  # Once you do a regular move, Disengage should not be available
#         dfs.trigger("Quickened Fireball at [ 6 10]")
#         transitions = dfs.get_available_transitions()
#         # For the second action, coordinates are not taken into account, but Dodge is included
#         assert 'Staff of Defence on Goblin' in transitions
#         assert 'Firebolt on Goblin' in transitions
#         assert 'Dodge of Faurung' in transitions
#         assert 'Disengage of Faurung' in transitions
#
# def test_select_best_action_movement_and_fireball(battle_map, teams, effect_tracker, combatant1, combatant2, combatant3):
#     battle_map.build_adjacency_matrix()
#     battle_map.set_effect_tracker(effect_tracker)
#     effect_tracker.set_battle_map(battle_map)
#     teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
#     teams.add_combatant_to_team(combatant2, Teams.Color.RED)
#     # teams.add_combatant_to_team(combatant3, Teams.Color.RED)
#     battle_map.set_combatant_coordinates(combatant1, np.array([1, 3]))
#     battle_map.set_combatant_coordinates(combatant2, np.array([10, 10]))
#     # battle_map.set_combatant_coordinates(combatant3, np.array([2, 3]))  # Have to set it for fireball placement
#
#     dfs = select_best_action(combatant1, battle_map)
#     # Tests regular movement + fireball
#     assert dfs.state == '0'
#     dfs.trigger("m_(2, 3)")
#     transitions = dfs.get_available_transitions()
#     # Check that we have all the action (except for the Staff attack) available
#     assert 'Quickened Fireball at [ 6 10]' in transitions
#     assert 'Quickened Firebolt on Goblin' in transitions
#     assert 'Quickened Haste on Faurung' in transitions
#     assert 'Fireball at [ 6 10]' in transitions
#     assert 'Firebolt on Goblin' in transitions
#     assert 'Haste on Faurung' in transitions
#     assert 'Dodge of Faurung' not in transitions  # Once you do a regular move, Dodge should not be available
#     assert 'Disengage of Faurung' not in transitions  # Once you do a regular move, Disengage should not be available
#     dfs.trigger("Fireball at [ 6 10]")
#     transitions = dfs.get_available_transitions()
#     # For the second action, coordinates are not taken into account
#     assert 'Quickened Firebolt on Goblin' in transitions
#
# def test_select_best_action_movement_and_staff_attack(battle_map, teams, effect_tracker, combatant1, combatant2, combatant3):
#     battle_map.build_adjacency_matrix()
#     battle_map.set_effect_tracker(effect_tracker)
#     effect_tracker.set_battle_map(battle_map)
#     teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
#     teams.add_combatant_to_team(combatant2, Teams.Color.RED)
#     # teams.add_combatant_to_team(combatant3, Teams.Color.RED)
#     battle_map.set_combatant_coordinates(combatant1, np.array([1, 3]))
#     battle_map.set_combatant_coordinates(combatant2, np.array([10, 10]))
#     # battle_map.set_combatant_coordinates(combatant3, np.array([2, 3]))
#
#     dfs = select_best_action(combatant1, battle_map)
#     # Tests regular movement + staff of defence attack
#     assert dfs.state == '0'
#     dfs.trigger("m_(9, 10)")
#     transitions = dfs.get_available_transitions()
#     # Check that we have all the action (except for the Staff attack) available
#     assert 'Quickened Fireball at [ 6 10]' in transitions
#     assert 'Quickened Firebolt on Goblin' in transitions
#     assert 'Quickened Haste on Faurung' in transitions
#     assert 'Fireball at [ 6 10]' in transitions
#     assert 'Firebolt on Goblin' in transitions
#     assert 'Haste on Faurung' in transitions
#     assert 'Staff of Defence on Goblin' in transitions
#     assert 'Dodge of Faurung' not in transitions  # Once you do a regular move, Dodge should not be available
#     assert 'Disengage of Faurung' not in transitions  # Once you do a regular move, Disengage should not be available
#     dfs.trigger("Staff of Defence on Goblin")
#     transitions = dfs.get_available_transitions()
#     # For the second action, coordinates are not taken into account, but Dodge is included
#     assert 'Quickened Fireball at [ 6 10]' in transitions
#     assert 'Quickened Firebolt on Goblin' in transitions
#     assert 'Quickened Haste on Faurung' in transitions
#
# def test_select_best_action_misty_step_and_staff_attack(battle_map, teams, effect_tracker, combatant1, combatant2,
#                                                       combatant3):
#     battle_map.build_adjacency_matrix()
#     battle_map.set_effect_tracker(effect_tracker)
#     effect_tracker.set_battle_map(battle_map)
#     teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
#     teams.add_combatant_to_team(combatant2, Teams.Color.RED)
#     # teams.add_combatant_to_team(combatant3, Teams.Color.RED)
#     battle_map.set_combatant_coordinates(combatant1, np.array([1, 3]))
#     battle_map.set_combatant_coordinates(combatant2, np.array([10, 10]))
#     # battle_map.set_combatant_coordinates(combatant3, np.array([2, 3]))
#
#     dfs = select_best_action(combatant1, battle_map)
#     # Tests Misty Step movement + staff of defence attack
#     assert dfs.state == '0'
#     dfs.trigger("ms_(9, 10)")
#     transitions = dfs.get_available_transitions()
#     # Check that we have all the action (except for the Staff attack) available
#     assert "Staff of Defence on Goblin" in transitions  # Test that Misty Step actions are also prepended with movement
#     assert "Firebolt on Goblin" in transitions
#     dfs.trigger("Staff of Defence on Goblin")
#     assert len(dfs.get_available_transitions()) == 0
#
# def test_select_best_action_dodge_and_movement_and_quickened_spell(battle_map, teams, effect_tracker, combatant1, combatant2, combatant3):
#     battle_map.build_adjacency_matrix()
#     battle_map.set_effect_tracker(effect_tracker)
#     effect_tracker.set_battle_map(battle_map)
#     teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
#     teams.add_combatant_to_team(combatant2, Teams.Color.RED)
#     # teams.add_combatant_to_team(combatant3, Teams.Color.RED)
#     battle_map.set_combatant_coordinates(combatant1, np.array([1, 3]))
#     battle_map.set_combatant_coordinates(combatant2, np.array([10, 10]))
#     # battle_map.set_combatant_coordinates(combatant3, np.array([2, 3]))
#
#     dfs = select_best_action(combatant1, battle_map)
#     # Tests Dodge + movement + a quickened spell
#     assert dfs.state == '0'
#     dfs.trigger("Dodge of Faurung")
#     assert dfs.state == 'Dodged'
#     transitions = dfs.get_available_transitions()
#     assert "m_(7, 3)" in transitions
#     assert "ms_(2, 3)" not in transitions  # Even though it's possible, we don't support Misty Step after Dodge, as it's very niche
#     dfs.trigger("m_(7, 3)")
#     assert dfs.state == "do_(7, 3)"
#     transitions = dfs.get_available_transitions()
#     assert 'Quickened Fireball at [ 6 10]' in transitions
#     assert 'Quickened Firebolt on Goblin' in transitions
#     assert 'Quickened Haste on Faurung' in transitions
#     dfs.trigger("Quickened Haste on Faurung")
#     assert len(dfs.get_available_transitions()) == 0
#
# def test_select_best_action_disengage_and_movement_and_quickened_spell(battle_map, teams, effect_tracker, combatant1, combatant2, combatant3):
#     battle_map.build_adjacency_matrix()
#     battle_map.set_effect_tracker(effect_tracker)
#     effect_tracker.set_battle_map(battle_map)
#     teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
#     teams.add_combatant_to_team(combatant2, Teams.Color.RED)
#     # teams.add_combatant_to_team(combatant3, Teams.Color.RED)
#     battle_map.set_combatant_coordinates(combatant1, np.array([1, 3]))
#     battle_map.set_combatant_coordinates(combatant2, np.array([10, 10]))
#     # battle_map.set_combatant_coordinates(combatant3, np.array([2, 3]))
#
#     dfs = select_best_action(combatant1, battle_map)
#     # Tests Disengage + movement + a quickened spell
#     assert dfs.state == '0'
#     dfs.trigger("Disengage of Faurung")
#     assert dfs.state == 'Disengaged'
#     transitions = dfs.get_available_transitions()
#     assert "m_(5, 3)" in transitions
#     assert "ms_(2, 3)" not in transitions  # Even though it's possible, we don't support Misty Step after Dodge, as it doesn't make muche sense
#     dfs.trigger("m_(5, 3)")
#     assert dfs.state == "di_(5, 3)"
#     transitions = dfs.get_available_transitions()
#     assert 'Quickened Fireball at [ 6 10]' in transitions
#     assert 'Quickened Firebolt on Goblin' in transitions
#     assert 'Quickened Haste on Faurung' in transitions
#     dfs.trigger("Quickened Firebolt on Goblin")
#     assert len(dfs.get_available_transitions()) == 0
