from simulator.actions.action_fsms import generate_action_fsm
from simulator.feasibility import get_feasible_actions
from simulator.test.fixtures import combatant1, battle_map

def test_generate_action_fsm(combatant1, battle_map):
    fsm = generate_action_fsm(combatant1, battle_map)