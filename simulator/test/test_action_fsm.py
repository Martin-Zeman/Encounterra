import numpy as np
import pytest
from simulator.actions.action_fsms import generate_action_fsm
from simulator.utils.state_machine_template import StateMachineTemplate
from simulator.combatant_coords import Coords
from simulator.teams import Teams
from simulator.test.fixtures import *
# from transitions.extensions import GraphMachine

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


def test_remove_state():
    fsm = StateMachineTemplate()
    try:
        fsm.add_new_state('A')
        fsm.add_transition('to_A', '0', 'A')
        fsm.add_transition('to_nop', 'A', 'nop')
        fsm.remove_transition('to_A', '0')
        fsm.add_transition('to_A', '0', 'A')
        fsm.remove_transition('to_A', '0')
        fsm.add_transition('to_A', '0', 'A')
    except Exception as e:
        assert False, f"Raised an exception {e}"
    # Have to inspect the log output manually


def test_generate_action_fsm(test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian, test_stone_giant, test_ogre, battle_map, effect_tracker, teams):
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)
    teams.add_combatant_to_team(test_ogre, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([7, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([5, 11]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([10, 12]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([11, 6]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([0, 0]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([13, 6]))
    fsm, transition_mapping, _ = generate_action_fsm(test_draconic_sorcerer_5lvl)
    assert fsm.state == '0'
    # fsm.get_graph().draw('state_diagram_faurung.png', prog='dot')

    fsm, transition_mapping, _ = generate_action_fsm(test_goblin)
    assert fsm.state == '0'
    # fsm.get_graph().draw('state_diagram_goblin.png', prog='dot')

    fsm, transition_mapping, _ = generate_action_fsm(test_bugbear)
    assert fsm.state == '0'
    # fsm.get_graph().draw('state_diagram_bugbear.png', prog='dot')

    fsm, transition_mapping, _ = generate_action_fsm(test_totem_barbarian)
    assert fsm.state == '0'
    # fsm.get_graph().draw('state_diagram_totem_barbarian5lvl.png', prog='dot')

    fsm, transition_mapping, _ = generate_action_fsm(test_stone_giant)
    assert fsm.state == '0'
    # fsm.get_graph().draw('state_diagram_stone_giant.png', prog='dot')

    fsm, transition_mapping, _ = generate_action_fsm(test_ogre)
    assert fsm.state == '0'
    # fsm.get_graph().draw('state_diagram_ogre.png', prog='dot')

