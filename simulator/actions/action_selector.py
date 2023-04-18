import copy
import itertools
import numpy as np

from simulator.actions.action_fsms import generate_action_fsm
from simulator.actions.actoid import ActoidFlags
from simulator.threat import accumulate_threat_along_path

def find_ranges_of_consecutive(coords_w_threats):
    """
    A helper function which returns the index ranges consecutive threat.
    :param coords_w_threats: list of tuples in the [((x1, y1), threat1), ((x2, y2), threat2)...] format
    :return: dict which maps threat -> (start_index, end_index)
    """
    res = dict()
    idx = 0
    while idx < len(coords_w_threats):
        start_pos = idx
        val = coords_w_threats[idx][1]

        while (idx < len(coords_w_threats) and coords_w_threats[idx][1] == val):
            idx += 1
        end_pos = idx - 1

        res[val] = start_pos, end_pos
    return res

def get_data_for_special_treatment_actions(combatant, misty_step_state, dag):
    """
    A helper function which takes care of the actions that requre special treatment such as Misty Step, Dodge and
    Disengage.
    :param combatant: the combatant taking the actions
    :param misty_step_state: state of the DAG after taking Misty Step action to any coord. This is handed into here for
    the sake of efficiency since it needs to be determined in the preceeding step already to prevent expanding on Misty Step.
    :param dag: the DAG on which we operate
    :return: tuple of (post_misty_step_actions, added_misty_step_coord_states, post_dodge_actions, post_disengage_actions)
    """
    post_misty_step_actions = dag.get_available_transitions_in_state(misty_step_state)
    dag.trigger("Dodge of " + str(combatant))
    post_dodge_actions = dag.get_available_transitions_in_state(dag.state)
    post_dodge_state = dag.state
    dag.reset()
    dag.trigger("Disengage of " + str(combatant))
    post_disengage_actions = dag.get_available_transitions_in_state(dag.state)
    post_disengage_state = dag.state
    dag.reset()
    return post_misty_step_actions, post_dodge_actions, post_dodge_state, post_disengage_actions, post_disengage_state

def build_special_treatment_part_of_dag(action_to_eligible_coords, action_fsm, dag, added_transitions, post_state, post_actions, coord_state_prefix):
    """
    A helper function which builds the Dodge and Disengage parts of the DAG
    :param action_to_eligible_coords: mapping from actions to their eligible coordinates
    :param action_fsm: the original action FSM based on which the DAG is built
    :param dag: the DAG which we're building
    :param added_transitions:
    :param post_state: post Dodge/Disengage state
    :param post_actions: post Dodge/Disengage eligible actions
    :param coord_state_prefix: a prefix to make the newly pre-pended coord state unique
    :return: the dag
    """
    for post_action in post_actions:
        for coords in action_to_eligible_coords[post_action]:
            for coord in coords:
                for transitions in action_fsm.events[post_action].transitions.values():  # Iterate over the original to avoid deleting from the one being iterated over
                    for transition in [t for t in transitions if t.source == post_state]:
                        new_state_name = coord_state_prefix + str(coord)  # Needs to be made unique from the other coord states
                        dag.add_state(new_state_name)
                        # coords_to_states[coord] = new_state_name  # TODO what is this good for? doesn't it get overwritten?
                        move_transition_name = "m_" + new_state_name
                        if move_transition_name not in added_transitions:  # Avoid adding the same transition multiple times
                            dag.add_transition(move_transition_name, transition.source, new_state_name)
                            added_transitions.add(move_transition_name)
                        dag.add_transition(post_action, new_state_name, transition.dest)
                        dag.remove_transition(post_action, transition.source)  # Remove the original
    return dag  # TODO do I need to return this or is it modified?

def build_action_dag(combatant, battle_map, action_fsm, transition_name_to_action, misty_step_state):
    """
    Builds action DAG for a combatant given the combatant's action_fsm. It determines eligible coords for each
    action. Then the coords are pre-pended into the action_fsm to form the final DAG. However, Misty Step, Dodge and
    Disengage require special treatment. Misty Step generated a special form of movement which is added as a transition
    to all post-Misty-Step states. Dodge and Disengage always make sense to be taken before ant movement, therefore
    in their case coords are also pre-pended to their follow-up actions.
    :param combatant: the combatant for whom the DAG is modeled
    :param battle_map:
    :param action_fsm: finite state machine representing all possible actions for combatant
    :param transition_name_to_action: dict mapping action names -> actions
    :param misty_step_state: name of the state into which taking the Misty Step bonus action would take us
    :return: dict which maps threat -> (start_index, end_index) and a mapping from state name -> coord
    """
    # TODO: Look into caching!!!
    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(combatant)
    dag = copy.deepcopy(action_fsm)

    post_misty_step_actions, post_dodge_actions, post_dodge_state, post_disengage_actions, post_disengage_state = \
        get_data_for_special_treatment_actions(combatant, misty_step_state, dag)
    added_misty_step_coord_states = set()  # thanks which misty steps states have already been created

    # get eligible coords for all actions
    transition_names = action_fsm.get_available_transitions()
    transition_actions = [transition_name_to_action[tn] for tn in transition_names]
    action_to_eligible_coords = {a: a.get_eligible_coords(battle_map, shortest_paths) for a in transition_actions}

    coords_to_states = dict()
    added_transitions = set()
    for action, coords in action_to_eligible_coords.items():
        action_name = str(action)
        if "Dodge" in action_name or "Disengage" in action_name:
            # Dodge also gets a special treatment. It always makes sense to Dodge first before movement if Dodge is used at all
            continue
        else:
            # All the other actions
            for coord in coords:
                for transitions in action_fsm.events[action_name].transitions.values():  # Iterate over the original to avoid deleting from the one being iterated over
                    for transition in [t for t in transitions if t.source == "0"]:
                        new_state_name = str(coord)
                        dag.add_state(new_state_name)
                        coords_to_states[coord] = new_state_name  # TODO what is this good for? doesn't it get overwritten?
                        move_transition_name = "m_" + new_state_name
                        if move_transition_name not in added_transitions:  # Avoid adding the same transition multiple times
                            dag.add_transition(move_transition_name, transition.source, new_state_name)
                            added_transitions.add(move_transition_name)
                        dag.add_transition(action_name, new_state_name, transition.dest)
                        dag.remove_transition(action_name, transition.source)  # Remove the original

                        # Make a special graph section to model misty step. The ms_ transition implies the possibility of Misty Step included in the movement
                        if action_name in post_misty_step_actions:
                            new_state_name = "ms_" + str(coord)
                            if new_state_name not in added_misty_step_coord_states:
                                added_misty_step_coord_states.add(new_state_name)
                                dag.add_state(new_state_name)
                            dag.add_transition(new_state_name, "0", new_state_name)  # transition name is the same as state name
                            dag.add_transition(action_name, new_state_name, "nop")

    dag = build_special_treatment_part_of_dag(action_to_eligible_coords, action_fsm, dag, added_transitions, post_dodge_state,
                                        post_dodge_actions, "do_")
    dag = build_special_treatment_part_of_dag(action_to_eligible_coords, action_fsm, dag, added_transitions,
                                              post_disengage_state,
                                              post_disengage_actions, "di_")

    return dag, coords_to_states


def select_best_action(combatant, battle_map):
    fsm, transition_name_to_action, misty_step_state = generate_action_fsm(combatant, battle_map)
    dfs, _ = build_action_dag(combatant, battle_map, fsm, transition_name_to_action, misty_step_state)
    # TODO Topological sort
    return dfs
