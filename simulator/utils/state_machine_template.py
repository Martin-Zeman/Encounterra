from transitions import State, Machine

class StateMachineTemplate(Machine):
    """
    A thin wrapper for the Machine. It tracks the last added state to help build up the action FSM.
    """

    def __init__(self):
        states = ['0', 'nop']
        Machine.__init__(self, states=states, initial='0', ignore_invalid_triggers=True, auto_transitions=False)
        self.last_added_state = '-1'
        self.forward_transitions = dict()

    def add_new_state(self, state_name):
        self.add_state(State(state_name))

    def remove_state(self, state_name):
        for t in self.get_available_transitions_in_state(state_name):
            self.remove_transition(t, state_name)

    def get_next_state_name(self):
        self.last_added_state = str(int(self.last_added_state) + 1)
        return self.last_added_state

    def get_available_transitions(self):
        return self.get_triggers(self.state)

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


    def reset(self):
        self.set_state('0')
