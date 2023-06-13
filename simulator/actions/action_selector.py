import copy
import logging
import re
import math

import numpy as np
from toposort import toposort_flatten

from simulator.actions.action_constants import PRIORITY_ACTIONS
from simulator.actions.action_types import Movement
from simulator.actions.break_grapple import BreakGrappleFactory
from simulator.actions.movement import MovementGenerator, GetUpFactory, MovementIncrement
from simulator.battle_map import convert_path_to_increments
from simulator.combatant_coords import CombatantCoords
from simulator.misc import reconstruct_path_through_dag, Conditions
from simulator.spells.misty_step import MistyStepFactory
from simulator.threat_utils import accumulate_threat_along_path, get_aoe_and_aoo_threat_for_increment, \
    calc_threat_for_path_with_misty_step

logger = logging.getLogger("EncounTroll")

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


def build_priority_transitions(post_priority_transitions, action_to_eligible_coords, dag, added_states, transition_name_to_action):
    """
    A helper function which builds the priority part of the DAG such as Dodge or Disengage.
    :param post_priority_transitions: dict from transition -> list of eligible follow-up transitions if the form of (transition, dest_state)
    :param action_to_eligible_coords: mapping from action names to their eligible coordinates
    :param dag: the DAG which we're building
    :param added_states: set of already existing states to avoid adding them multiple times
    :param transition_name_to_action: dict mapping action names -> actions
    :return: None but the the dag is modified
    """
    for transition, post_transitions in post_priority_transitions.items():
        if not post_transitions:  # If there are no follow-up actions possible, connect directly to nop and return
            dag.add_transition(transition, "0", "nop")
            continue
        action_type = transition.split()[0]
        new_source_state = action_type + "d"  # e.g. Dodge of FooBar -> Dodged
        prefix = PRIORITY_ACTIONS[transition_name_to_action[transition].factory.action_type][1]
        if new_source_state not in added_states:
            added_states.add(new_source_state)
            dag.add_state(new_source_state)
        dag.add_transition(transition, "0", new_source_state)
        for post_transition in post_transitions:
            try:
                for coord in action_to_eligible_coords[post_transition[0]]:
                    coord = tuple(coord)
                    coord_state_name = prefix + str(coord)  # Needs to be made unique from the other coord states
                    if coord_state_name not in added_states:
                        added_states.add(coord_state_name)
                        dag.add_state(coord_state_name)
                    move_transition_name = prefix + str(coord)
                    dag.add_transition(move_transition_name, new_source_state, coord_state_name)  # Will be added multiple times, but it's ok
                    dag.add_transition(post_transition[0], coord_state_name, post_transition[1])
            except KeyError:
                pass  # Some may not be available for the secondary plan

def prune_dead_dependencies(dag):
    """
    A small helper function which cuts off the dependencies any states that are unreachable from '0'. This is necessary since
    the dead branch may be arbitrarily long (for long multiattacks)
    :param dag: the DAG to be pruned
    :return: None but the dag is modified
    """
    removed = True
    while removed:
        removed = False
        for state in dag.states:
            try:
                if not dag.dependencies[state]:
                    logger.info(f"Pruning state {state}")  # TODO Remove me, FIXME
                    for successor_state in dag.forward_transitions[state]:
                        dag.dependencies[successor_state].remove(state)
                        # TODO delete key if set empty?
                    removed = True
            except KeyError:
                pass  # Will happen for state 0

def decode_ms_path_to_actions(combatant, initial_coord, ms_path, actions, ms_pattern, ms_factory):
    """
    A helper function which decodes an action which represents movement with the possibility of including Misty Step into a sequence of
    actions which look like: regular movement (optional), Misty Step, regular movement (optional)
    :param combatant: the combatant for whom the actions are translated
    :param initial_coord: the initial coordinate of the combatant
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
    if before_ms_idx is not None:
        before_path = [initial_coord]
        for i in range(0, before_ms_idx + 1):
            x, y = re.search(ms_pattern, ms_path[i]).groups()
            before_path.append(np.array([int(x), int(y)]))
        before_path = convert_path_to_increments(before_path)
        actions.extend(list(MovementGenerator(combatant, before_path, Movement.STANDARD).get_generator()))  # Unpack the movement generator
    x, y = re.search(ms_pattern, ms_path[ms_idx]).groups()
    actions.append(ms_factory.create(np.array([int(x), int(y)])))
    if after_ms_idx is not None:
        after_path = [actions[-1].coord]  # use the Misty Step target coord as the initial one
        for i in range(ms_idx + 1, after_ms_idx + 1):
            x, y = re.search(ms_pattern, ms_path[i]).groups()
            after_path.append(np.array([int(x), int(y)]))
        after_path = convert_path_to_increments(after_path)
        actions.extend(list(MovementGenerator(combatant, after_path, Movement.STANDARD).get_generator()))  # Unpack the movement generator

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
        if action == "dummy":
            continue
        try:
            actions.append(transition_name_to_action[action])
        except KeyError:
            movement_type, x, y = re.search(pattern, action).groups()
            match movement_type:
                case "m" | "do":
                    path = battle_map.get_path_to_coord(combatant,  np.array([int(x), int(y)]), distances, shortest_paths, True)
                    movement_generator = MovementGenerator(combatant, path, Movement.STANDARD).get_generator()
                    actions.extend(list(movement_generator))  # Unpack the movement generator
                case "di":
                    path = battle_map.get_path_to_coord(combatant, np.array([int(x), int(y)]), distances, shortest_paths, False)
                    movement_generator = MovementGenerator(combatant, path, Movement.DISENGAGE).get_generator()
                    actions.extend(list(movement_generator))  # Unpack the movement generator
                case "ms":
                    decode_ms_path_to_actions(combatant, battle_map.get_combatant_position(combatant).get()[0], transition_name_to_ms_path[action], actions, ms_pattern, ms_factory)
                    # TODO also unpack actions
                case _:
                    logger.error(f"Unknown movement type {movement_type}")
    return actions

def get_pretend_coords(current_coords, search_pattern, state, max_threat_backwards_transition):
    """
    A helper function which determines if we use the coordinates of the previous transition of the current coordinates or None
    :param current_coords: combatant's current coordinates
    :param search_pattern: regex coordinate search pattern
    :param state: state of the dag currently being examined
    :param max_threat_backwards_transition: backwards transition dict which state -> predecessor state
    :return: the coordinate to be considered as the combatant's position when calculating the next transition threat
    """
    curr_state = state
    while True:
        try:
            previous_transition_name = max_threat_backwards_transition[curr_state][0]
            _, x, y = re.search(search_pattern, previous_transition_name).groups()
            curr_state = max_threat_backwards_transition[curr_state][1]
            pretend_coords = CombatantCoords(np.array([int(x), int(y)]))
            return pretend_coords
        except KeyError:
            break
        except AttributeError:
            curr_state = max_threat_backwards_transition[curr_state][1]
        except Exception as e:
            logger.error(f"Unexpected exception occurred in get_pretend_coords: {e}")
            break
    return current_coords

def get_threat_modification_by_previous_action(combatant, battle_map, state, action, max_threat_backwards_transition, transition_name_to_action):
    """
    Goes back through the backwards transitions looking for an ability that would mofidy the threat of the current action
    :param combatant:
    :param battle_map:
    :param state: current state
    :param action: action to be modified
    :param max_threat_backwards_transition: backwards transition to the preceeding best action
    :param transition_name_to_action: dict mapping action names -> actions
    :return: threat modification
    """
    threat = 0
    curr_state = state
    while True:
        try:
            previous_transition_name = max_threat_backwards_transition[curr_state][0]
            threat = transition_name_to_action[previous_transition_name].calculate_threat_for_attack(combatant, battle_map, action)
            break
        except (KeyError, AttributeError):
            try:
                curr_state = max_threat_backwards_transition[curr_state][1]
            except KeyError:
                break
        except Exception as e:
            logger.error(f"Unexpected exception occurred in get_threat_modification_by_previous_action: {e}")
            break
    return threat

def build_action_dag(combatant, battle_map, action_fsm, transition_name_to_action, distances, shortest_paths, post_misty_step_actions):
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
    :param distances: the distances to all squares (result of Dijkstra)
    :param shortest_paths: the shortest paths to all squares (result of Dijkstra)
    :param post_misty_step_actions: list of actions that are eligible after taking the Misty Step action
    :return: dict which maps threat -> (start_index, end_index) and a mapping from state name -> coord
    """
    post_priority_transitions = get_post_transitions_of_priority_transitions(action_fsm, transition_name_to_action)
    for priority_transition in post_priority_transitions.keys():  # TODO Do I need to have them removed for all states or just 0?
        for origin_state in action_fsm.states.keys():
            action_fsm.remove_transition(priority_transition, origin_state)  # Get rid of the originals, don't want to have them pre-pended with coords

    dag = copy.deepcopy(action_fsm)
    transition_names = action_fsm.get_available_transitions()
    transition_names = list(filter(lambda t: t != "dummy", transition_names))
    if not transition_names or transition_names[0] == 'None':
        return None
    if not post_misty_step_actions:
        post_misty_step_actions = []

    if combatant.movement > 0:
        action_to_eligible_coords = {tn: transition_name_to_action[tn].get_eligible_coords(battle_map, distances, shortest_paths) for tn in transition_names}
    else:
        current_position = tuple(battle_map.get_combatant_position(combatant).get()[0])
        action_to_eligible_coords = {tn: [current_position] for tn in transition_names if transition_name_to_action[tn].is_current_coord_eligible(battle_map)}

    for transition in transition_names:  # Filter out actions which don't have any eligible coords
        if transition not in action_to_eligible_coords.keys():
            dag.remove_transition(transition, '0')

    added_states = set()  # tracks which states have already been added
    for action_name, coords in action_to_eligible_coords.items():
        # if action_name.startswith("Wildshape"):
        #     continue  # Wilshape itself is coord-independent but we're interested in the coords of the follow-up actions
        for coord in coords:
            transitions = [t[0] for t in action_fsm.events[action_name].transitions.values() if t[0].source == "0"]
            assert len(transitions) == 1
            for transition in transitions:  # Iterate over the original to avoid deleting from the one being iterated over
                new_state_and_transition_name = "m_" + str(coord)
                if new_state_and_transition_name not in added_states:
                    added_states.add(new_state_and_transition_name)
                    dag.add_state(new_state_and_transition_name)
                    dag.add_transition(new_state_and_transition_name, transition.source, new_state_and_transition_name)  # Will be added multiple times, but it's ok
                dag.add_transition(action_name, new_state_and_transition_name, transition.dest)

                # Make a special graph section to model misty step. The ms_ transition implies the possibility of Misty Step included in the movement (not a direct jump to the coord)
                if action_name in post_misty_step_actions:
                    new_state_name = "ms_" + str(coord)
                    if new_state_name not in added_states:
                        added_states.add(new_state_name)
                        dag.add_state(new_state_name)
                    dag.add_transition(new_state_name, "0", new_state_name)  # transition name is the same as state name
                    dag.add_transition(action_name, new_state_name, "nop")
        try:
            dag.remove_transition(action_name, transition.source)  # Remove the original
        except AttributeError as e:
            print("FIXME")

    build_priority_transitions(post_priority_transitions, action_to_eligible_coords, dag, added_states, transition_name_to_action)
    prune_dead_dependencies(dag)
    return dag


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
    :return: the longest path in the DAG as per the threat along its edges and nodes and a mapping of transitions names
    to special Misty Step paths
    """
    # combatant = combatant.get_current_form()  # Takes care of possible wildshape
    effect_to_coords = {e: e.get_affected_coords(battle_map) for e in battle_map.effect_tracker.get_aoe_effects()}
    threat = {key: [-math.inf, -math.inf] for key in sorted_states}
    sorted_states.pop()  # Get rid of the nop state
    threat['0'] = [0, 0]
    max_threat_backwards_transition = dict()
    pattern = r'([msdio]+)_\((\d+), (\d+)\)'
    transition_name_to_ms_path = dict()
    current_coords = battle_map.get_combatant_position(combatant)

    # Optimization: calculate_threat is cached, so we need to clear the cache before the computation
    # for action in transition_name_to_action.values():
    #     action.clear_cache()

    for state in sorted_states:
        if state != '0' and not dag.dependencies[state]:
            continue  # This essentially prunes unreachable states
        for transition_name, target_state in dag.forward_transitions[state]:
            if transition_name == "dummy":
                transition_threat = threat[state][1] if threat[state][1] > -math.inf else 0
                movement_threat = threat[state][0] if threat[state][0] > -math.inf else 0
            else:
                try:
                    # Is it a transition which represents a (bonus) action?
                    pretend_coords = get_pretend_coords(current_coords, pattern, state, max_threat_backwards_transition)
                    pretend_coords = pretend_coords.get()[0] if pretend_coords is not None else None

                    action = transition_name_to_action[transition_name]
                    with battle_map.as_if_combatant_position(combatant, pretend_coords), battle_map.replace_combatant_if_action_by_wildshaped(action, combatant) as did_transform:
                        transition_threat = action.calculate_threat(combatant, battle_map, consider_dist=(not did_transform)) + (threat[state][1] if threat[state][1] > -math.inf else 0)
                        transition_threat += get_threat_modification_by_previous_action(combatant, battle_map, state, action, max_threat_backwards_transition, transition_name_to_action)
                    movement_threat = threat[state][0] if threat[state][0] > -math.inf else 0
                except KeyError:  # either not in the dict or regex search came up empty
                    # or different kind which represents some type of movement
                    movement_type, x, y = re.search(pattern, transition_name).groups()
                    destination = np.array([int(x), int(y)])
                    path = battle_map.get_path_to_coord(combatant, destination, distances, shortest_paths, True)
                    if path is None:  # Note that an empty path is still a valid one
                        continue
                    match movement_type:
                        case "m":
                            movement_threat = accumulate_threat_along_path(battle_map, path, combatant, effect_to_coords)
                        case "di":
                            movement_threat = accumulate_threat_along_path(battle_map, path, combatant, effect_to_coords, disengaged=True)
                        case "do":
                            movement_threat = accumulate_threat_along_path(battle_map, path, combatant, effect_to_coords, dodged=True)
                        case "ms":
                            movement_threat, misty_step_path = calc_threat_for_path_with_misty_step(battle_map, path, combatant, effect_to_coords)
                            transition_name_to_ms_path[transition_name] = misty_step_path
                        case _:
                            logger.error(f"Unknown movement type {movement_type}")
                            movement_threat = accumulate_threat_along_path(battle_map, path, combatant, effect_to_coords)
                    transition_threat = threat[state][1] if threat[state][1] > -math.inf else 0
                    movement_threat += 0.01 if np.array_equal(destination, current_coords.get()[0]) else 0  # Small bias towards current position
            if (movement_threat + transition_threat > sum(threat[target_state])) or (threat[target_state][1] <= 0 and transition_threat > 0):
                threat[target_state] = [movement_threat, transition_threat]
                max_threat_backwards_transition[target_state] = (transition_name, state)
    if not max_threat_backwards_transition:
            return None, None
    # Let's go backwards to reconstruct the longest path
    return reconstruct_path_through_dag('nop', '0', max_threat_backwards_transition), transition_name_to_ms_path



def get_action(combatant, battle_map):
    """
    Calculates the next best action. The algorithm works in two phases. In the first phase when the combatant still has movement left,
    it follows the steps described above. In the second phase, once the combatant reaches the target destination or runs out of movement
    the best action is recalculated every time to react to any possible changes on the battle_map.
    :param battle_map:
    :return: the next best actoid
    """
    combatant = combatant.get_current_form()  # Takes care of possible wildshape
    grapple_cond = combatant.needs_to_break_out_of_grapple()
    if grapple_cond:
        return BreakGrappleFactory(grapple_cond).create()
    if combatant.is_affected_by(Conditions.PRONE):
        return GetUpFactory().create()
    distances, shortest_paths = battle_map.calc_dijkstra(combatant)  # Has to be recalculated every time (due to forced movement etc.)
    combatant.shortest_paths_cache = shortest_paths
    if combatant.action_plan:
        if isinstance(combatant.action_plan[0], MovementIncrement) and combatant.movement:
            return combatant.action_plan.pop(0)
    combatant.action_plan = combatant.calculate_action_plan(battle_map, distances, shortest_paths)
    if not combatant.action_plan:
        return None  # Either no action possible or all actions already used
    return combatant.action_plan.pop(0)
