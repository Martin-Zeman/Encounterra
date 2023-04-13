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

def build_action_dag(combatant, battle_map, action_fsm, transition_name_to_action):
    """
    Builds action DAG for a combatant given the combatant's action_fsm. It determines eligible coords for each
    action at depth == 1. It filters the coords such that only the closest one per threat level is kept. Then
    the coords and pre-pended into the action_fsm to form the final DAG.
    :param combatant:
    :param battle_map:
    :param action_fsm: finite state machine representing all possible actions for combatant
    :param transition_name_to_action: dict mapping action names -> actions
    :return: dict which maps threat -> (start_index, end_index)
    """
    # TODO: Look into caching!!!
    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(combatant)
    dag = copy.deepcopy(action_fsm)

    # get eligible coords for all actions at depth == 1
    transition_names = action_fsm.get_available_transitions()
    transition_actions = [transition_name_to_action[t] for t in transition_names]
    action_to_eligible_coords = {a: a.get_eligible_coords(battle_map) for a in transition_actions if ActoidFlags.IS_POSITIONING_INDEPENDENT not in a.actoid_flags}
    for action, coords in action_to_eligible_coords.items():
        # For each action only pick the closest coord from all coords with the same threat level
        coords_w_threats = [(c, accumulate_threat_along_path(battle_map, battle_map.get_path_to_coord(
            combatant, np.array(c), distances, shortest_paths, True), combatant)) for c in coords]
        # Sort by threat
        coords_w_threats.sort(key=lambda c: c[1])
        # Find where the borders of threat levels are
        groups = find_ranges_of_consecutive(coords_w_threats)
        new_coords = []
        for rng in groups.values():
            coords_w_threats[rng[0]:rng[1] + 1] = sorted(coords_w_threats[rng[0]:rng[1] + 1], key=lambda c: battle_map.get_hop_distance(combatant, np.array([c[0]])))
            new_coords.append(coords_w_threats[rng[0]][0])
        action_to_eligible_coords[action] = new_coords

    all_eligible_coords = set()
    for coord in action_to_eligible_coords.values():
        all_eligible_coords.update(coord)
    coords_to_states = dict()
    for coord in all_eligible_coords:
        # Each coord that is an eligible to at least one action gets a state
        new_state_name = dag.get_next_state_name()
        dag.add_state(new_state_name)
        coords_to_states[coord] = new_state_name

    for action, coords in action_to_eligible_coords.items():
        for coord in coords:
            try:
                for transition in dag.events[str(action)].transitions['0']:
                    if transition.source == '0':
                        original_target = transition.dest
                    else:
                        continue
            except KeyError:
                continue
            # Put the coord state in between
            dag.add_transition("move_to_" + coords_to_states[coord], "0", coords_to_states[coord])
            dag.add_transition(str(action), coords_to_states[coord], original_target)
            dag.remove_transition(str(action))  # Remove the original

    return dag
    # TODO create a state for every of all_eligible_coords
    # Then connect up the states with their respective actions by prepending them between the init state and the next state


def select_best_action(combatant, battle_map):
    fsm, transition_name_to_action = generate_action_fsm(combatant, battle_map)
    dfs = build_action_dag(combatant, battle_map, fsm, transition_name_to_action)
    # TODO
    return dfs
