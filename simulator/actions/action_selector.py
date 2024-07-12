import copy
import logging
import re
import math
import sys

import numpy as np
from numba import njit

from .action_dag import replace_combatant_with_wildshape
from .actoid import ActoidFlags
from ..actions.action_constants import PRIORITY_ACTIONS, PRIORITY_BONUS_ACTIONS
from ..actions.action_types import Movement, MovementThreatType, BonusAction
from ..actions.break_grapple import BreakGrappleFactory
from ..actions.movement import MovementGenerator, GetUpFactory, MovementIncrement
from ..battle_map import convert_path_to_increments, Map, _get_hop_distance_coords
from ..misc import get_factory_of_type
from ..conditions import Conditions, needs_to_break_out_of_grapple, is_affected_by
from ..threat_interfaces import AttackThreatModifier
from ..threat_utils import accumulate_threat_along_path, calc_threat_for_path_with_misty_step, \
    get_aoe_and_aoo_threat_for_increment

logger = logging.getLogger("Encounterra")

REGEX_MOVEMENT_PATTERN = re.compile(r'([msdchio]+)_\((\d+), (\d+)\)')
REGEX_MS_MOVEMENT_PATTERN = re.compile(r'[mschdio_]+\((\d+), (\d+)\)')


def get_post_transitions_of_priority_transitions(dag, transition_name_to_action, prio_action_dict):
    """
    A helper function which gets eligible follow-up actions to priority actions of the given dict present in the DAG
    :param dag: the DAG on which we operate
    :param transition_name_to_action: dict mapping action names -> actions
    :param prio_action_dict: either PRIORITY_ACTIONS or PRIORITY_BONUS_ACTIONS
    :return: dict priority_transition_name -> list of eligible follow-up transitions
    """
    post_priority_transitions = dict()
    for transition in dag.get_available_transitions():
        if transition == 'None_0':
            break
        if transition_name_to_action[transition].factory.action_type in prio_action_dict.keys():
            post_transitions = []
            if dag.trigger(transition):
                # We filter out priority transitions even from all the post transitions
                try:
                    post_transitions = [ft for ft in dag.forward_transitions[dag.state] if ActoidFlags.IS_PRIORITY not in transition_name_to_action[ft[0]].actoid_flags]
                except KeyError:
                    pass  # For the case when the target state is nop
                dag.reset()
            post_priority_transitions[transition] = post_transitions
    return post_priority_transitions


def get_post_transitions_of_all_priority_transitions(proto_dag, transition_name_to_action):
    """
    Retrieves eligible follow-up actions for all priority actions present in the action finite state machine (FSM).

    This helper function is used to gather eligible follow-up actions for priority actions and bonus actions separately.
    It operates on the provided action finite state machine (proto_dag) and uses the mapping of action names to actions (transition_name_to_action).
    The output of this function is utilized by the `build_priority_transitions` function.

    :param proto_dag: The action finite state machine (FSM) on which the operation is performed.
    :param transition_name_to_action: A dictionary mapping action names to their corresponding actions.

    :return: A tuple of two dictionaries:
        1. A dictionary containing priority action names as keys and lists of eligible follow-up transitions as values.
        2. A dictionary containing priority bonus action names as keys and lists of eligible follow-up transitions as values.
    """
    post_priority_action_transitions = get_post_transitions_of_priority_transitions(proto_dag, transition_name_to_action, PRIORITY_ACTIONS)
    post_priority_bonus_action_transitions = get_post_transitions_of_priority_transitions(proto_dag, transition_name_to_action, PRIORITY_BONUS_ACTIONS)
    for priority_transition in post_priority_action_transitions.keys():
        for origin_state in proto_dag.states.keys():
            proto_dag.remove_transition(priority_transition, origin_state)  # Get rid of the originals, don't want to have them pre-pended with coords
    for priority_transition in post_priority_bonus_action_transitions.keys():
        for origin_state in proto_dag.states.keys():
            proto_dag.remove_transition(priority_transition, origin_state)  # Get rid of the originals, don't want to have them pre-pended with coords
    return post_priority_action_transitions, post_priority_bonus_action_transitions


def get_post_misty_step_transitions(dag, transition_name_to_action):
    dag.trigger("Misty Step to 0, 0_1")  # It's the only MS we created
    try:
        ms_post_transitions = [pt for pt in dag.forward_transitions[dag.state] if ActoidFlags.IS_PRIORITY not in transition_name_to_action[pt[0]].actoid_flags]
    except KeyError:
        ms_post_transitions = []
    dag.reset()
    dag.remove_transition("Misty Step to 0, 0_1", "0")
    return ms_post_transitions


def build_misty_step_transitions(dag, ms_post_transitions, transition_to_eligible_coords, movement_trans_to_coord_and_type):
    """
    A helper function which builds the Misty Step transitions of the DAG.
    :param dag: the DAG which we're building
    :param ms_post_transitions: dict from transition -> list of eligible follow-up transitions if the form of (transition, dest_state)
    :param transition_to_eligible_coords: mapping from action names to their eligible coordinates
    :param movement_trans_to_coord_and_type: mapping from movement transition -> coord, MovementThreatType
    :return: None but the dag is modified
    """
    eligible_transitions_to_state, coord_to_eligible_transitions = create_movement_states(dag, transition_to_eligible_coords)
    for mspt in ms_post_transitions:
        try:
            for coord in transition_to_eligible_coords[mspt[0]]:
                post_ms_state = eligible_transitions_to_state[coord_to_eligible_transitions[coord]]
                movement_transition_name = "ms_" + str(coord)
                movement_trans_to_coord_and_type[movement_transition_name] = (coord, MovementThreatType.MISTY_STEPPED)
                dag.add_transition(movement_transition_name, "0", post_ms_state)
                dag.add_transition(mspt[0], post_ms_state, mspt[1])
        except KeyError:
            pass  # Happens e.g. for melee weapons when out of range


def build_priority_transitions(dag, post_priority_transitions, transition_to_eligible_coords, movement_trans_to_coord_and_type, transition_name_to_action, prio_action_dict):
    """
    A helper function which builds the priority part of the DAG such as Dodge or Disengage.
    :param dag: the DAG which we're building
    :param post_priority_transitions: dict from transition -> list of eligible follow-up transitions if the form of (transition, dest_state)
    :param transition_to_eligible_coords: mapping from action names to their eligible coordinates
    :param movement_trans_to_coord_and_type: mapping from movement transition -> coord, MovementThreatType
    :param transition_name_to_action: dict mapping action names -> actions
    :param prio_action_dict: either PRIORITY_ACTIONS or PRIORITY_BONUS_ACTIONS
    :return: None but the dag is modified
    """
    eligible_transitions_to_state, coord_to_eligible_transitions = create_movement_states(dag, transition_to_eligible_coords)

    newly_added_states = []
    for transition, post_transitions in post_priority_transitions.items():
        if not post_transitions:  # If there are no follow-up actions possible, connect directly to nop and return
            dag.add_transition(transition, "0", "nop")
            continue
        action_type = transition.split()[0]
        new_prio_state = action_type + "d"  # e.g. Dodge of FooBar -> Dodged
        prefix = prio_action_dict[transition_name_to_action[transition].factory.action_type][0]
        dag.add_new_state(new_prio_state)
        newly_added_states.append(new_prio_state)
        dag.add_transition(transition, "0", new_prio_state)
        for post_transition in post_transitions:
            try:
                for coord in transition_to_eligible_coords[post_transition[0]]:
                    post_pt_state = eligible_transitions_to_state[coord_to_eligible_transitions[coord]]
                    movement_transition_name = prefix + str(coord)
                    movement_trans_to_coord_and_type[movement_transition_name] = (coord, prio_action_dict[transition_name_to_action[transition].factory.action_type][1])
                    dag.add_transition(movement_transition_name, new_prio_state, post_pt_state)  # Will be added multiple times, but it's ok
                    dag.add_transition(post_transition[0], post_pt_state, post_transition[1])
            except KeyError:
                pass  # Some may not be available for the secondary plan

    # Some states may have been left unconnected due to their follow-up actions not having eligible coords -> connect them to nop
    for newly_added_state in newly_added_states:  # TODO is this still needed?
        if newly_added_state not in dag.forward_transitions.keys():
            dag.add_transition("dummy", newly_added_state, "nop")


def decode_ms_path_to_actions(combatant, initial_coord, ms_path, actions, ms_factory):
    """
    A helper function which decodes an action which represents movement with the possibility of including Misty Step into a sequence of
    actions which look like: regular movement (optional), Misty Step, regular movement (optional)
    :param combatant: the combatant for whom the actions are translated
    :param initial_coord: the initial coordinate of the combatant
    :param ms_path: name of the current action to be decoded
    :param actions: the list of actions to which we add the resulting sequence
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
    if before_ms_idx is not None:
        before_path = [initial_coord]
        for i in range(0, before_ms_idx + 1):
            x, y = REGEX_MS_MOVEMENT_PATTERN.search(ms_path[i]).groups()
            before_path.append(np.array([int(x), int(y)]))
        before_path = convert_path_to_increments(before_path)
        actions.extend(list(MovementGenerator(combatant, before_path, Movement.STANDARD).get_generator()))  # Unpack the movement generator
    try:
        x, y = REGEX_MS_MOVEMENT_PATTERN.search(ms_path[ms_idx]).groups()
    except TypeError:
        print("FIXME")  # the ms_idx was None as some point
    actions.append(ms_factory.create(np.array([int(x), int(y)])))
    if after_ms_idx is not None:
        after_path = [actions[-1].coord]  # use the Misty Step target coord as the initial one
        for i in range(ms_idx + 1, after_ms_idx + 1):
            x, y = REGEX_MS_MOVEMENT_PATTERN.search(ms_path[i]).groups()
            after_path.append(np.array([int(x), int(y)]))
        after_path = convert_path_to_increments(after_path)
        actions.extend(list(MovementGenerator(combatant, after_path, Movement.STANDARD).get_generator()))  # Unpack the movement generator


def translate_sequence_to_actions(combatant, distances, shortest_paths, transition_name_to_action, movement_trans_to_coord_and_type, sequence, transition_name_to_ms_path):
    """
    Translates the string form of the longest path back to action objects
    :param combatant: the combatant for whom the actions are translated
    :param distances: potentially already pre-computed distances to all coords
    :param shortest_paths: potentially already pre-computed shortest paths to all coords
    :param transition_name_to_action: dictionary mapping of non-movement types to actions
    :param movement_trans_to_coord_and_type: mapping from movement transition -> coord, MovementThreatType
    :param sequence: list of best actions as strings
    :param transition_name_to_ms_path: dictionary mapping of transition names to paths that may include a Misty Step (can be empty)
    :return: list of the following types: np.array, action, bonus action
    """
    actions = []
    battle_map = Map.get()
    for transition in sequence:
        if transition == "dummy":
            continue
        try:
            actions.append(transition_name_to_action[transition])
        except KeyError:
            coord, movement_type = movement_trans_to_coord_and_type[transition]
            match movement_type:
                case MovementThreatType.STANDARD | MovementThreatType.DODGED:
                    path = battle_map.get_path_to_coord(combatant,  np.array(coord), distances, shortest_paths, True)
                    movement_generator = MovementGenerator(combatant, path, Movement.STANDARD).get_generator()
                    actions.extend(list(movement_generator))  # Unpack the movement generator
                case MovementThreatType.DISENGAGED:
                    path = battle_map.get_path_to_coord(combatant, np.array(coord), distances, shortest_paths, False)
                    movement_generator = MovementGenerator(combatant, path, Movement.DISENGAGED).get_generator()
                    actions.extend(list(movement_generator))  # Unpack the movement generator
                case MovementThreatType.MISTY_STEPPED:
                    ms_factory = get_factory_of_type(combatant.bonus_action_factories, BonusAction.MISTY_STEP)
                    decode_ms_path_to_actions(combatant, battle_map.get_combatant_position(combatant).get()[0], transition_name_to_ms_path[transition], actions, ms_factory)
                    # TODO also unpack actions
                case _:
                    logger.error(f"Unknown movement type {movement_type}")
    return actions


def get_dist_to_action_sequence_coord(sequence, distances):
    """
    Extracts the movement part of an action plan and returns the distance to its coordinate
    :param sequence: list of best actions as strings
    :param distances: already pre-computed distances to all coords
    :return: list of movement increments or None
    """
    for transition in sequence:
        if transition == "dummy":
            continue
        match = REGEX_MOVEMENT_PATTERN.search(transition)
        if match:
            _, x, y = match.groups()
            map_size = Map.get().size
            return distances[int(x) * map_size + int(y)]
    return 0  # This should not happen


def create_movement_states(dag, transition_to_eligible_coords):
    """
    Movement states that share eligible transitions can be merged. Create new states for them.
    :param dag: the dag which the states are to be added
    :param transition_to_eligible_coords:
    :param transition_name_to_action: used to filter out priority actions
    :return: dict mapping eligible transitions -> newly created state, dict mapping coord -> eligible transitions
    """
    coord_to_eligible_transitions = dict()
    for transition_name, coords in transition_to_eligible_coords.items():
        for coord in coords:
            try:
                coord_to_eligible_transitions[coord].add(transition_name)
            except KeyError:
                coord_to_eligible_transitions[coord] = {transition_name}
    coord_to_eligible_transitions = {c: frozenset(a) for c, a in coord_to_eligible_transitions.items()}
    eligible_transitions_to_state = {a: dag.get_next_state_name() for a in coord_to_eligible_transitions.values()}
    for state_name in eligible_transitions_to_state.values():
        dag.add_new_state(state_name)
    return eligible_transitions_to_state, coord_to_eligible_transitions


def build_action_dag(combatant, proto_dag, transition_name_to_action, distances, shortest_paths):
    """
    Builds action DAG for a combatant given the combatant's proto_dag. It determines eligible coords for each
    action. Then the coords are pre-pended into the proto_dag to form the final DAG. However, Misty Step, Dodge and
    Disengage require special treatment. Misty Step generates a special form of movement which is added as a transition
    to all post-Misty-Step states. Dodge and Disengage always make sense to be taken before any movement, therefore
    in their case coords are also pre-pended to their follow-up actions.
    :param combatant: the combatant for whom the DAG is modeled
    :param proto_dag: DAG (finite state machine) representing all possible actions for combatant. Doesn't model movement.
    :param transition_name_to_action: dict mapping action names -> actions
    :param distances: the distances to all squares (result of Dijkstra)
    :param shortest_paths: the shortest paths to all squares (result of Dijkstra)
    :return: Tuple of:
        - dict which maps threat -> (start_index, end_index) and a mapping from state name -> coord
        - dict which maps a movement transition -> to target coord
    """
    battle_map = Map.get()
    battle_map.calc_visibility_dict_for_all_coords(combatant, shortest_paths)
    # Optimization: calculate_threat is cached, so we need to clear the cache before the computation
    for action in transition_name_to_action.values():
        action.clear_cache()

    post_priority_action_transitions, post_priority_bonus_action_transitions = get_post_transitions_of_all_priority_transitions(proto_dag, transition_name_to_action)

    ms_transition_to_eligible_coords = None
    post_misty_step_transitions = None
    transition_names = proto_dag.get_all_transitions()
    if 'Misty Step to 0, 0_1' in transition_names:
        post_misty_step_transitions = get_post_misty_step_transitions(proto_dag, transition_name_to_action)

    dag = copy.deepcopy(proto_dag)

    a_pt_transition_to_eligible_coords = {tn[0]: transition_name_to_action[tn[0]].get_eligible_coords(distances, shortest_paths) for pre in post_priority_action_transitions.values() for tn in pre}
    a_pt_transition_to_eligible_coords = {tn: coords for tn, coords in a_pt_transition_to_eligible_coords.items() if coords}
    ba_pt_transition_to_eligible_coords = {tn[0]: transition_name_to_action[tn[0]].get_eligible_coords(distances, shortest_paths) for pre in post_priority_bonus_action_transitions.values() for tn in pre}
    ba_pt_transition_to_eligible_coords = {tn: coords for tn, coords in ba_pt_transition_to_eligible_coords.items() if coords}
    if post_misty_step_transitions:
        ms_transition_to_eligible_coords = {tn[0]: transition_name_to_action[tn[0]].get_eligible_coords(distances, shortest_paths) for tn in post_misty_step_transitions}
        ms_transition_to_eligible_coords = {tn: coords for tn, coords in ms_transition_to_eligible_coords.items() if coords}


    transition_names = list(filter(lambda t: t != "dummy", transition_names))
    if not transition_names or transition_names[0] == 'None_0':
        return None, None, None

    transition_to_eligible_coords = dict()
    for tn in transition_names:
        # try:
        action = transition_name_to_action[tn]
        if action.factory.combatant.get_original_form().get_current_form() is not action.factory.combatant:
            # The actions of wildshaped forms need to be on the map in order to determine feasible coordinates
            with replace_combatant_with_wildshape(action.factory.combatant, action.factory.combatant.get_original_form()):
                transition_to_eligible_coords[tn] = transition_name_to_action[tn].get_eligible_coords(distances, shortest_paths)
        else:
            transition_to_eligible_coords[tn] = transition_name_to_action[tn].get_eligible_coords(distances, shortest_paths)
        # except AttributeError:
        #     continue  # Happens for wildshaped actions, will be dealt with separately since this is a chicken an egg problem. We need to be put to the wildshape's eligible coord first.
    transition_to_eligible_coords = {tn: coords for tn, coords in transition_to_eligible_coords.items() if coords}

    for transition_name in transition_names:  # Filter out actions which don't have any eligible coords
        try:
            if not transition_to_eligible_coords[transition_name]:
                dag.remove_transition(transition_name, '0')
        except KeyError:
            dag.remove_transition(transition_name, '0')  # Happens where the combatant's out of movement

    eligible_transitions_to_state, coord_to_eligible_transitions = create_movement_states(dag, transition_to_eligible_coords)

    movement_transition_to_coord_and_type = dict()
    for transition_name, coords in transition_to_eligible_coords.items():
        if transition_name.startswith("Misty Step"):
            continue
        transitions = [t[0] for t in proto_dag.events[transition_name].transitions.values() if t[0].source == "0"]  # Iterate over the original to avoid deleting from the one being iterated over
        if not transitions:
            continue  # Happens for all actions of source != 0
        transition = transitions[0]
        for coord in coords:
            movement_state_name = eligible_transitions_to_state[coord_to_eligible_transitions[coord]]
            movement_transition_name = "m_" + str(coord)
            movement_transition_to_coord_and_type[movement_transition_name] = (coord, MovementThreatType.STANDARD)
            dag.add_transition(movement_transition_name, "0", movement_state_name)
            dag.add_transition(transition_name, movement_state_name, transition.dest)
        dag.remove_transition(transition_name, "0")  # Remove the original

    if post_misty_step_transitions:
        build_misty_step_transitions(dag, post_misty_step_transitions, ms_transition_to_eligible_coords, movement_transition_to_coord_and_type)
    build_priority_transitions(dag, post_priority_action_transitions, a_pt_transition_to_eligible_coords, movement_transition_to_coord_and_type, transition_name_to_action, PRIORITY_ACTIONS)
    build_priority_transitions(dag, post_priority_bonus_action_transitions, ba_pt_transition_to_eligible_coords, movement_transition_to_coord_and_type, transition_name_to_action, PRIORITY_BONUS_ACTIONS)
    return dag, movement_transition_to_coord_and_type, transition_to_eligible_coords


# def get_nearest_and_minimize(sequences, sorted_sequences, sequence_to_threat, sequence_idx_to_transition_step_threat, distances):
def get_nearest_and_minimize(sequences, sorted_sequences, sequence_to_threat, distances, sequence_idx_to_transition_step_threat, transition_name_to_action):
    """
    Filters, minimizes, and sorts action sequences to find the one with maximum threat while maintaining minimum distance.

    This function takes a list of action sequences and performs the following steps:
    1. Filter: It filters the sequences to only include those with the maximum threat (if there are multiple sequences with the same maximum
     threat).
    2. Minimize: It minimizes the length of each sequence while ensuring the total threat remains the same. This step discards actions that
    do not add any additional threat.
    3. Sort: It sorts the sequences by their length in ascending order.

    The function is designed to be used in the context of the `get_movement_and_threat_for_next_turn` function. It helps in selecting the most optimal
    action sequence among sets of actions with equal threat but different orders.

    :param sequences: List of all action sequences in no particular order.
    :param sorted_sequences: Indices of sequences sorted by threat in descending order.
    :param sequence_to_threat: A dictionary mapping sequence index to its threat value.
    :param distances: A pre-computed dictionary of distances to all coordinates.
    :param sequence_idx_to_transition_step_threat: A dictionary of dictionaries.  Maps for each sequence index to a dict
    of individual transition indices -> threat contributions.
    :param transition_name_to_action: dict mapping action names -> actions
    :return: A tuple of the action sequence with maximum threat and more distant coordinate requirement after
    minimization and the maximum threat.
    """
    if not sorted_sequences:
        return None, 0
    max_threat = sum(sequence_to_threat[sorted_sequences[0]])
    idx = 0
    while idx < len(sorted_sequences) and sum(sequence_to_threat[sorted_sequences[idx]]) == max_threat:
        idx += 1
    sorted_sequences = sorted_sequences[:idx]
    min_dist = sys.maxsize
    for idx in sorted_sequences:
        dist = get_dist_to_action_sequence_coord(sequences[idx], distances)
        if dist < min_dist:
            min_dist = dist
    sorted_sequences = [idx for idx in sorted_sequences if get_dist_to_action_sequence_coord(sequences[idx], distances) == min_dist]

    # Filter out transitions which contribute nothing
    for idx in sorted_sequences:
        new_sequence = []
        for t_idx, elem in enumerate(sequences[idx]):
            try:
                if sequence_idx_to_transition_step_threat[idx][t_idx] > 0 or ActoidFlags.IS_PRIORITY in transition_name_to_action[sequences[idx][t_idx]].actoid_flags:
                    new_sequence.append(elem)
            except KeyError:
                new_sequence.append(elem)
        sequences[idx] = new_sequence

    sorted_sequences.sort(key=lambda idx: len(sequences[idx]))
    best_sequence = sequences[sorted_sequences[0]]
    best_out_threat = sequence_to_threat[sorted_sequences[0]]  # We're only interested in the out threat
    if len(best_sequence) == 1:
        return None, [0, 0]  # This means the only non-movement action was a NOP and there's only movement left
    return best_sequence, best_out_threat


@njit
def _dfs(dag_forward: np.ndarray, current_state: int, max_sequence_length: int):
    sequences = []
    empty_sequence = np.zeros(max_sequence_length, dtype=np.int32)
    sequence_length = 0
    stack = [(current_state, sequence_length, empty_sequence.copy())]

    while stack:
        state, sequence_length, current_sequence = stack.pop()

        if state == 1:  # 'nop' state
            sequences.append(current_sequence[:sequence_length].copy())
            continue

        for i in range(dag_forward.shape[1]):
            transition, next_state = dag_forward[state, i]
            if transition == -1:
                break
            if sequence_length < max_sequence_length:
                new_sequence = current_sequence.copy()
                new_sequence[sequence_length] = transition
                stack.append((next_state, sequence_length + 1, new_sequence))

    return sequences


def prune_sequences(sequences, transition_name_to_action, index_to_transition, transition_to_simplified):
    sequence_sets = set()
    pruned_sequences = []
    for sequence in sequences:
        current_sequence_set = frozenset((transition_to_simplified[tx_idx] for tx_idx in sequence))  # Removes the trailing level designator
        if current_sequence_set not in sequence_sets:
            pruned_sequences.append(sequence)
            sequence_sets.add(current_sequence_set)
        else:
            for tx in sequence:
                try:
                    if ActoidFlags.IS_ATTACK_MODIFIER in transition_name_to_action[index_to_transition[tx]].actoid_flags:
                        pruned_sequences.append(sequence)
                        break
                except KeyError:
                    pass
    return pruned_sequences


def create_coord_to_sequence_mapping(sequences, movement_transition_to_coord_and_type):
    coord_to_sequence_ids = dict()  # Maps coord (and movement type) to all sequences which end in that coord
    for idx, sequence in enumerate(sequences):
        coord = None
        for tx in sequence:
            try:
                coord = movement_transition_to_coord_and_type[tx]
                break
            except KeyError:
                pass  # Skipping transitions that aren't movement
        if coord is not None:
            try:
                coord_to_sequence_ids[coord].append(idx)
            except KeyError:
                coord_to_sequence_ids[coord] = [idx]
    return coord_to_sequence_ids


def find_best_sequence(combatant, dag, transition_name_to_action, transition_to_eligible_coords, movement_transition_to_coord_and_type, distances, shortest_paths, infeasibility_multiplier=0.5):
    """
    Finds the path through the DAG which represents the movement and actions with the highest calculated threat.
    We're taking advantage of the fact that as a result of the DFS traversal the coordinates in generated sequences are block-wise.
    Therefore, we can process the sequences by these coord-wise blocks and only call as_if_combatant_position once per block.
    To achieve this, coord_to_sequence_ids needs mapping between a target coordinate to all sequence ids which contain it, needs to be
    built.
    :param combatant: the combatant for whom the DAG is modeled
    :param dag: finite state machine representing all possible actions for combatant
    :param transition_name_to_action: dict mapping non-movement transition names -> action objects
    :param transition_to_eligible_coords: dict mapping non-movement transition names -> their eligible coordinates
    :param movement_transition_to_coord_and_type: dict mapping movement transition names -> target coord, MovementThreatType
    :param distances: potentially already pre-computed distances to all coords
    :param shortest_paths: potentially already pre-computed shortest paths to all coords
    :return: the longest path in the DAG as per the threat along its edges and nodes and a mapping of transitions names
    to special Misty Step paths
    """
    battle_map = Map.get()
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    transition_name_to_ms_path = dict()
    sequence_to_threat = dict()  # Overall threat score of a sequence: sequence idx -> [movement threat, action threat]
    sequence_idx_to_transition_step_threat = dict()
    current_coords = battle_map.get_combatant_position(combatant).get()[0]
    try:
        del movement_transition_to_coord_and_type[f"ms_({current_coords[0]}, {current_coords[1]})"]  # Removing Misty Step to current coordinate
    except KeyError:
        pass

    dag_forward, num_states, index_to_state, index_to_transition, transition_to_simplified = dag.get_numba_compatible_data()
    max_sequence_length = num_states * 2  # This is a rough estimate
    all_sequences = _dfs(dag_forward, 0, max_sequence_length)
    pruned_sequences = prune_sequences(all_sequences, transition_name_to_action, index_to_transition, transition_to_simplified)
    sequences = []
    for arr in pruned_sequences:
        sequence = [index_to_transition.get(item, f"Unknown_{item}") for item in arr]
        sequences.append(sequence)
    coord_to_sequence_ids = create_coord_to_sequence_mapping(sequences, movement_transition_to_coord_and_type)

    accumulate_threat_along_path.cache_clear()
    get_aoe_and_aoo_threat_for_increment.cache_clear()
    # Movement transitions
    for coord_and_movement_type, ids in coord_to_sequence_ids.items():
        if coord_and_movement_type is None:
            continue
        coord, movement_type = coord_and_movement_type
        path = battle_map.get_path_to_coord(combatant, np.array(coord, dtype=np.int32), distances, shortest_paths, True)
        if path is None:  # Note that an empty path is still a valid one
            continue
        match movement_type:
            case MovementThreatType.STANDARD:
                movement_threat = accumulate_threat_along_path(path, combatant, effect_to_coords)
            case MovementThreatType.DISENGAGED:
                movement_threat = accumulate_threat_along_path(path, combatant, effect_to_coords, disengaged=True)
            case MovementThreatType.DODGED:
                movement_threat = accumulate_threat_along_path(path, combatant, effect_to_coords, dodged=True)
            case MovementThreatType.MISTY_STEPPED:
                movement_threat, misty_step_path = calc_threat_for_path_with_misty_step(path, combatant, effect_to_coords)  # TODO align this with accumulate_threat_along_path
                transition_name_to_ms_path["ms_" + str(coord)] = misty_step_path
            case _:
                logger.error(f"Unknown movement type {movement_type}")
                movement_threat = accumulate_threat_along_path(path, combatant, effect_to_coords)
        for idx in ids:
            sequence_to_threat[idx] = movement_threat  # We initialize it with the movement threat

    # (Bonus) action transitions
    for coord_and_movement_type, ids in coord_to_sequence_ids.items():
        if coord_and_movement_type is None:
            continue
        coord, _ = coord_and_movement_type
        battle_map.clear_caches()
        with battle_map.as_if_combatant_position(combatant, np.array(coord)):
            for idx in ids:
                delta_action = None
                threat_acc = 0
                first_feasibility_check_done = False
                feasibility_multiplier = 1
                delta_action_t_idx = 0
                for t_idx, transition in enumerate(sequences[idx]):
                    if transition == "dummy":
                        break
                    try:  # Is it a transition which represents a (bonus) action?
                        action = transition_name_to_action[transition]
                        with battle_map.replace_combatant_if_action_by_wildshaped(action, combatant, coord) as did_transform:
                            if ActoidFlags.LOCATION_INDEPENDENT not in action.actoid_flags:
                                if t_idx == 1:  # The first location-dependent action after movement has an eligible movement predecessor guaranteed
                                    feasibility_multiplier = 1 if distances[coord[0] * battle_map.size + coord[1]] <= combatant.movement else infeasibility_multiplier
                                    first_feasibility_check_done = True
                                else:  # Can only be > 1 since the movement is skipped with try-except
                                    eligible_coords = transition_to_eligible_coords[transition]
                                    if not eligible_coords:
                                        continue  # e.g. when there's no place to hide
                                    if not first_feasibility_check_done:  # The case where a location-dependent action follows a location-independent action
                                        feasibility_multiplier = 1 if coord in eligible_coords and distances[coord[0] * battle_map.size + coord[1]] <= combatant.movement else infeasibility_multiplier
                                        first_feasibility_check_done = True
                                    else:  # Two location-dependent actions in succession
                                        remaining_dist = _get_hop_distance_coords(np.array(eligible_coords), np.array([coord]))  # This is a simplification, but good enough
                                        feasibility_multiplier = 1 if remaining_dist <= combatant.movement - distances[coord[0] * battle_map.size + coord[1]] else infeasibility_multiplier
                            threat = action.calculate_threat(consider_dist=(not did_transform), movement_threat=sequence_to_threat[idx])
                            threat_acc += threat
                            if delta_action:
                                delta_threat = delta_action.calculate_threat_for_attack(combatant, action)
                                threat_acc += delta_threat
                                sequence_idx_to_transition_step_threat[idx][delta_action_t_idx] += delta_threat
                            if isinstance(action, AttackThreatModifier):
                                delta_action = action
                                delta_action_t_idx = t_idx
                            for existing_delta_effect in battle_map.effect_tracker.get_affecting_combatant(combatant):
                                if isinstance(existing_delta_effect, AttackThreatModifier):
                                    threat_acc += existing_delta_effect.calculate_threat_for_attack(combatant, action)
                            # This gives us a detailed view of what exactly each transition contributes for the sake of subsequent filtering
                            try:
                                sequence_idx_to_transition_step_threat[idx][t_idx] = threat
                            except KeyError:
                                sequence_idx_to_transition_step_threat[idx] = {t_idx: threat}
                    except KeyError:  # or different kind which represents some type of movement
                        pass  # Skipping
                sequence_to_threat[idx] = [sequence_to_threat[idx][-1], threat_acc * feasibility_multiplier]  # Overwrite the movement threat tuple with the final movement and transition total
                sequence_to_threat[idx][0] += 0.01 if np.array_equal(np.array(coord), current_coords) else 0  # Small bias towards current position prevents oscillations

    sorted_sequences = sorted(sequence_to_threat, key=lambda x: sum(sequence_to_threat[x]) if sequence_to_threat[x][1] > 0 else -math.inf, reverse=True)
    # sorted_sequences = sorted(sequence_to_threat, key=lambda x: sum(sequence_to_threat[x]), reverse=True) This has significance to NOP, 'sequence_to_threat[x][1] > 0' precludes NOP being selected. I should check Fighter vs Fighter again
    nearest_and_minimized_sequence, max_threat = get_nearest_and_minimize(sequences, sorted_sequences, sequence_to_threat, distances, sequence_idx_to_transition_step_threat, transition_name_to_action)
    return nearest_and_minimized_sequence, transition_name_to_ms_path, max_threat


def get_action(combatant):
    """
    Calculates the next best action. The algorithm works in two phases. In the first phase when the combatant still has movement left,
    it follows the steps described above. In the second phase, once the combatant reaches the target destination or runs out of movement
    the best action is recalculated every time to react to any possible changes on the battle_map.
    :return: the next best actoid
    """
    # start_time = time.time()
    battle_map = Map.get()
    battle_map.clear_caches()
    combatant = combatant.get_current_form()  # Takes care of possible wildshape
    grapple_cond = needs_to_break_out_of_grapple(combatant)
    if grapple_cond and combatant.has_action:
        return BreakGrappleFactory(grapple_cond).create()
    if is_affected_by(combatant, Conditions.PRONE) and combatant.movement >= combatant.speed / 2:
        return GetUpFactory().create()
    distances, shortest_paths = battle_map.calc_dijkstra(combatant)  # Has to be recalculated every time (due to forced movement etc.)
    combatant.shortest_paths_cache = shortest_paths
    if combatant.action_plan:
        if isinstance(combatant.action_plan[0], MovementIncrement) and combatant.movement:
            return combatant.action_plan.pop(0)
    combatant.action_plan = combatant.calculate_action_plan(distances, shortest_paths)
    if not combatant.action_plan:
        return None  # Either no action possible or all actions already used
    # print("---get_action_plan took %s seconds ---" % (time.time() - start_time))
    return combatant.action_plan.pop(0)
