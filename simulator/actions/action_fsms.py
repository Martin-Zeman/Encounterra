import copy
from statemachine import State, StateMachine
from simulator.feasibility import get_feasible_factories
from simulator.resources import use_resources


# class TwoMeleeOneRangedWithReckless(StateMachine):
#     A = State("A", (1, 2, 3), initial=True)  # not attacked yet
#     B = State("B", (1,))  # attacked with melee
#     C = State("C", (2,))  # attacked with melee recklessly
#     nop = State("nop", value=(), final=True)
#     melee = A.to(B) | B.to(nop)
#     melee_recklessly = A.to(C) | C.to(nop)
#     ranged = A.to(nop)


# class TwoMeleeOneRanged(StateMachine):
#     A = State("A", value=(1, 2), initial=True)  # not attacked yet
#     B = State("B", value=(1,))  # attacked once
#     nop = State("nop", value=(),final=True)
#     melee = A.to(B) | B.to(nop)
#     ranged = A.to(nop)

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


from transitions import Machine, State
from transitions.extensions import GraphMachine
class StateMachineTemplate(GraphMachine):


    def __init__(self):
        states = ['0', 'nop']
        GraphMachine.__init__(self, states=states, initial='0', ignore_invalid_triggers=True, auto_transitions=False)
        self.last_added_state = '-1'

    def add_new_state(self, state_name):
        self.add_state(State(state_name))
        # self.last_added_state = state_name

    def get_next_state_name(self):
        self.last_added_state = str(int(self.last_added_state) + 1)
        return self.last_added_state

    # def add_transition(self, name, from_state, to_state):
    #     self.machine.add_transition(trigger=name, source=from_state, dest=to_state)

    def get_available_transitions(self):
        return self.get_triggers(self.state)


class AttackStateMachineTemplate(StateMachineTemplate):
    """
    Attack sequences are modelled by their own state machines which are used by resoures and feasibility as well as to build
    the overall action state machines.
    """
    def __init__(self):
        super().__init__()
        self.add_state('0')


def actions_to_set(actions):
    return frozenset([str(f) for f in actions])


def get_all_feasible_action_factories(combatant, battle_map):
    feasible_action_factories = get_feasible_factories(combatant.action_factories, combatant, battle_map)
    feasible_bonus_action_factories = get_feasible_factories(combatant.bonus_action_factories, combatant, battle_map)
    feasible_haste_action_factories = get_feasible_factories(combatant.haste_action_factories, combatant, battle_map)
    all_action_factories = feasible_action_factories
    all_action_factories.extend(feasible_bonus_action_factories)
    all_action_factories.extend(feasible_haste_action_factories)
    return all_action_factories

def generate_action_fsm(combatant, battle_map):
    fsm = StateMachineTemplate()
    # initial_resources = combatant.export_resources()
    state_footprint_to_count = dict()
    visited = set()
    transition_name_to_action = dict()
    def dfs(previous_state_name, action_taken=None):
        fafs = get_all_feasible_action_factories(combatant, battle_map)
        fas = [faf[1].create_all(battle_map) for faf in fafs]
        fas = [fa for sublist in fas for fa in sublist]
        state_footprint = actions_to_set(fas)
        if not state_footprint:
            fsm.add_transition(str(action_taken), previous_state_name, 'nop')
        elif state_footprint not in visited:
            new_state_name = fsm.get_next_state_name()
            state_footprint_to_count[state_footprint] = new_state_name
            if action_taken:
                action_name = str(action_taken)
                transition_name_to_action[action_name] = action_taken
                fsm.add_transition(action_name, previous_state_name, new_state_name)
                fsm.add_new_state(new_state_name)  # Avoid adding the initial state again
            visited.add(state_footprint)
            for fa in fas:
                exported_resources = combatant.export_resources()
                use_resources(combatant, fa, battle_map)
                dfs(new_state_name, str(fa))
                combatant.load_resources(exported_resources)
        else:
            fsm.add_transition(str(action_taken), previous_state_name, state_footprint_to_count[state_footprint])
    dfs('0')
    return fsm, transition_name_to_action
