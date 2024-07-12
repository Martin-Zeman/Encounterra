import copy

from transitions import State, Machine
import numpy as np


class StateMachineTemplate(Machine):
    """
    A thin wrapper for the Machine. It tracks the last added state to help build up the action FSM.
    """

    def __init__(self):
        states = ['0', 'nop']
        Machine.__init__(self, states=states, initial='0', ignore_invalid_triggers=True, auto_transitions=False)
        self.last_added_state = '-1'
        self.forward_transitions = dict()
        # self.state_to_index = nb.typed.Dict.empty(key_type=nb.types.unicode_type, value_type=nb.types.int32)
        # self.index_to_state = nb.typed.Dict.empty(key_type=nb.types.int32, value_type=nb.types.unicode_type)
        # self.transition_to_index = nb.typed.Dict.empty(key_type=nb.types.unicode_type, value_type=nb.types.int32)
        # self.index_to_transition = nb.typed.Dict.empty(key_type=nb.types.int32, value_type=nb.types.unicode_type)
        # self.state_to_index['0'] = 0
        # self.state_to_index['nop'] = 1
        # self.index_to_state[0] = '0'
        # self.index_to_state[1] = 'nop'
        # self.dag_forward = None
        # self.num_states = 2
        # self.max_transitions = 0

        self.state_to_index = {'0': 0, 'nop': 1}
        self.index_to_state = {0: '0', 1: 'nop'}
        self.transition_to_index = {}
        self.transition_to_simplified = {}  # Mapping from transition index -> index of transition with trailing level designator removed
        self.simplified_transitions = {}  # Helper to transition_to_simplified
        self.index_to_transition = {}
        self.dag_forward = None
        self.num_states = 2
        self.max_transitions = 0

    def add_new_state(self, state_name):
        if state_name not in self.state_to_index:
            self.add_state(State(state_name))
            self.state_to_index[state_name] = self.num_states
            self.index_to_state[self.num_states] = state_name
            self.num_states += 1

    def remove_state(self, state_name):
        for t in self.get_available_transitions_in_state(state_name):
            self.remove_transition(t, state_name)
        index = self.state_to_index.pop(state_name)
        del self.index_to_state[index]
        self.num_states -= 1

    def get_next_state_name(self):
        self.last_added_state = str(int(self.last_added_state) + 1)
        return self.last_added_state

    def get_available_transitions(self):
        return self.get_triggers(self.state)

    def get_all_transitions(self):
        return [trigger for s in self.states for trigger in self.get_triggers(s)]

    def get_available_transitions_in_state(self, state):
        return self.get_triggers(state)

    def add_transition(self, name, origin, dest):
        """
        Overrides the add_transition of the Machine to allow us to build our dependency dictionary on the side and
        enable us to do a topological sort directly without additional processing.
        At the same time we're building our simplified version of forward transitions. This is the reverse of the
        dependencies which tells us which states are directly reachable from a given source state. It is possible
        to extract this information from the Machine itself but only with extra processing. This serves as sort of a
        cache.
        :param name: name of the transition
        :param origin: name of the origin state
        :param dest: name of the destination state
        :return:
        """
        try:
            self.forward_transitions[origin].add((name, dest))
        except KeyError:
            self.forward_transitions[origin] = {(name, dest)}
        super().add_transition(name, origin, dest)

        if name not in self.transition_to_index:
            index = len(self.transition_to_index)
            self.transition_to_index[name] = index
            self.index_to_transition[index] = name

            # This is an optimization to make equivalent sequence detection easier later on
            shortened_name = name[:-2] if name[-2] == "_" else name  # Removes the trailing level designator
            if shortened_name not in self.simplified_transitions:
                simplified_index = len(self.simplified_transitions)
                self.simplified_transitions[shortened_name] = simplified_index
            else:
                simplified_index = self.simplified_transitions[shortened_name]

            self.transition_to_simplified[index] = simplified_index

        self.max_transitions = max(self.max_transitions, len(self.forward_transitions[origin]))

    def remove_transition(self, transition_name, origin):
        """
        Overrides the remove_transition of the Machine to allow us to also remove from the forward dictionary on the side
        :param transition_name: name of the transition
        :param origin: name of the origin state
        :param dest: name of the destination state
        :return:
        """
        try:
            transition_name = next(ft[0] for ft in self.forward_transitions[origin] if ft[0].split("_")[0] == transition_name.split("_")[0])
            self.forward_transitions[origin] = {ft for ft in self.forward_transitions[origin] if ft[0] != transition_name}
            if not self.forward_transitions[origin]:  # Created a dead end
                self.add_transition("dummy", origin, 'nop')
            super().remove_transition(transition_name, origin)
        except (ValueError, KeyError, StopIteration):
            pass

    def _update_dag_forward(self):
        # all states, all transitions from that state (pre-allocated to max num transitions from any state), transition index/next state
        self.dag_forward = np.full((self.num_states, self.max_transitions, 2), -1, dtype=np.int32)
        for state, transitions in self.forward_transitions.items():
            state_idx = self.state_to_index[state]
            for i, (transition, next_state) in enumerate(transitions):
                self.dag_forward[state_idx, i, 0] = self.transition_to_index[transition]
                self.dag_forward[state_idx, i, 1] = self.state_to_index[next_state]

    def get_numba_compatible_data(self):
        self._update_dag_forward()
        return self.dag_forward, self.num_states, self.index_to_state, self.index_to_transition, self.transition_to_simplified

    def reset(self):
        self.set_state('0')
