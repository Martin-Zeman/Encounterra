import copy
import itertools

import numpy as np

from simulator.actions.action_fsms import generate_action_fsm
from simulator.actions.actoid import ActoidFlags
from simulator.threat import accumulate_threat_along_path

def find_ranges_of_consecutive(coords_w_threats):
    res = dict()
    idx = 0
    while idx < len(coords_w_threats):
        start_pos = idx
        val = coords_w_threats[idx][1]

        # getting last pos.
        while (idx < len(coords_w_threats) and coords_w_threats[idx][1] == val):
            idx += 1
        end_pos = idx - 1

        # appending in format [ele, strt_pos, end_pos]
        res[val] = start_pos, end_pos
    return res

def build_action_dfs(combatant, battle_map, action_fsm, transition_name_to_action):
    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(combatant)
    dfs = copy.deepcopy(action_fsm)

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
        # groups = [(k, list(g)) for k, g in itertools.groupby(coords_w_threats, key=lambda c: c[0])]
        # groups = {k: [(i, i + len(g) - 1) for i, (k_, g) in enumerate(groups) if k_ == k] for k, _ in groups}
        groups = find_ranges_of_consecutive(coords_w_threats)
        new_coords = set()
        for rng in groups.values():
            # coords_w_threats[group[1][0][0]:group[1][0][-1] + 1] = sorted(coords[group[1][0][0]:group[1][0][-1] + 1], key=lambda c: battle_map.get_hop_distance(combatant, c[0]))
            coords_w_threats[rng[0]:rng[1] + 1] = sorted(coords_w_threats[rng[0]:rng[1] + 1], key=lambda c: battle_map.get_hop_distance(combatant, np.array([c[0]])))
            new_coords.add(coords_w_threats[rng[0]][0])
        action_to_eligible_coords[action] = new_coords



    all_eligible_coords = set()
    for coord in action_to_eligible_coords.values():
        all_eligible_coords.update(coord)
    coords_to_states = dict()
    for coord in all_eligible_coords:
        # Each coord that is an eligible to at least one action gets a state
        new_state_name = dfs.get_next_state_name()
        dfs.add_state(new_state_name)
        coords_to_states[coord] = new_state_name

    for action, coords in action_to_eligible_coords.items():
        for coord in coords:
            try:
                for transition in dfs.events[str(action)].transitions['0']:
                    if transition.source == '0':
                        original_target = transition.dest
            except KeyError:
                pass
            # Put the coord state in between
            dfs.add_transition("move_to_" + coords_to_states[coord], "0", coords_to_states[coord])
            dfs.add_transition(str(action), coords_to_states[coord], original_target)
            dfs.remove_transition(str(action))  # Remove the original

    return dfs
    # TODO create a state for every of all_eligible_coords
    # Then connect up the states with their respective actions by prepending them between the init state and the next state


def select_best_action(combatant, battle_map):
    fsm, transition_name_to_action = generate_action_fsm(combatant, battle_map)
    dfs = build_action_dfs(combatant, battle_map, fsm, transition_name_to_action)
    # TODO
    return dfs
