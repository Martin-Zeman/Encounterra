import numpy as np
import pytest

from simulator.actions.action_fsms import generate_action_fsm
from simulator.combatant_coords import CombatantCoords
from simulator.teams import Teams
from simulator.test.fixtures import combatant1, combatant2, combatant3, teams, effect_tracker, battle_map
from simulator.actions.action_selector import select_best_action

def test_select_best_action(battle_map, teams, effect_tracker, combatant1, combatant2, combatant3):
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
    assert "ms_(7, 3)" in transitions
    assert "ms_(2, 3)" in transitions
    assert "m_(7, 3)" in transitions
    dfs.trigger("ms_(2, 3)")
    transitions = dfs.get_available_transitions()
    assert "Staff of Defence on Goblin" not in transitions  # Test that Misty Step actions are also prepended with movement
    # TODO What about the Dodge here?
    assert "Firebolt on Goblin" in transitions
    dfs.trigger("Firebolt on Goblin")
    assert len(dfs.get_available_transitions()) == 0

    # Tests regular movement + quickened fireball
    dfs.reset()
    assert dfs.state == '0'
    dfs.trigger("m_(2, 3)")
    transitions = dfs.get_available_transitions()
    # Check that we have all the action (except for the Staff attack) available
    assert 'Quickened Fireball at [ 6 10]' in transitions
    assert 'Quickened Firebolt on Goblin' in transitions
    assert 'Quickened Haste on Faurung' in transitions
    assert 'Fireball at [ 6 10]' in transitions
    assert 'Firebolt on Goblin' in transitions
    assert 'Haste on Faurung' in transitions
    dfs.trigger("Quickened Fireball at [ 6 10]")
    transitions = dfs.get_available_transitions()
    # For the second action, coordinates are not taken into account, but Dodge is included
    assert 'Staff of Defence on Goblin' in transitions
    assert 'Firebolt on Goblin' in transitions
    assert 'Dodge of Faurung' in transitions

    # Tests regular movement + fireball
    dfs.reset()
    assert dfs.state == '0'
    dfs.trigger("m_(2, 3)")
    transitions = dfs.get_available_transitions()
    # Check that we have all the action (except for the Staff attack) available
    assert 'Quickened Fireball at [ 6 10]' in transitions
    assert 'Quickened Firebolt on Goblin' in transitions
    assert 'Quickened Haste on Faurung' in transitions
    assert 'Fireball at [ 6 10]' in transitions
    assert 'Firebolt on Goblin' in transitions
    assert 'Haste on Faurung' in transitions
    dfs.trigger("Fireball at [ 6 10]")
    transitions = dfs.get_available_transitions()
    # For the second action, coordinates are not taken into account, but Dodge is included
    assert 'Quickened Firebolt on Goblin' in transitions

    # Tests regular movement + staff of defence attack
    dfs.reset()
    assert dfs.state == '0'
    dfs.trigger("m_(9, 10)")
    transitions = dfs.get_available_transitions()
    # Check that we have all the action (except for the Staff attack) available
    assert 'Quickened Fireball at [ 6 10]' in transitions
    assert 'Quickened Firebolt on Goblin' in transitions
    assert 'Quickened Haste on Faurung' in transitions
    assert 'Fireball at [ 6 10]' in transitions
    assert 'Firebolt on Goblin' in transitions
    assert 'Haste on Faurung' in transitions
    assert 'Staff of Defence on Goblin' in transitions
    dfs.trigger("Staff of Defence on Goblin")
    transitions = dfs.get_available_transitions()
    # For the second action, coordinates are not taken into account, but Dodge is included
    assert 'Quickened Fireball at [ 6 10]' in transitions
    assert 'Quickened Firebolt on Goblin' in transitions
    assert 'Quickened Haste on Faurung' in transitions

    # Tests Misty Step movement + staff of defence attack
    dfs.reset()
    assert dfs.state == '0'
    dfs.trigger("ms_(9, 10)")
    transitions = dfs.get_available_transitions()
    # Check that we have all the action (except for the Staff attack) available
    assert "Staff of Defence on Goblin" in transitions  # Test that Misty Step actions are also prepended with movement
    assert "Firebolt on Goblin" in transitions
    # assert "Dodge of Faurung" in transitions  TODO figure out the Dodge
    dfs.trigger("Staff of Defence on Goblin")
    assert len(dfs.get_available_transitions()) == 0

