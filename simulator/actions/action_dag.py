import logging
from contextlib import contextmanager

from .actoid import ActoidFlags
from ..abilities.wildshape import Wildshape
from ..actions.action_types import BonusAction
from ..battle_map import Map
from ..feasibility import get_feasible_factories
from ..misc import Size
from ..resources import use_resources
from ..utils.state_machine_template import StateMachineTemplate

logger = logging.getLogger("Encounterra")


def actions_to_set(actions):
    return frozenset(str(f) for f in actions)


@contextmanager
def replace_combatant_if_action_is_wildshape(action, combatant):
    """
    Replaces the combatant with the wildshaped form given by the action
    :param action:
    :param combatant:
    :return:
    """
    battle_map = Map.get()
    if isinstance(action, Wildshape):
        original_size = action.form.size
        try:
            battle_map.teams.replace_combatant(combatant, action.form)
            position = battle_map.get_combatant_position(combatant)
            action.form.size = Size.MEDIUM  # TODO this is a hack, making the form medium to make sure it fits
            battle_map.remove_combatant(combatant)
            battle_map.set_combatant_coordinates(action.form, position.get()[0])  # TODO shouldn't this also use find_wildshaped_coordinate
            yield action.form
        finally:
            action.form.size = original_size
            battle_map.teams.replace_combatant(action.form, combatant)
            position = battle_map.get_combatant_position(action.form)
            battle_map.remove_combatant(action.form)
            battle_map.set_combatant_coordinates(combatant, position.get()[0])
    else:
        yield combatant


@contextmanager
def replace_combatant_with_wildshape(form, combatant):
    """
    Replaces the combatant with the wildshaped form given by the action
    :param form:
    :param combatant:
    :return:
    """
    battle_map = Map.get()
    original_size = form.size
    try:
        battle_map.teams.replace_combatant(combatant, form)
        position = battle_map.get_combatant_position(combatant)
        form.size = Size.MEDIUM  # TODO this is a hack, making the form medium to make sure it fits
        battle_map.remove_combatant(combatant)
        battle_map.set_combatant_coordinates(form, position.get()[0])  # TODO shouldn't this also use find_wildshaped_coordinate
        yield form
    finally:
        form.size = original_size
        battle_map.teams.replace_combatant(form, combatant)
        position = battle_map.get_combatant_position(form)
        battle_map.remove_combatant(form)
        battle_map.set_combatant_coordinates(combatant, position.get()[0])


def get_all_feasible_action_factories(combatant, depth):
    """
    A helper functions which collects all feasible (bonus/haste) action factories for a combatant. Note that it excludes Misty Step which
    is resolved separately.
    :param combatant: for whom the feasible factories are is to be constructed
    :param battle_map:
    :param depth: depth in the FSM
    :return: all feasible (bonus/haste) action factories for a combatant
    """
    feasible_action_factories = get_feasible_factories(combatant.action_factories, combatant)
    if depth > 1:
        feasible_bonus_action_factories = [fbaf for fbaf in get_feasible_factories(combatant.bonus_action_factories, combatant) if fbaf[0] is not BonusAction.MISTY_STEP]
    else:
        feasible_bonus_action_factories = [fbaf for fbaf in get_feasible_factories(combatant.bonus_action_factories, combatant) if fbaf[0]]
    feasible_haste_action_factories = get_feasible_factories(combatant.haste_action_factories, combatant)
    all_action_factories = feasible_action_factories
    all_action_factories.extend(feasible_bonus_action_factories)
    all_action_factories.extend(feasible_haste_action_factories)
    return all_action_factories


def generate_proto_dag(combatant):
    """
    Builds a combatant-specific FSM which expresses all possible (bonus) action combinations the may take on their turn.
    It assumes the combatant's attack FSM is manually constructed already and is used as an input for the overall FSM.
    Misty Step gets a special treatment. We don't create states nor transitions for the Misty Step actions. We just note down which state
    the initial Misty Step would bring us into and pass it onto build_action_dag.
    :param combatant: for whom the FSM is to be constructed
    :return: fsm, the mapping between FSM transition names to the actual action factory objects
    """
    fsm = StateMachineTemplate()
    state_footprint_to_state_name = dict()
    visited = set()
    transition_name_to_action = dict()

    def dfs(subject, previous_state_name, af_to_a, depth, action_taken=None):
        """
        Recursively builds the action Finite State Machine (FSM) for a given combatant using depth-first search.

        This function traverses through all feasible action combinations, considering both actions and bonus actions,
        at each depth level. It creates states in the FSM for each unique combination of actions, connects states with transitions,
        and handles special cases like Action Enablers and wildshape actions.

        :param subject: The combatant for whom the FSM is being built.
        :param previous_state_name: The name of the previous state in the FSM.
        :param af_to_a: A dictionary mapping action factories to their corresponding actions.
        :param depth: The current depth in the action decision tree.
        :param action_taken: The action taken to reach the current state, if any.
        :return: None. The function works by side-effect, modifying the FSM directly.

        Note: This function assumes that it's called within the context of `generate_proto_dag`
        where the FSM and other necessary structures are initialized.
        """
        fafs = get_all_feasible_action_factories(subject, depth)
        try:
            fas = tuple(a for faf in fafs for a in af_to_a[faf])
        except KeyError:  # This can happen when the attack_fsm doesn't have all attacks types available from state 0
            af_to_a = {faf: faf[1].create_all() for faf in fafs}
            fas = tuple(a for faf in fafs for a in af_to_a[faf])
        # A state is fully defined by all the possible (bonus) actions the combatant may take in it
        state_footprint = actions_to_set(fas)
        action_taken_name = f"{action_taken}_{depth}"
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
                use_resources(subject, fa)
                with subject.as_if_used_action_enabler(fa) as action_enabler_used:  # This covers Action Enablers in general
                    if action_enabler_used:
                        with replace_combatant_if_action_is_wildshape(fa, subject) as form:  # This covers wildshape being the current action
                            fafs = get_all_feasible_action_factories(form, depth)
                            af_to_a_used = {faf: faf[1].create_all(action_taken) for faf in fafs}
                            dfs(form, curr_state_name, af_to_a_used, depth + 1, fa)
                    elif ActoidFlags.IS_ACTION_ENABLER in fa.actoid_flags:  # This should be more lightweight than inheritance
                        af_to_a_used = {faf: faf[1].create_all(fa) for faf in fafs}
                        dfs(subject, curr_state_name, af_to_a_used, depth + 1, fa)
                    else:
                        dfs(subject, curr_state_name, af_to_a, depth + 1, fa)
                subject.import_resources(exported_resources)
        else:
            # State already exists, just hook up the transition
            fsm.add_transition(action_taken_name, previous_state_name, state_footprint_to_state_name[state_footprint])

    # Optimization: the output of create_all doesn't change, only which factories are feasible changes => we can pre-compute them
    fafs = get_all_feasible_action_factories(combatant, 0)
    af_to_a = {faf: faf[1].create_all() for faf in fafs}

    dfs(combatant, '0', af_to_a, 0)

    return fsm, transition_name_to_action


def generate_wildshape_proto_dag(combatant):
    """
    A special variation of generate_proto_dag which generated an action FSM where the only allowed first action is a wildshape
    :param combatant: for whom the FSM is to be constructed
    :return: fsm, the mapping between FSM transition names to the actual action factory objects,
    list of actions that can be taken after misty step
    """
    fsm = StateMachineTemplate()
    state_footprint_to_state_name = dict()
    visited = set()
    transition_name_to_action = dict()

    def dfs(subject, previous_state_name, af_to_a, depth, action_taken=None):
        """
        Recursively builds the action Finite State Machine (FSM) for a given combatant using depth-first search.

        This function traverses through all feasible action combinations, considering both actions and bonus actions,
        at each depth level. It creates states in the FSM for each unique combination of actions, connects states with transitions,
        and handles special cases like Action Enablers and wildshape actions.

        :param subject: The combatant for whom the FSM is being built.
        :param previous_state_name: The name of the previous state in the FSM.
        :param af_to_a: A dictionary mapping action factories to their corresponding actions.
        :param depth: The current depth in the action decision tree.
        :param action_taken: The action taken to reach the current state, if any.
        :return: None. The function works by side-effect, modifying the FSM directly.

        Note: This function assumes that it's called within the context of `generate_proto_dag`
        where the FSM and other necessary structures are initialized.
        """
        fafs = get_all_feasible_action_factories(subject, depth,)
        fas = tuple(a for faf in fafs for a in af_to_a[faf])
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
                use_resources(subject, fa)
                with subject.as_if_used_action_enabler(fa) as action_enabler_used:  # This covers Action Enablers in general
                    if action_enabler_used:
                        with replace_combatant_if_action_is_wildshape(fa, subject) as form:  # This covers wildshape being the current action
                            fafs = get_all_feasible_action_factories(form, depth)
                            af_to_a_used = {faf: faf[1].create_all(action_taken) for faf in fafs}
                            dfs(form, curr_state_name, af_to_a_used, depth, fa)
                    elif ActoidFlags.IS_ACTION_ENABLER in fa.actoid_flags:  # This should be more lightweight than inheritance
                        af_to_a_used = {faf: faf[1].create_all(fa) for faf in fafs}
                        dfs(subject, curr_state_name, af_to_a_used, depth, fa)
                    else:
                        dfs(subject, curr_state_name, af_to_a, depth, fa)
                subject.import_resources(exported_resources)
        else:
            # State already exists, just hook up the transition
            fsm.add_transition(action_taken_name, previous_state_name, state_footprint_to_state_name[state_footprint])

    # Optimization: the output of create_all doesn't change, only which factories are feasible changes => we can pre-compute them
    fafs = get_all_feasible_action_factories(combatant, 0)
    af_to_a = {faf: faf[1].create_all() for faf in fafs}

    dfs(combatant, '0', af_to_a, 0)

    return fsm, transition_name_to_action
