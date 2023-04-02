import numpy as np
import pytest
from simulator.actions.action_fsms import generate_action_fsm, StateMachineTemplate
from simulator.combatant_coords import CombatantCoords
from simulator.teams import Teams
from simulator.test.fixtures import *
from transitions.extensions import GraphMachine

def test_state_machine_template():
    fsm = StateMachineTemplate()
    assert fsm.state == '0'
    fsm.add_new_state('A')
    fsm.add_new_state('B')
    fsm.add_new_state('C')
    fsm.add_new_state('D')
    fsm.add_transition('to_A', '0', 'A')
    fsm.add_transition('to_B', 'A', 'B')
    fsm.add_transition('to_C', 'B', 'C')
    fsm.add_transition('to_D', 'B', 'D')
    fsm.add_transition('to_nop', 'C', 'nop')
    fsm.add_transition('to_nop', 'D', 'nop')
    assert fsm.get_available_transitions() == ['to_A']
    fsm.to_A()
    assert fsm.state == 'A'
    assert fsm.is_A()
    assert fsm.get_available_transitions() == ['to_B']
    fsm.to_B()
    assert fsm.state == 'B'
    assert fsm.get_available_transitions() == ['to_C', 'to_D']
    fsm.to_D()
    assert fsm.state == 'D'
    assert fsm.get_available_transitions() == ['to_nop']
    fsm.to_nop()
    assert fsm.state == 'nop'
    assert fsm.get_available_transitions() == []


def test_generate_action_fsm(combatant1, combatant2, combatant3, combatant4, combatant5, combatant6, battle_map, effect_tracker, teams):
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant2, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)
    teams.add_combatant_to_team(combatant4, Teams.Color.RED)
    teams.add_combatant_to_team(combatant5, Teams.Color.RED)
    teams.add_combatant_to_team(combatant6, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(combatant1, CombatantCoords(np.array([7, 3]), combatant1.size))
    battle_map.set_combatant_coordinates(combatant2, CombatantCoords(np.array([5, 11]), combatant2.size))
    battle_map.set_combatant_coordinates(combatant3, CombatantCoords(np.array([10, 12]), combatant3.size))
    battle_map.set_combatant_coordinates(combatant4, CombatantCoords(np.array([11, 6]), combatant4.size))
    fsm, transition_mapping = generate_action_fsm(combatant1, battle_map)
    assert fsm.state == '0'
    # graph_machine = GraphMachine(model=fsm, use_pygraphviz=False)
    fsm.get_graph().draw('state_diagram_faurung.png', prog='dot')

    fsm, transition_mapping = generate_action_fsm(combatant2, battle_map)
    assert fsm.state == '0'
    # graph_machine = GraphMachine(model=fsm, use_pygraphviz=False)
    fsm.get_graph().draw('state_diagram_goblin.png', prog='dot')

    fsm, transition_mapping = generate_action_fsm(combatant3, battle_map)
    assert fsm.state == '0'
    # graph_machine = GraphMachine(model=fsm, use_pygraphviz=False)
    fsm.get_graph().draw('state_diagram_bugbear.png', prog='dot')

    fsm, transition_mapping = generate_action_fsm(combatant4, battle_map)
    assert fsm.state == '0'
    # graph_machine = GraphMachine(model=fsm, use_pygraphviz=False)
    fsm.get_graph().draw('state_diagram_totem_barbarian5lvl.png', prog='dot')

    fsm, transition_mapping = generate_action_fsm(combatant5, battle_map)
    assert fsm.state == '0'
    # graph_machine = GraphMachine(model=fsm, use_pygraphviz=False)
    fsm.get_graph().draw('state_diagram_stone_giant.png', prog='dot')

    fsm, transition_mapping = generate_action_fsm(combatant6, battle_map)
    assert fsm.state == '0'
    # graph_machine = GraphMachine(model=fsm, use_pygraphviz=False)
    fsm.get_graph().draw('state_diagram_ogre.png', prog='dot')

