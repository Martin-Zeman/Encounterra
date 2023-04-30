from statemachine import State, StateMachine
from simulator.feasibility import get_feasible_factories
from simulator.resources import use_resources
from simulator.utils.state_machine_template import StateMachineTemplate


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

    # Optimization: the output of create_all doesn't change, only which factories are feasible changes => we can pre-compute them
    fafs = get_all_feasible_action_factories(combatant, battle_map)
    af_to_a = {faf: faf[1].create_all(battle_map) for faf in fafs}

    def dfs(previous_state_name, action_taken=None):
        """
        Internal function which recursively builds the action FSM in a DFS manner
        """
        nonlocal misty_step_state
        fafs = get_all_feasible_action_factories(combatant, battle_map)
        # fas = {tuple(af_to_a[faf]) for faf in fafs}
        fas = {a for faf in fafs for a in af_to_a[faf]}
        # fas = {fa for sublist in fas for fa in fafs}  # flatten the fas from a list of lists into a single list
        # A state is fully defined by all the possible (bonus) actions the combatant may take in it
        state_footprint = actions_to_set(fas)
        action_taken_name = str(action_taken)
        if not state_footprint:
            # No more actions -> connect to the nop state
            if "Misty Step" not in action_taken_name:
                transition_name_to_action[action_taken_name] = action_taken  # TODO This can be taken out of the if else
                fsm.add_transition(action_taken_name, previous_state_name, 'nop')
        elif state_footprint not in visited:
            # State not yet discovered, create a new state, remember the footprint and add transitions
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
            # State already exists, just hook up the transition
            if "Misty Step" in action_taken_name:
                # Misty Step gets a special treatment. We just need to make the state MS would bring us into but not include it in the graph
                misty_step_state = state_footprint_to_state_name[state_footprint]
                return  # No need to explore further with Misty Step
            transition_name_to_action[action_taken_name] = action_taken
            fsm.add_transition(action_taken_name, previous_state_name, state_footprint_to_state_name[state_footprint])

    dfs('0')
    return fsm, transition_name_to_action, misty_step_state
