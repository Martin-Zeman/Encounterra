import copy
import itertools
import re
import sys
import time

import numpy as np
from toposort import toposort_flatten

from simulator.actions.action_fsms import generate_action_fsm
from simulator.actions.actoid import ActoidFlags
from simulator.threat import accumulate_threat_along_path, get_aoe_and_aoo_threat_for_increment


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
    the sake of efficiency since it needs to be determined in the preceding step already to prevent expanding on Misty Step.
    :param dag: the DAG on which we operate
    :return: tuple of (post_misty_step_actions, added_misty_step_coord_states, post_dodge_actions, post_disengage_actions)
    """
    post_misty_step_actions = dag.get_available_transitions_in_state(misty_step_state)
    dag.trigger("Dodge of " + str(combatant))
    post_dodge_actions = dag.get_available_transitions()
    dag.reset()
    dag.trigger("Disengage of " + str(combatant))
    post_disengage_actions = dag.get_available_transitions()
    dag.reset()
    return post_misty_step_actions, post_dodge_actions, post_disengage_actions

def build_special_treatment_part_of_dag(action_to_eligible_coords, dag, post_actions, added_states, action_name):
    """
    A helper function which builds the Dodge and Disengage parts of the DAG
    :param action_to_eligible_coords: mapping from action names to their eligible coordinates
    :param dag: the DAG which we're building
    :param post_actions: post Dodge/Disengage eligible actions
    :param added_states: set of already existing states to avoid adding them multiple times
    :param action_name: Dodge or Disengage
    :return: the dag
    """
    # TODO Consider merging Dodged and Disengaged into one state
    # a prefix to make the newly pre-pended coord state unique
    dag.remove_transition(action_name, "0")
    action_type = action_name.split()[0]
    coord_state_prefix = action_type[0:2].lower() + "_"  # di_ or do_
    new_source_state = action_type + "d"  # Dodged or Disengaged
    if new_source_state not in added_states:
        added_states.add(new_source_state)
        dag.add_state(new_source_state)
        dag.add_transition(action_name, "0", new_source_state)

    for post_action in post_actions:
        for coord in action_to_eligible_coords[post_action]:
            new_state_name = coord_state_prefix + str(coord)  # Needs to be made unique from the other coord states
            if new_state_name not in added_states:
                added_states.add(new_state_name)
                dag.add_state(new_state_name)
                move_transition_name = "m_" + str(coord)
                dag.add_transition(move_transition_name, new_source_state, new_state_name) # will be added multiple times, but it's ok
            dag.add_transition(post_action, new_state_name, "nop")

def build_action_dag(combatant, battle_map, action_fsm, transition_name_to_action, shortest_paths, misty_step_state):
    """
    Builds action DAG for a combatant given the combatant's action_fsm. It determines eligible coords for each
    action. Then the coords are pre-pended into the action_fsm to form the final DAG. However, Misty Step, Dodge and
    Disengage require special treatment. Misty Step generates a special form of movement which is added as a transition
    to all post-Misty-Step states. Dodge and Disengage always make sense to be taken before any movement, therefore
    in their case coords are also pre-pended to their follow-up actions.
    :param combatant: the combatant for whom the DAG is modeled
    :param battle_map:
    :param action_fsm: finite state machine representing all possible actions for combatant
    :param transition_name_to_action: dict mapping action names -> actions
    :param shortest_paths: the shortest paths to all squares (result of Dijkstra)
    :param misty_step_state: name of the state into which taking the Misty Step bonus action would take us
    :return: dict which maps threat -> (start_index, end_index) and a mapping from state name -> coord
    """
    # TODO: Look into caching!!!
    dag = copy.deepcopy(action_fsm)

    post_misty_step_actions, post_dodge_actions, post_disengage_actions = get_data_for_special_treatment_actions(combatant, misty_step_state, dag)
    added_states = set()  # tracks which states have already been added

    # Get eligible coords for all actions
    transition_names = action_fsm.get_available_transitions()
    dodge_name = "Dodge of " + str(combatant)
    disengage_name = "Disengage of " + str(combatant)
    transition_names.remove(dodge_name)
    transition_names.remove(disengage_name)
    action_to_eligible_coords = {tn: transition_name_to_action[tn].get_eligible_coords(battle_map, shortest_paths) for tn in transition_names}

    coords_to_states = dict()
    for action_name, coords in action_to_eligible_coords.items():
        for coord in coords:
            for transitions in action_fsm.events[action_name].transitions.values():  # Iterate over the original to avoid deleting from the one being iterated over
                for transition in [t for t in transitions if t.source == "0"]:
                    new_state_name = str(coord)
                    if new_state_name not in added_states:
                        added_states.add(new_state_name)
                        dag.add_state(new_state_name)
                    coords_to_states[coord] = new_state_name  # TODO what is this good for? doesn't it get overwritten?
                    move_transition_name = "m_" + new_state_name
                    dag.add_transition(move_transition_name, transition.source, new_state_name) # will be added multiple times, but it's ok
                    dag.add_transition(action_name, new_state_name, transition.dest)
                    dag.remove_transition(action_name, transition.source)  # Remove the original

                    # Make a special graph section to model misty step. The ms_ transition implies the possibility of Misty Step included in the movement
                    if action_name in post_misty_step_actions:
                        new_state_name = "ms_" + str(coord)
                        if new_state_name not in added_states:
                            added_states.add(new_state_name)
                            dag.add_state(new_state_name)
                        dag.add_transition(new_state_name, "0", new_state_name)  # transition name is the same as state name
                        dag.add_transition(action_name, new_state_name, "nop")

    build_special_treatment_part_of_dag(action_to_eligible_coords, dag, post_dodge_actions, added_states, dodge_name)
    build_special_treatment_part_of_dag(action_to_eligible_coords, dag, post_disengage_actions, added_states, disengage_name)

    return dag, coords_to_states


def longest_path(combatant, battle_map, dag, sorted_states, transition_name_to_action, distances, shortest_paths):
    """
    Finds the longest path in the DAG which represents the movement and actions with the highest calculated threat.
    :param combatant: the combatant for whom the DAG is modeled
    :param battle_map:
    :param dag: finite state machine representing all possible actions for combatant
    :param sorted_states: topologically sorted states of the DAG
    :param transition_name_to_action: dict mapping action names -> actions
    :param distances: potentially already computed distances to all coords
    :param shortest_paths: potentially already computed shortest paths to all coords
    :return: the longest path in the DAG as per the threat along its edges and nodes
    """
    effect_to_coords = {e: e.get_affected_coords(battle_map) for e in battle_map.effect_tracker.get_aoe_effects()}
    MINUS_INF = -sys.maxsize - 1
    threat = dict.fromkeys(sorted_states, MINUS_INF)
    sorted_states.pop()  # Get rid of the nop state
    threat['0'] = 0
    pattern = r'([msdio]+)_\((\d+), (\d+)\)'
    for idx, state in enumerate(sorted_states):

        for transition_name, target_state in dag.forward_transitions[state]:
            try:
                threat_acc = transition_name_to_action[transition_name].calculate_threat(combatant, battle_map) + (threat[state] if threat[state] > MINUS_INF else 0)
            except KeyError:
                movement_type, x, y = re.search(pattern, transition_name).groups()
                path = battle_map.get_path_to_coord(combatant, np.array([int(x), int(y)]), distances, shortest_paths, True)
                # TODO handle misty step
                threat_acc = accumulate_threat_along_path(battle_map, path, combatant, effect_to_coords, disengaged=True if movement_type == 'di' else False)
            if threat_acc > threat[target_state]:
                threat[target_state] = threat_acc
    return threat


def select_best_action(combatant, battle_map):
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    fsm, transition_name_to_action, misty_step_state = generate_action_fsm(combatant, battle_map)
    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(combatant)
    dag, _ = build_action_dag(combatant, battle_map, fsm, transition_name_to_action, shortest_paths, misty_step_state)
    sorted_states = toposort_flatten(dag.dependencies)
    longest_pth = longest_path(combatant, battle_map, dag, sorted_states, transition_name_to_action, distances, shortest_paths)
    return dag
