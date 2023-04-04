import copy

from simulator.actions.action_fsms import generate_action_fsm
from simulator.actions.actoid import ActoidFlags


def build_action_dfs(combatant, battle_map, action_fsm, transition_name_to_action):
    dfs = copy.deepcopy(action_fsm)

    # get eligible coords for all actions at depth == 1
    transition_names = action_fsm.get_available_transitions()
    transition_actions = [transition_name_to_action[t] for t in transition_names]
    action_to_eligible_coords = {a: a.get_eligible_coords(battle_map) for a in transition_actions if ActoidFlags.IS_POSITIONING_INDEPENDENT not in a.actoid_flags}
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
