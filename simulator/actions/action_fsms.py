import logging

import numpy as np

from statemachine import State, StateMachine

from simulator.abilities.wildshape import Wildshape
from simulator.actions.action_types import BonusAction
from simulator.feasibility import get_feasible_factories
from simulator.resources import use_resources
from simulator.utils.state_machine_template import StateMachineTemplate

logger = logging.getLogger("EncounTroll")



def actions_to_set(actions):
    return frozenset([str(f) for f in actions])


def get_all_feasible_action_factories(combatant, battle_map):
    """
    A helper functions which collects all feasible (bonus/haste) action factories for a combatant. Note that it excludes Misty Step which
    is resolved separately.
    :param combatant: for whom the feasible factories are is to be constructed
    :param battle_map:
    :return: all feasible (bonus/haste) action factories for a combatant
    """
    feasible_action_factories = get_feasible_factories(combatant.action_factories, combatant, battle_map)
    feasible_bonus_action_factories = [fbaf for fbaf in get_feasible_factories(combatant.bonus_action_factories, combatant, battle_map) if fbaf[0] is not BonusAction.MISTY_STEP]
    feasible_haste_action_factories = get_feasible_factories(combatant.haste_action_factories, combatant, battle_map)
    all_action_factories = feasible_action_factories
    all_action_factories.extend(feasible_bonus_action_factories)
    all_action_factories.extend(feasible_haste_action_factories)
    return all_action_factories


def generate_action_fsm(combatant, battle_map):
    """
    Builds a combatant-specific FSM which expresses all possible (bonus) action combinations the may take on their turn.
    It assumes the combatant's attack FSM is manually constructed already and is used as an input for the overall FSM.
    Misty Step gets a special treatment. We don't create states nor transitions for the Misty Step actions. We just note down which state
    the initial Misty Step would bring us into and pass it onto build_action_dag.
    :param combatant: for whom the FSM is to be constructed
    :param battle_map:
    :return: fsm, the mapping between FSM transition names to the actual action factory objects,
    list of actions that can be taken after misty step
    """
    fsm = StateMachineTemplate()
    state_footprint_to_state_name = dict()
    visited = set()
    transition_name_to_action = dict()
    post_misty_step_actions = None

    def dfs(subject, previous_state_name, af_to_a_mapping, action_taken=None):
        """
        Internal function which recursively builds the action FSM in a DFS manner
        """
        fafs = get_all_feasible_action_factories(subject, battle_map)
        fas = {a for faf in fafs for a in af_to_a_mapping[faf]}
        # A state is fully defined by all the possible (bonus) actions the combatant may take in it
        state_footprint = actions_to_set(fas)
        action_taken_name = str(action_taken)
        if action_taken:
            transition_name_to_action[action_taken_name] = action_taken

        if not state_footprint:
            # No more actions -> connect to the nop state
            fsm.add_transition(action_taken_name, previous_state_name, 'nop')
        elif state_footprint not in visited:
            # State not yet discovered, create a new state, remember the footprint and add transitions
            visited.add(state_footprint)
            curr_state_name = fsm.get_next_state_name()
            state_footprint_to_state_name[state_footprint] = curr_state_name
            if action_taken:
                fsm.add_new_state(curr_state_name)  # Avoid adding the initial state again
                fsm.add_transition(action_taken_name, previous_state_name, curr_state_name)
            for fa in fas:
                exported_resources = subject.export_resources()
                use_resources(subject, fa, battle_map)
                with subject.as_if_used_action_enabler(fa, battle_map) as did_transform:  # This covers Action Enablers in general
                    if did_transform:
                        with battle_map.replace_combatant_if_action_is_wildshape(fa, subject) as form:  # This covers wildshape being the current action
                            fafs = get_all_feasible_action_factories(form, battle_map)
                            af_to_a_used = {faf: faf[1].create_all(battle_map) for faf in fafs}
                            dfs(form, curr_state_name, af_to_a_used, fa)
                    else:
                        af_to_a_used = af_to_a_mapping
                        dfs(subject, curr_state_name, af_to_a_used, fa)
                subject.load_resources(exported_resources)
        else:
            # State already exists, just hook up the transition
            fsm.add_transition(action_taken_name, previous_state_name, state_footprint_to_state_name[state_footprint])

    # Optimization: the output of create_all doesn't change, only which factories are feasible changes => we can pre-compute them
    fafs = get_all_feasible_action_factories(combatant, battle_map)
    af_to_a = {faf: faf[1].create_all(battle_map) for faf in fafs}

    dfs(combatant, '0', af_to_a)

    # If the combatant has Misty Step, deal with it separately
    for fbaf in get_feasible_factories(combatant.bonus_action_factories, combatant, battle_map):
        if fbaf[0] is BonusAction.MISTY_STEP:
            ms = fbaf[1].create(np.array([0, 0]))  # coords don't matter here
            exported_resources = combatant.export_resources()
            use_resources(combatant, ms, battle_map)
            fafs = get_all_feasible_action_factories(combatant, battle_map)
            post_misty_step_actions = {str(a) for faf in fafs for a in af_to_a[faf]}
            combatant.load_resources(exported_resources)

    return fsm, transition_name_to_action, post_misty_step_actions


def generate_wildshape_action_fsm(combatant, battle_map):
    """
    A special variation of generate_action_fsm which generated an action FSM where the only allowed first action is a wildshape
    :param combatant: for whom the FSM is to be constructed
    :param battle_map:
    :return: fsm, the mapping between FSM transition names to the actual action factory objects,
    list of actions that can be taken after misty step
    """
    fsm = StateMachineTemplate()
    state_footprint_to_state_name = dict()
    visited = set()
    transition_name_to_action = dict()
    post_misty_step_actions = None

    def dfs(subject, previous_state_name, af_to_a_mapping, action_taken=None):
        """
        Internal function which recursively builds the action FSM in a DFS manner
        """
        fafs = get_all_feasible_action_factories(subject, battle_map)
        fas = {a for faf in fafs for a in af_to_a_mapping[faf]}
        # A state is fully defined by all the possible (bonus) actions the combatant may take in it
        state_footprint = actions_to_set(fas)
        action_taken_name = str(action_taken)
        if action_taken:
            transition_name_to_action[action_taken_name] = action_taken

        if not state_footprint:
            # No more actions -> connect to the nop state
            fsm.add_transition(action_taken_name, previous_state_name, 'nop')
        elif state_footprint not in visited:
            # State not yet discovered, create a new state, remember the footprint and add transitions
            visited.add(state_footprint)
            curr_state_name = fsm.get_next_state_name()
            state_footprint_to_state_name[state_footprint] = curr_state_name
            if action_taken:
                fsm.add_new_state(curr_state_name)  # Avoid adding the initial state again
                fsm.add_transition(action_taken_name, previous_state_name, curr_state_name)
            for fa in fas:
                if not action_taken and not isinstance(fa, Wildshape):
                    continue
                exported_resources = subject.export_resources()
                use_resources(subject, fa, battle_map)
                with subject.as_if_used_action_enabler(fa, battle_map) as did_transform:  # This covers Action Enablers in general
                    if did_transform:
                        with battle_map.replace_combatant_if_action_is_wildshape(fa, subject) as form:  # This covers wildshape being the current action
                            fafs = get_all_feasible_action_factories(form, battle_map)
                            af_to_a_used = {faf: faf[1].create_all(battle_map) for faf in fafs}
                            dfs(form, curr_state_name, af_to_a_used, fa)
                    else:
                        af_to_a_used = af_to_a_mapping
                        dfs(subject, curr_state_name, af_to_a_used, fa)
                subject.load_resources(exported_resources)
        else:
            # State already exists, just hook up the transition
            fsm.add_transition(action_taken_name, previous_state_name, state_footprint_to_state_name[state_footprint])

    # Optimization: the output of create_all doesn't change, only which factories are feasible changes => we can pre-compute them
    fafs = get_all_feasible_action_factories(combatant, battle_map)
    af_to_a = {faf: faf[1].create_all(battle_map) for faf in fafs}

    dfs(combatant, '0', af_to_a)

    return fsm, transition_name_to_action, post_misty_step_actions
