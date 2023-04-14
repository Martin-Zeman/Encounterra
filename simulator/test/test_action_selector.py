import numpy as np
import pytest

from simulator.actions.action_fsms import generate_action_fsm
from simulator.combatant_coords import CombatantCoords
from simulator.teams import Teams
from simulator.test.fixtures import combatant1, combatant2, teams, effect_tracker, battle_map
from simulator.actions.action_selector import select_best_action

def test_select_best_action(battle_map, teams, effect_tracker, combatant1, combatant2):
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant2, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(combatant1, np.array([1, 3]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(combatant2, np.array([10, 10]))  # Have to set it for fireball placement

    # fsm, transition_mapping = generate_action_fsm(combatant1, battle_map)
    # assert fsm.state == '0'
    # fsm.get_graph().draw('state_diagram_faurung_pre_coords.png', prog='dot')

    dfs, _ = select_best_action(combatant1, battle_map)
    dfs.get_graph().draw('state_diagram_faurung_with_coords.png', prog='dot')