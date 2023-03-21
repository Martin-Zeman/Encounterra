import copy

from statemachine import State, StateMachine

from simulator.feasibility import get_feasible_actions


class TwoMeleeOneRangedWithReckless(StateMachine):
    A = State("A", (1, 2, 3), initial=True)  # not attacked yet
    B = State("B", (1,))  # attacked with melee
    C = State("C", (2,))  # attacked with melee recklessly
    nop = State("nop", value=(), final=True)
    melee = A.to(B) | B.to(nop)
    melee_recklessly = A.to(C) | C.to(nop)
    ranged = A.to(nop)


class TwoMeleeOneRanged(StateMachine):
    A = State("A", value=(1, 2), initial=True)  # not attacked yet
    B = State("B", value=(1,))  # attacked once
    nop = State("nop", value=(),final=True)
    melee = A.to(B) | B.to(nop)
    ranged = A.to(nop)

class OneAttack(StateMachine):
    A = State("A", value=(1,), initial=True)  # not attacked yet
    nop = State("nop", value=(), final=True)
    attack = A.to(nop)

class FaurungFSM(StateMachine):
    A = State("A", value=(1,), initial=True)  # not attacked yet
    nop = State("nop", value=(), final=True)
    attack = A.to(nop)


class OneMeleeOrOneRanged(StateMachine):
    A = State("A", value=(1, 2, 3, 4), initial=True)  # not attacked yet
    nop = State("nop", value=(), final=True)
    melee = A.to(nop)
    ranged = A.to(nop)
    dodge = A.to(nop)
    disengage = A.to(nop)


class EmptyStateMachineTemplate(StateMachine):
    A = State("A", value=(), initial=True)
    nop = State("nop", value=(), final=True)

def generate_action_fsm(combatant, battle_map):
    fsm = EmptyStateMachineTemplate()
    combatant_copy = copy.deepcopy(combatant)
    feasible_action_factories = get_feasible_actions(combatant.action_factories, combatant_copy, battle_map)
    feasible_bonus_action_factories = get_feasible_actions(combatant.bonus_action_factories, combatant_copy, battle_map)
    feasible_haste_action_factories = get_feasible_actions(combatant.haste_action_factories, combatant_copy, battle_map)
    all_action_factories = feasible_action_factories
    all_action_factories.extend(feasible_bonus_action_factories)
    all_action_factories.extend(feasible_haste_action_factories)
    feasible_actions_to_state_mapping = dict()

