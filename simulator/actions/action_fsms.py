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


from transitions import State, Machine
# from transitions.extensions import GraphMachine

# class StateMachineTemplate(GraphMachine):
class StateMachineTemplate(Machine):
    """
    A thin wrapper for the GraphMachine. It tracks the last added state to help build up the action FSM.
    """


    def __init__(self):
        states = ['0', 'nop']
        # GraphMachine.__init__(self, states=states, initial='0', ignore_invalid_triggers=True, auto_transitions=False)
        Machine.__init__(self, states=states, initial='0', ignore_invalid_triggers=True, auto_transitions=False)
        self.last_added_state = '-1'

    def add_new_state(self, state_name):
        self.add_state(State(state_name))

    def get_next_state_name(self):
        self.last_added_state = str(int(self.last_added_state) + 1)
        return self.last_added_state

    def get_available_transitions(self):
        return self.get_triggers(self.state)

    def get_available_transitions_in_state(self, state):
        return self.get_triggers(state)

    # def get_actions_leading_to_state(self, state):
    #     actions = []
    #     for action_name, event in self.events.items():
    #         for transition in event.transitions.values():
    #             if transition[0].dest == state:
    #                 actions.append(action_name)
    #     return actions

    def reset(self):
        self.set_state('0')


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
    """
    A helper functions which collects all feasible (bonus/haste) action factories for a combatant
    :param combatant: for whom the feasible factories are is to be constructed
    :param battle_map:
    :return: all feasible (bonus/haste) action factories for a combatant
    """
    feasible_action_factories = get_feasible_factories(combatant.action_factories, combatant, battle_map)
    feasible_bonus_action_factories = get_feasible_factories(combatant.bonus_action_factories, combatant, battle_map)
    feasible_haste_action_factories = get_feasible_factories(combatant.haste_action_factories, combatant, battle_map)
    all_action_factories = feasible_action_factories
    all_action_factories.extend(feasible_bonus_action_factories)
    all_action_factories.extend(feasible_haste_action_factories)
    return all_action_factories

def generate_action_fsm(combatant, battle_map):
    """
    Builds a combatant-specific FSM which expresses all possible (bonus) action combinations the may take on their turn.
    It assumes the combatant's attack FSM is manually constructed already and is used as an input for the overall FSM.
    Misty Step gets a special treatment.
    :param combatant: for whom the FSM is to be constructed
    :param battle_map:
    :return: fsm, the mapping between FSM transition names to the actual action factory objects,
    list of actions that can be taken after misty step
    """
    fsm = StateMachineTemplate()
    state_footprint_to_state_name = dict()
    visited = set()
    transition_name_to_action = dict()
    misty_step_state = None
    def dfs(previous_state_name, action_taken=None):
        """
        Internal function which recursively builds the action FSM in a DFS manner
        """
        nonlocal misty_step_state
        fafs = get_all_feasible_action_factories(combatant, battle_map)
        fas = [faf[1].create_all(battle_map) for faf in fafs]
        fas = [fa for sublist in fas for fa in sublist]  # flatten the fas from a list of lists into a single list
        # A state is fully defined by all the possible (bonus) actions the combatant may take in it
        state_footprint = actions_to_set(fas)
        action_taken_name = str(action_taken)
        if not state_footprint:
            # no more actions -> connect to the nop state
            if "Misty Step" not in action_taken_name:
                transition_name_to_action[action_taken_name] = action_taken  # TODO This can be taken out of the if else
                fsm.add_transition(action_taken_name, previous_state_name, 'nop')
        elif state_footprint not in visited:
            visited.add(state_footprint)
            new_state_name = fsm.get_next_state_name()
            state_footprint_to_state_name[state_footprint] = new_state_name
            if action_taken:
                fsm.add_new_state(new_state_name)  # Avoid adding the initial state again
                if "Misty Step" in action_taken_name:
                    # Misty Step gets a special treatment. We just need to make the state MS would bring us into but not include it in the graph
                    misty_step_state = new_state_name
                else:
                    transition_name_to_action[action_taken_name] = action_taken
                    fsm.add_transition(action_taken_name, previous_state_name, new_state_name)
            for fa in fas:
                exported_resources = combatant.export_resources()
                use_resources(combatant, fa, battle_map)
                dfs(new_state_name, fa)
                combatant.load_resources(exported_resources)
        else:
            if "Misty Step" in action_taken_name:
                # Misty Step gets a special treatment. We just need to make the state MS would bring us into but not include it in the graph
                misty_step_state = state_footprint_to_state_name[state_footprint]
                return  # No need to explore further with Misty Step
            transition_name_to_action[action_taken_name] = action_taken
            fsm.add_transition(action_taken_name, previous_state_name, state_footprint_to_state_name[state_footprint])

    dfs('0')
    return fsm, transition_name_to_action, misty_step_state
