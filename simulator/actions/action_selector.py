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
    action. It then filters the coords such that only the closest one per threat level is kept (this is a heuristic
    since it may no longer be the closest if the combatant first moves for another action). Then the coords are
    pre-pended into the action_fsm to form the final DAG.
    :param combatant:
    :param battle_map:
    :param action_fsm: finite state machine representing all possible actions for combatant
    :param transition_name_to_action: dict mapping action names -> actions
    :return: dict which maps threat -> (start_index, end_index) and a mapping from state name -> coord
    """
    # TODO: Look into caching!!!
    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(combatant)
    dag = copy.deepcopy(action_fsm)

    # get eligible coords for all actions
    transition_names = action_fsm.get_available_transitions()
    transition_actions = [transition_name_to_action[t] for t in transition_names]
    action_to_eligible_coords = {a: a.get_eligible_coords(battle_map) for a in transition_actions if ActoidFlags.IS_POSITIONING_INDEPENDENT not in a.actoid_flags}
    # for action, coords in action_to_eligible_coords.items():
    #     # For each action only pick the closest coord from all coords with the same threat level
    #     coords_w_threats = [(c, accumulate_threat_along_path(battle_map, battle_map.get_path_to_coord(
    #         combatant, np.array(c), distances, shortest_paths, True), combatant)) for c in coords]
    #     # Sort by threat
    #     coords_w_threats.sort(key=lambda c: c[1])
    #     # Find where the borders of threat levels are
    #     groups = find_ranges_of_consecutive(coords_w_threats)
    #     new_coords = []
    #     for rng in groups.values():
    #         coords_w_threats[rng[0]:rng[1] + 1] = sorted(coords_w_threats[rng[0]:rng[1] + 1], key=lambda c: battle_map.get_hop_distance(combatant, np.array([c[0]])))
    #         new_coords.append(coords_w_threats[rng[0]][0])
    #     action_to_eligible_coords[action] = new_coords

    coords_to_states = dict()

    added_transitions = set()
    for action, coords in action_to_eligible_coords.items():
        for coord in coords:
            # try:
            for transitions in action_fsm.events[str(action)].transitions.values():  # Iterate over the original to avoid deleting from the one being iterated over
                for transition in [t for t in transitions if t.source == "0"]:
                    new_state_name = str(coord)
                    dag.add_state(new_state_name)
                    coords_to_states[coord] = new_state_name  # TODO what is this good for? doesn't it get overwritten?
                    move_transition_name ="m_" + new_state_name
                    if move_transition_name not in added_transitions:  # Avoid adding the same transition multiple times
                        dag.add_transition(move_transition_name, transition.source, new_state_name)
                        added_transitions.add(move_transition_name)
                    dag.add_transition(str(action), new_state_name, transition.dest)
                    dag.remove_transition(str(action), transition.source)  # Remove the original
            # except KeyError:
            #     continue

    return dag, coords_to_states


def select_best_action(combatant, battle_map):
    fsm, transition_name_to_action = generate_action_fsm(combatant, battle_map)
    dfs = build_action_dag(combatant, battle_map, fsm, transition_name_to_action)
    # TODO Topological sort
    return dfs
