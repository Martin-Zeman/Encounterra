import copy
from statemachine import State, StateMachine
from simulator.feasibility import get_feasible_actions
from simulator.resources import use_resources


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

# class OneAttack(StateMachine):
#     A = State("A", value=(1,), initial=True)  # not attacked yet
#     nop = State("nop", value=(), final=True)
#     attack = A.to(nop)

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


from transitions import Machine, State
class StateMachineTemplate:
    states = ['initial', 'nop']

    def __init__(self):
        self.machine = Machine(model=self, states=StateMachineTemplate.states, initial='initial', ignore_invalid_triggers=True, auto_transitions=False)

    def add_state(self, state_name):
        self.machine.add_state(State(state_name))

    def add_transition(self, name, from_state, to_state):
        self.machine.add_transition(trigger=name, source=from_state, dest=to_state)

    def get_available_transitions(self):
        return self.machine.get_triggers(self.state)

    # def get_transitions(self, state_name):
    #     return self.machine.get_triggers(state_name)




# def generate_state_name(last_state_name):
#     if last_state_name[-1] < 'Z':
#         return last_state_name[:-1] + chr(ord(last_state_name[-1]) + 1)
#     return last_state_name + 'A'

def factories_to_set(factories):
    s = set()
    for f in factories:
        s.add(str(f[1]))
    return s




def get_all_feasible_action_factories(combatant, battle_map):
    feasible_action_factories = get_feasible_actions(combatant.action_factories, combatant, battle_map)
    feasible_bonus_action_factories = get_feasible_actions(combatant.bonus_action_factories, combatant, battle_map)
    feasible_haste_action_factories = get_feasible_actions(combatant.haste_action_factories, combatant, battle_map)
    all_action_factories = feasible_action_factories
    all_action_factories.extend(feasible_bonus_action_factories)
    all_action_factories.extend(feasible_haste_action_factories)
    return all_action_factories

def generate_action_fsm(combatant, battle_map):
    fsm = StateMachineTemplate()
    # combatant_copy = copy.deepcopy(combatant)
    initial_resources = combatant.export_resources()

    visited = []
    def dfs(resources):
        combatant.load_resources(resources)
        faf = get_all_feasible_action_factories(combatant, battle_map)
        state_footprint = factories_to_set(faf)
        if state_footprint not in visited:
            visited.append(state_footprint)
            for f in faf:
                action = f[1].create_mock()
                use_resources(combatant, action, battle_map)
                exported_resources = combatant.export_resources()
                dfs(exported_resources)
    dfs(initial_resources)
    return visited
    # Use something like DFS, but for every node make a copy of the resources and to load them again (this would be combatant specific function I guess)

