from transitions import State, Machine
from transitions.extensions import GraphMachine

class StateMachineTemplate(Machine):
    """
    A thin wrapper for the Machine. It tracks the last added state to help build up the action FSM.
    """

    def __init__(self):
        states = ['0', 'nop']
        Machine.__init__(self, states=states, initial='0', ignore_invalid_triggers=True, auto_transitions=False)
        self.last_added_state = '-1'
        self.dependencies = {'nop': ['0']}
        self.forward_transitions = dict()

    def add_new_state(self, state_name):
        self.add_state(State(state_name))

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
            self.dependencies[dest].append(origin)
        except KeyError:
            self.dependencies[dest] = [origin]

        try:
            self.forward_transitions[origin].append((name, dest))
        except KeyError:
            self.forward_transitions[origin] = [(name, dest)]
        super().add_transition(name, origin, dest)


    def reset(self):
        self.set_state('0')

class GraphStateMachineTemplate(GraphMachine):
    """
    A thin wrapper for the GraphMachine. It tracks the last added state to help build up the action FSM.
    """

    def __init__(self):
        states = ['0', 'nop']
        GraphMachine.__init__(self, states=states, initial='0', ignore_invalid_triggers=True, auto_transitions=False)
        self.last_added_state = '-1'
        self.dependencies = {'nop': ['0']}
        self.forward_transitions = dict()

    def add_new_state(self, state_name):
        self.add_state(State(state_name))

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
            self.dependencies[dest].append(origin)
        except KeyError:
            self.dependencies[dest] = [origin]

        try:
            self.forward_transitions[origin].append((name, dest))
        except KeyError:
            self.forward_transitions[origin] = [(name, dest)]
        super().add_transition(name, origin, dest)

    def reset(self):
        self.set_state('0')


# class AttackStateMachineTemplate(StateMachineTemplate):
#     """
#     Attack sequences are modelled by their own state machines which are used by resoures and feasibility as well as to build
#     the overall action state machines.
#     """
#     def __init__(self):
#         super().__init__()
#         self.add_state('0')