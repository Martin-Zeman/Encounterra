import copy
import itertools
import logging
import re
import sys
import time

import numpy as np
from toposort import toposort_flatten

from simulator.action_types import Movement
from simulator.actions.action_fsms import generate_action_fsm
from simulator.actions.actoid import ActoidFlags
from simulator.actions.movement import MovementGenerator
from simulator.battle_map import convert_path_to_increments
from simulator.misc import reconstruct_path_through_dag
from simulator.spells.misty_step import MistyStepFactory
from simulator.threat import accumulate_threat_along_path, get_aoe_and_aoo_threat_for_increment, \
    calc_threat_for_path_with_misty_step

logger = logging.getLogger(__name__)

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
                move_transition_name = coord_state_prefix + str(coord)
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
            transitions = [t[0] for t in action_fsm.events[action_name].transitions.values() if t[0].source == "0"]
            assert len(transitions) == 1
            for transition in transitions:  # Iterate over the original to avoid deleting from the one being iterated over
                new_state_name = str(coord)
                if new_state_name not in added_states:
                    added_states.add(new_state_name)
                    dag.add_state(new_state_name)
                coords_to_states[coord] = new_state_name  # TODO what is this good for? doesn't it get overwritten?
                move_transition_name = "m_" + new_state_name
                dag.add_transition(move_transition_name, transition.source, new_state_name) # will be added multiple times, but it's ok
                dag.add_transition(action_name, new_state_name, transition.dest)

                # Make a special graph section to model misty step. The ms_ transition implies the possibility of Misty Step included in the movement (not a direct jump to the coord)
                if action_name in post_misty_step_actions:
                    new_state_name = "ms_" + str(coord)
                    if new_state_name not in added_states:
                        added_states.add(new_state_name)
                        dag.add_state(new_state_name)
                    dag.add_transition(new_state_name, "0", new_state_name)  # transition name is the same as state name
                    dag.add_transition(action_name, new_state_name, "nop")
        dag.remove_transition(action_name, transition.source)  # Remove the original

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
    :param distances: potentially already pre-computed distances to all coords
    :param shortest_paths: potentially already pre-computed shortest paths to all coords
    :return: the longest path in the DAG as per the threat along its edges and nodes
    """
    effect_to_coords = {e: e.get_affected_coords(battle_map) for e in battle_map.effect_tracker.get_aoe_effects()}
    MINUS_INF = -sys.maxsize - 1
    threat = dict.fromkeys(sorted_states, MINUS_INF)
    sorted_states.pop()  # Get rid of the nop state
    threat['0'] = 0
    max_threat_backwards_transition = {'0': None}
    max_threat = MINUS_INF
    pattern = r'([msdio]+)_\((\d+), (\d+)\)'
    transition_name_to_ms_path = dict()

    # Optimization: calculate_threat is cached, so we need to clear the cache before the computation
    for action in transition_name_to_action.values():
        action.clear_cache()

    for state in sorted_states:
        for transition_name, target_state in dag.forward_transitions[state]:

            try:
                # Is it a transition which represents a (bonus) action?
                threat_acc = transition_name_to_action[transition_name].calculate_threat(combatant, battle_map) + (threat[state] if threat[state] > MINUS_INF else 0)
            except KeyError:
                # or different kind which represents some type of movement
                movement_type, x, y = re.search(pattern, transition_name).groups()
                path = battle_map.get_path_to_coord(combatant, np.array([int(x), int(y)]), distances, shortest_paths, True)
                match movement_type:
                    case "m":
                        threat_acc = accumulate_threat_along_path(battle_map, path, combatant, effect_to_coords)
                    case "di":
                        threat_acc = accumulate_threat_along_path(battle_map, path, combatant, effect_to_coords, disengaged=True)
                    case "do":
                        threat_acc = accumulate_threat_along_path(battle_map, path, combatant, effect_to_coords, dodged=True)
                    case "ms":
                        threat_acc, misty_step_path = calc_threat_for_path_with_misty_step(battle_map, path, combatant, effect_to_coords)
                        transition_name_to_ms_path[transition_name] = misty_step_path
                    case _:
                        logger.error(f"Unknown movement type {movement_type}")
                        threat_acc = accumulate_threat_along_path(battle_map, path, combatant, effect_to_coords)
            if threat_acc > threat[target_state]:
                threat[target_state] = threat_acc
                max_threat_backwards_transition[target_state] = (transition_name, state)
                if threat_acc > max_threat:
                    max_threat = threat_acc

    # Let's go backwards to reconstruct the longest path
    return reconstruct_path_through_dag('nop', '0', max_threat_backwards_transition), transition_name_to_ms_path


def decode_ms_path_to_actions(combatant, ms_path, actions, ms_pattern, ms_factory):
    """
    A helper function which decodes an action which represents movement with the possibility of including Misty Step into a sequence of
    actions which look like: regular movement (optional), Misty Step, regular movement (optional)
    :param combatant: the combatant for whom the actions are translated
    :param ms_path: name of the current action to be decoded
    :param actions: the list of actions to which we add the resulting sequence
    :param ms_pattern: Optimization to avoid reallocation: search regex to extract coordinates from action names
    :param ms_factory: Optimization to avoid reallocation: Misty Step factory instance
    :return: None but actions shall be modified
    """
    before_ms_idx = None
    ms_idx = None
    for i, element in enumerate(ms_path):
        if element.startswith('m_'):
            before_ms_idx = i
        elif element.startswith('ms_'):
            ms_idx = i
            break
    after_ms_idx = (len(ms_path) - 1) if ms_idx != (len(ms_path) - 1) else None
    if before_ms_idx:
        before_path = []
        for i in range(0, before_ms_idx + 1):
            x, y = re.search(ms_pattern, ms_path[before_ms_idx]).groups()
            before_path.append(np.array([int(x), int(y)]))
        before_path = convert_path_to_increments(before_path)
        before_movement_generator = MovementGenerator(combatant, before_path, Movement.STANDARD).get_generator()
        actions.append(before_movement_generator)
    x, y = re.search(ms_pattern, ms_path[ms_idx]).groups()
    actions.append(ms_factory.create(np.array([int(x), int(y)])))
    if after_ms_idx:
        after_path = []
        for i in range(ms_idx + 1, after_ms_idx + 1):
            x, y = re.search(ms_pattern, ms_path[after_ms_idx]).groups()
            after_path.append(np.array([int(x), int(y)]))
        after_path = convert_path_to_increments(after_path)
        after_movement_generator = MovementGenerator(combatant, after_path, Movement.STANDARD).get_generator()
        actions.append(after_movement_generator)

def translate_longest_pth_to_actions(combatant, battle_map, distances, shortest_paths, transition_name_to_action, longest_pth, transition_name_to_ms_path):
    """
    Translates the string form of longest path back to action objects
    :param combatant: the combatant for whom the actions are translated
    :param battle_map:
    :param distances: potentially already pre-computed distances to all coords
    :param shortest_paths: potentially already pre-computed shortest paths to all coords
    :param transition_name_to_action: dictionary mapping of non-movement types to actions
    :param longest_pth: list of best actions as strings
    :param transition_name_to_ms_path: dictionary mapping of transition names to paths that may include a Misty Step (can be empty)
    :return: list of the following types: np.array, action, bonus action
    """
    pattern = r'([msdio]+)_\((\d+), (\d+)\)'
    ms_pattern = r'[msdio_]+\((\d+), (\d+)\)'
    ms_factory = MistyStepFactory(combatant)
    actions = []
    for action in longest_pth:
        try:
            actions.append(transition_name_to_action[action])
        except KeyError:
            movement_type, x, y = re.search(pattern, action).groups()
            match movement_type:
                case "m" | "do":
                    path = battle_map.get_path_to_coord(combatant,  np.array([int(x), int(y)]), distances, shortest_paths, True)
                    movement_generator = MovementGenerator(combatant, path, Movement.STANDARD).get_generator()
                    actions.append(movement_generator)
                case "di":
                    path = battle_map.get_path_to_coord(combatant, np.array([int(x), int(y)]), distances, shortest_paths, False)
                    movement_generator = MovementGenerator(combatant, path, Movement.DISENGAGE).get_generator()
                    actions.append(movement_generator)
                case "ms":
                    decode_ms_path_to_actions(combatant, transition_name_to_ms_path[action], actions, ms_pattern, ms_factory)
                case _:
                    logger.error(f"Unknown movement type {movement_type}")
    return actions


def get_best_actions(combatant, battle_map, distances, shortest_paths):
    """
    Finds chain of movement, action and bonus action with the highest (threat_out - threat_in)
    :param combatant: the combatant for whom the DAG is modeled
    :param battle_map:
    :param distances: potentially already pre-computed distances to all coords
    :param shortest_paths: potentially already pre-computed shortest paths to all coords
    :return: list of the following types: np.array, action, bonus action
    """
    # start_time = time.time()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    fsm, transition_name_to_action, misty_step_state = generate_action_fsm(combatant, battle_map)
    dag, _ = build_action_dag(combatant, battle_map, fsm, transition_name_to_action, shortest_paths, misty_step_state)
    sorted_states = toposort_flatten(dag.dependencies)
    longest_pth, transition_name_to_ms_path = longest_path(combatant, battle_map, dag, sorted_states, transition_name_to_action, distances, shortest_paths)
    # print("---get_best_actions took %s seconds ---" % (time.time() - start_time))
    return translate_longest_pth_to_actions(combatant, battle_map, distances, shortest_paths, transition_name_to_action, longest_pth, transition_name_to_ms_path)
