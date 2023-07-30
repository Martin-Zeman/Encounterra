import copy
import logging
import re
import math
import sys
import time

import numpy as np

from simulator.actions.action_constants import PRIORITY_ACTIONS
from simulator.actions.action_types import Movement
from simulator.actions.break_grapple import BreakGrappleFactory
from simulator.actions.movement import MovementGenerator, GetUpFactory, MovementIncrement
from simulator.battle_map import convert_path_to_increments, Map
from simulator.misc import Conditions
from simulator.spells.misty_step import MistyStepFactory
from simulator.threat_interfaces import AttackThreatModifier
from simulator.threat_utils import accumulate_threat_along_path, calc_threat_for_path_with_misty_step

logger = logging.getLogger("EncounTroll")

REGEX_MOVEMENT_PATTERN = re.compile(r'([msdchio]+)_\((\d+), (\d+)\)')
REGEX_MS_MOVEMENT_PATTERN = re.compile(r'[mschdio_]+\((\d+), (\d+)\)')


def get_post_transitions_of_priority_transitions(dag, transition_name_to_action):
    """
    A helper function which gets eligible follow-up actions to all priority actions present in the DAG
    :param combatant: the combatant taking the actions
    :param dag: the DAG on which we operate
    :param transition_name_to_action: dict mapping action names -> actions
    :return: dict priority_transition_name -> list of eligible follow-up transitions
    """
    post_priority_transitions = dict()
    for transition in dag.get_available_transitions():
        if transition == 'None':
            break
        if transition_name_to_action[transition].factory.action_type in PRIORITY_ACTIONS.keys():
            post_transitions = None
            if dag.trigger(transition):
                # We filter out priority transitions even from all the post transitions
                try:
                    post_transitions = [ft for ft in dag.forward_transitions[dag.state] if transition_name_to_action[ft[0]].factory.action_type not in PRIORITY_ACTIONS.keys()]
                except KeyError:
                    pass  # For the case when the target state is nop
                dag.reset()
            post_priority_transitions[transition] = post_transitions
    return post_priority_transitions

def get_post_misty_step_transitions(dag, transition_name_to_action):
    dag.trigger("Misty Step to 0, 0_1")  # It's the only MS we created
    ms_post_transitions = [pt for pt in dag.forward_transitions[dag.state] if transition_name_to_action[pt[0]].factory.action_type not in PRIORITY_ACTIONS.keys()]
    dag.reset()
    return ms_post_transitions

def build_misty_step_transitions(dag, ms_post_transitions, transition_to_eligible_coords, eligible_transitions_to_state, coord_to_eligible_transitions):
    for mspt in ms_post_transitions:
        for coord in transition_to_eligible_coords[mspt[0]]:
            try:
                post_ms_state = eligible_transitions_to_state[coord_to_eligible_transitions[coord]]
            except KeyError:
                post_ms_state = dag.get_next_state_name()
                dag.add_state(post_ms_state)
            dag.add_transition("ms_" + str(coord), "0", post_ms_state)


def build_priority_transitions(post_priority_transitions, transition_to_eligible_coords, dag, transition_name_to_action):
    """
    A helper function which builds the priority part of the DAG such as Dodge or Disengage.
    :param post_priority_transitions: dict from transition -> list of eligible follow-up transitions if the form of (transition, dest_state)
    :param transition_to_eligible_coords: mapping from action names to their eligible coordinates
    :param dag: the DAG which we're building
    :param transition_name_to_action: dict mapping action names -> actions
    :return: None but the the dag is modified
    """
    newly_added_states = []
    for transition, post_transitions in post_priority_transitions.items():
        if not post_transitions:  # If there are no follow-up actions possible, connect directly to nop and return
            dag.add_transition(transition, "0", "nop")
            continue
        action_type = transition.split()[0]
        new_prio_state = action_type + "d"  # e.g. Dodge of FooBar -> Dodged
        prefix = PRIORITY_ACTIONS[transition_name_to_action[transition].factory.action_type][1]
        dag.add_state(new_prio_state)
        newly_added_states.append(new_prio_state)
        dag.add_transition(transition, "0", new_prio_state)
        for post_transition in post_transitions:
            try:
                for coord in transition_to_eligible_coords[post_transition[0]]:
                    coord_state_name = prefix + str(tuple(coord))  # Needs to be made unique from the other coord states
                    dag.add_transition(coord_state_name, new_prio_state, coord_state_name)  # Will be added multiple times, but it's ok
                    dag.add_transition(post_transition[0], coord_state_name, post_transition[1])
            except KeyError:
                pass  # Some may not be available for the secondary plan

    # Some states may have been left unconnected due to their follow-up actions not having eligible coords -> connect them to nop
    for newly_added_state in newly_added_states:
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
    x, y = REGEX_MS_MOVEMENT_PATTERN.search(ms_path[ms_idx]).groups()
    actions.append(ms_factory.create(np.array([int(x), int(y)])))
    if after_ms_idx is not None:
        after_path = [actions[-1].coord]  # use the Misty Step target coord as the initial one
        for i in range(ms_idx + 1, after_ms_idx + 1):
            x, y = REGEX_MS_MOVEMENT_PATTERN.search(ms_path[i]).groups()
            after_path.append(np.array([int(x), int(y)]))
        after_path = convert_path_to_increments(after_path)
        actions.extend(list(MovementGenerator(combatant, after_path, Movement.STANDARD).get_generator()))  # Unpack the movement generator

def translate_sequence_to_actions(combatant, distances, shortest_paths, transition_name_to_action, longest_pth, transition_name_to_ms_path):
    """
    Translates the string form of longest path back to action objects
    :param combatant: the combatant for whom the actions are translated
    :param distances: potentially already pre-computed distances to all coords
    :param shortest_paths: potentially already pre-computed shortest paths to all coords
    :param transition_name_to_action: dictionary mapping of non-movement types to actions
    :param longest_pth: list of best actions as strings
    :param transition_name_to_ms_path: dictionary mapping of transition names to paths that may include a Misty Step (can be empty)
    :return: list of the following types: np.array, action, bonus action
    """
    ms_factory = MistyStepFactory(combatant)
    actions = []
    battle_map = Map.get()
    for action in longest_pth:
        if action == "dummy":
            continue
        try:
            actions.append(transition_name_to_action[action])
        except KeyError:
            movement_type, x, y = REGEX_MOVEMENT_PATTERN.search(action).groups()
            match movement_type:
                case "m" | "do":
                    path = battle_map.get_path_to_coord(combatant,  np.array([int(x), int(y)]), distances, shortest_paths, True)
                    movement_generator = MovementGenerator(combatant, path, Movement.STANDARD).get_generator()
                    actions.extend(list(movement_generator))  # Unpack the movement generator
                case "di" | "cdi" | "hdi":
                    path = battle_map.get_path_to_coord(combatant, np.array([int(x), int(y)]), distances, shortest_paths, False)
                    movement_generator = MovementGenerator(combatant, path, Movement.DISENGAGED).get_generator()
                    actions.extend(list(movement_generator))  # Unpack the movement generator
                case "ms":
                    decode_ms_path_to_actions(combatant, battle_map.get_combatant_position(combatant).get()[0], transition_name_to_ms_path[action], actions, ms_factory)
                    # TODO also unpack actions
                case _:
                    logger.error(f"Unknown movement type {movement_type}")
    return actions

def extract_movement(combatant, distances, shortest_paths, longest_pth):
    """
    Extracts the movement part of an action plan
    :param combatant: the combatant for whom the actions are translated
    :param distances: potentially already pre-computed distances to all coords
    :param shortest_paths: potentially already pre-computed shortest paths to all coords
    :param longest_pth: list of best actions as strings
    :return: list of movement increments or None
    """
    actions = []
    for action in longest_pth:
        if action == "dummy":
            continue
        match = REGEX_MOVEMENT_PATTERN.search(action)
        if match:
            _, x, y = match.groups()
            path = Map.get().get_path_to_coord(combatant,  np.array([int(x), int(y)]), distances, shortest_paths, True)
            movement_generator = MovementGenerator(combatant, path, Movement.STANDARD).get_generator()
            actions.extend(list(movement_generator))  # Unpack the movement generator
            break
    return actions if actions else None


def get_dist_to_action_sequence_coord(longest_pth, distances):
    """
    Extracts the movement part of an action plan and returns the distance to its coordinate
    :param longest_pth: list of best actions as strings
    :param distances: potentially already pre-computed distances to all coords
    :return: list of movement increments or None
    """
    for action in longest_pth:
        if action == "dummy":
            continue
        match = REGEX_MOVEMENT_PATTERN.search(action)
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
        dag.add_state(state_name)
    return eligible_transitions_to_state, coord_to_eligible_transitions


def build_action_dag(combatant, action_fsm, transition_name_to_action, distances, shortest_paths):
    """
    Builds action DAG for a combatant given the combatant's action_fsm. It determines eligible coords for each
    action. Then the coords are pre-pended into the action_fsm to form the final DAG. However, Misty Step, Dodge and
    Disengage require special treatment. Misty Step generates a special form of movement which is added as a transition
    to all post-Misty-Step states. Dodge and Disengage always make sense to be taken before any movement, therefore
    in their case coords are also pre-pended to their follow-up actions.
    :param combatant: the combatant for whom the DAG is modeled
    :param action_fsm: finite state machine representing all possible actions for combatant
    :param transition_name_to_action: dict mapping action names -> actions
    :param distances: the distances to all squares (result of Dijkstra)
    :param shortest_paths: the shortest paths to all squares (result of Dijkstra)
    :return: dict which maps threat -> (start_index, end_index) and a mapping from state name -> coord
    """
    battle_map = Map.get()
    battle_map.calc_visibility_dict_for_all_coords(combatant, shortest_paths)
    post_priority_transitions = get_post_transitions_of_priority_transitions(action_fsm, transition_name_to_action)
    for priority_transition in post_priority_transitions.keys():  # TODO Do I need to have them removed for all states or just 0?
        for origin_state in action_fsm.states.keys():
            action_fsm.remove_transition(priority_transition, origin_state)  # Get rid of the originals, don't want to have them pre-pended with coords

    dag = copy.deepcopy(action_fsm)
    transition_names = action_fsm.get_available_transitions()
    if 'Misty Step to 0, 0_1' in transition_names:
        has_misty_step = True
        post_misty_step_transitions = get_post_misty_step_transitions(dag, transition_name_to_action)
    transition_names = list(filter(lambda t: t != "dummy", transition_names))
    if not transition_names or transition_names[0] == 'None':
        return None

    if combatant.movement > 0 and not combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED, Conditions.SWALLOWED):
        transition_to_eligible_coords = {tn: transition_name_to_action[tn].get_eligible_coords(distances, shortest_paths) for tn in transition_names}
        transition_to_eligible_coords.update({tn[0]: transition_name_to_action[tn[0]].get_eligible_coords(distances, shortest_paths) for pre in post_priority_transitions.values() for tn in pre})
        if has_misty_step:  # TODO
            transition_to_eligible_coords.update({tn[0]: transition_name_to_action[tn[0]].get_eligible_coords(distances, shortest_paths) for tn in post_misty_step_transitions})
    else:
        current_position = tuple(battle_map.get_combatant_position(combatant).get()[0])
        transition_to_eligible_coords = {tn: [current_position] for tn in transition_names if transition_name_to_action[tn].is_current_coord_eligible()}
        transition_to_eligible_coords.update({tn[0]: [current_position] for pre in post_priority_transitions.values() if transition_name_to_action[tn[0]].is_current_coord_eligible() for tn in pre})
        if has_misty_step:  # TODO
            transition_to_eligible_coords.update({tn[0]: transition_name_to_action[tn[0]].get_eligible_coords(distances, shortest_paths) for tn in post_misty_step_transitions})

    for transition_name in transition_names:  # Filter out actions which don't have any eligible coords
        try:
            if not transition_to_eligible_coords[transition_name]:
                dag.remove_transition(transition_name, '0')
        except KeyError:
            dag.remove_transition(transition_name, '0')  # Happens where the combatant's out of movement

    eligible_transitions_to_state, coord_to_eligible_transitions = create_movement_states(dag, transition_to_eligible_coords)

    has_misty_step = False
    for transition_name, coords in transition_to_eligible_coords.items():
        if transition_name.startswith("Misty Step"):
            continue
        transitions = [t[0] for t in action_fsm.events[transition_name].transitions.values() if t[0].source == "0"]  # Iterate over the original to avoid deleting from the one being iterated over
        if not transitions:
            continue  # Happens for all actions of source != 0
        transition = transitions[0]
        for coord in coords:
            movement_state_name = eligible_transitions_to_state[coord_to_eligible_transitions[coord]]
            dag.add_transition("m_" + str(coord), "0", movement_state_name)
            dag.add_transition(transition_name, movement_state_name, transition.dest)
        dag.remove_transition(transition_name, "0")  # Remove the original

    if has_misty_step:
        build_misty_step_transitions(dag, transition_name_to_action, transition_to_eligible_coords, eligible_transitions_to_state, coord_to_eligible_transitions)

    build_priority_transitions(post_priority_transitions, transition_to_eligible_coords, dag, transition_name_to_action)
    return dag


def DFS(dag, sequences, current_state, current_sequence):
    if current_state == 'nop':
        sequences.append(copy.deepcopy(current_sequence))
        return

    for transition, next_state in dag.forward_transitions[current_state]:
        current_sequence.append(transition)
        DFS(dag, sequences, next_state, current_sequence)
        current_sequence.pop()


def get_nearest_from_best_sequences(sequences, sorted_sequences, sequence_to_threat, distances):
    """
    Takes all the sequences with the maximum threat (if there are multiple) and keeps the one with the nearest coordinate.
    This is important for the get_movement_for_next_turn function. This will typically pick between equal sets of action just in a different
    order.
    :param sequences: all the action sequences in no particular order
    :param sorted_sequences: indices of sequences sorted by threat in descending order
    :param sequence_to_threat: dict mapping sequence index -> threat
    :param distances: potentially already pre-computed distances to all coords
    :return: maximum threat sequence with the more distant coordinate requirement
    """
    max_threat = sequence_to_threat[sorted_sequences[0]]
    idx = 0
    while idx < len(sorted_sequences) and sequence_to_threat[sorted_sequences[idx]] == max_threat:
        idx += 1
    sorted_sequences = sorted_sequences[:idx]
    min_dist = sys.maxsize
    min_dist_idx = sorted_sequences[0]
    for idx in sorted_sequences:
        dist = get_dist_to_action_sequence_coord(sequences[idx], distances)
        if dist < min_dist:
            min_dist = dist
            min_dist_idx = idx
    return sequences[min_dist_idx]


def calc_best_sequence(combatant, dag, transition_name_to_action, distances, shortest_paths):
    """
    Finds the path through the DAG which represents the movement and actions with the highest calculated threat.
    :param combatant: the combatant for whom the DAG is modeled
    :param dag: finite state machine representing all possible actions for combatant
    :param transition_name_to_action: dict mapping action names -> actions
    :param distances: potentially already pre-computed distances to all coords
    :param shortest_paths: potentially already pre-computed shortest paths to all coords
    :return: the longest path in the DAG as per the threat along its edges and nodes and a mapping of transitions names
    to special Misty Step paths
    """
    battle_map = Map.get()
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    sequences = []
    transition_name_to_ms_path = dict()
    sequence_to_threat = dict()
    current_coords = battle_map.get_combatant_position(combatant)
    DFS(dag, sequences, '0', [])

    # Optimization: calculate_threat is cached, so we need to clear the cache before the computation
    for action in transition_name_to_action.values():
        action.clear_cache()

    for idx, sequence in enumerate(sequences):
        threat_acc = [0, 0]  # movement threat, transition threat
        pretend_coords = None
        delta_action = None
        for transition in sequence:
            if transition == "dummy":
                break
            try:  # Is it a transition which represents a (bonus) action?
                action = transition_name_to_action[transition]
                with battle_map.as_if_combatant_position(combatant, pretend_coords) as orig_coords, battle_map.replace_combatant_if_action_by_wildshaped(action, combatant, orig_coords) as did_transform:
                    threat_acc[1] += action.calculate_threat(consider_dist=(not did_transform))
                    if delta_action:
                        threat_acc[1] += delta_action.calculate_threat_for_attack(combatant, action)
                    if isinstance(action, AttackThreatModifier):
                        delta_action = action
            except KeyError:  # or different kind which represents some type of movement
                movement_type, x, y = REGEX_MOVEMENT_PATTERN.search(transition).groups()
                destination = np.array([int(x), int(y)])
                pretend_coords = destination
                path = battle_map.get_path_to_coord(combatant, destination, distances, shortest_paths, True)
                if path is None:  # Note that an empty path is still a valid one
                    continue
                match movement_type:
                    case "m":
                        movement_threat = accumulate_threat_along_path(path, combatant, effect_to_coords)
                    case "di" | "cdi" | "hdi":
                        movement_threat = accumulate_threat_along_path(path, combatant, effect_to_coords, disengaged=True)
                    case "do":
                        movement_threat = accumulate_threat_along_path(path, combatant, effect_to_coords, dodged=True)
                    case "ms":
                        movement_threat, misty_step_path = calc_threat_for_path_with_misty_step(path, combatant, effect_to_coords)
                        transition_name_to_ms_path[transition] = misty_step_path
                    case _:
                        logger.error(f"Unknown movement type {movement_type}")
                        movement_threat = accumulate_threat_along_path(path, combatant, effect_to_coords)
                movement_threat += 0.01 if np.array_equal(destination, current_coords.get()[0]) else 0  # Small bias towards current position
                threat_acc[0] += movement_threat
        sequence_to_threat[idx] = copy.copy(threat_acc)
    # We only consider sequences that contain a greater-than-zero transition action
    sorted_sequences = sorted(sequence_to_threat, key=lambda x: sum(sequence_to_threat[x]) if sequence_to_threat[x][1] > 0 else -math.inf, reverse=True)
    return get_nearest_from_best_sequences(sequences, sorted_sequences, sequence_to_threat, distances), transition_name_to_ms_path


def get_action(combatant):
    """
    Calculates the next best action. The algorithm works in two phases. In the first phase when the combatant still has movement left,
    it follows the steps described above. In the second phase, once the combatant reaches the target destination or runs out of movement
    the best action is recalculated every time to react to any possible changes on the battle_map.
    :return: the next best actoid
    """
    start_time = time.time()
    combatant = combatant.get_current_form()  # Takes care of possible wildshape
    grapple_cond = combatant.needs_to_break_out_of_grapple()
    if grapple_cond and combatant.has_action:
        return BreakGrappleFactory(grapple_cond).create()
    if combatant.is_affected_by(Conditions.PRONE) and combatant.movement >= combatant.speed / 2:
        return GetUpFactory().create()
    distances, shortest_paths = Map.get().calc_dijkstra(combatant)  # Has to be recalculated every time (due to forced movement etc.)
    combatant.shortest_paths_cache = shortest_paths
    if combatant.action_plan:
        if isinstance(combatant.action_plan[0], MovementIncrement) and combatant.movement:
            return combatant.action_plan.pop(0)
    combatant.action_plan = combatant.calculate_action_plan(distances, shortest_paths)
    if not combatant.action_plan:
        return None  # Either no action possible or all actions already used
    print("---get_action_plan took %s seconds ---" % (time.time() - start_time))
    return combatant.action_plan.pop(0)
