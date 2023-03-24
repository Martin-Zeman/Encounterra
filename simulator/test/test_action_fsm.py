import pytest
from simulator.actions.action_fsms import generate_action_fsm, StateMachineTemplate
from simulator.teams import Teams
from simulator.test.fixtures import combatant1, battle_map, effect_tracker, teams

def test_state_machine_template():
    fsm = StateMachineTemplate()
    assert fsm.state == 'initial'
    fsm.add_state('A')
    fsm.add_state('B')
    fsm.add_state('C')
    fsm.add_state('D')
    fsm.add_transition('to_A', 'initial', 'A')
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


# def test_generate_state_name():
#     assert generate_state_name('A') == 'B'
#     assert generate_state_name('C') == 'C'
#     assert generate_state_name('Z') == 'AA'
#     assert generate_state_name('AA') == 'AB'
#     assert generate_state_name('FGR') == 'FGS'
#     assert generate_state_name('FGRZ') == 'FGS'

def test_generate_action_fsm(combatant1, battle_map, effect_tracker, teams):
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)
    fsm = generate_action_fsm(combatant1, battle_map)