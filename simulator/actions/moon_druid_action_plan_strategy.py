import logging
import sys

import numpy as np

from ..actions.action_dag import generate_proto_dag, generate_wildshape_proto_dag
from ..actions.action_plan_strategy import ActionPlanStrategy
from ..actions.action_selector import find_best_sequence, build_action_dag, translate_sequence_to_actions
from ..actions.action_types import Action, BonusAction
from ..battle_map import Map

logger = logging.getLogger("Encounterra")

def evaluate_combination_eligibility(actions, transition_name_to_action):
    """
    A helper function which evaluates whether a non-wildshape action precedes a wildshape action in a list of actions.
    :param actions: sequence of actions as a list
    :param transition_name_to_action: dict mapping action names -> actions
    :return: True whether a combination is desired and the first non-wildshape action from the list if present
    """
    non_wildshape_action_idx = sys.maxsize
    wildshape_action_idx = 0
    for idx, action in enumerate(actions):
        try:
            if isinstance(transition_name_to_action[action].factory.action_type, Action):
                non_wildshape_action_idx = idx
                break
        except KeyError:
            continue
    for idx, action in enumerate(actions):
        try:
            if transition_name_to_action[action].factory.action_type is BonusAction.MOON_WILDSHAPE:
                wildshape_action_idx = idx
                break
        except KeyError:
            continue

    if non_wildshape_action_idx < wildshape_action_idx:
        return True, actions[non_wildshape_action_idx]
    elif non_wildshape_action_idx == sys.maxsize:
        return True, None
    return False, None

def get_moon_wildshape_action(action_plan):
    """
    A helper function which iterates through a list of actions and returns the moon wildshape it contains
    :param action_plan: a list of actions
    :return: moon wildshape action from the given list
    """
    for action in action_plan:
        try:
            if action.factory.action_type is BonusAction.MOON_WILDSHAPE:
                return action
        except KeyError:
            pass

class MoonDruidActionPlanStrategy(ActionPlanStrategy):

    def __init__(self, combatant):
        super().__init__(combatant)
        self.best_wildshape_plan_data = None


    def combine_action_plans(self, regular_action_plan, ws_action_plan, non_wildshape_action, distances, shortest_paths):
        """
        A helper function which combines the regular best action plan with the best wildshape plan.
        :param regular_action_plan: the best overall action plan
        :param ws_action_plan: the best action plan which starts with a wildshape
        :param non_wildshape_action: the first non-wildshape action from the regular action plan
        :param distances: potentially already pre-computed distances to all coords
        :param shortest_paths: potentially already pre-computed shortest paths to all coords
        :return: combined action plan
        """
        current_position = tuple(Map.get().get_combatant_position(self.combatant).get()[0])
        ws_movement_increments = [e.increment for e in ws_action_plan if hasattr(e, "increment")]
        sum_of_ws_increments = tuple(np.sum(ws_movement_increments, axis=0)) if ws_movement_increments else (0, 0)
        ws_destination = (current_position[0] + sum_of_ws_increments[0], current_position[1] + sum_of_ws_increments[1])
        try:
            if ws_destination in non_wildshape_action.get_eligible_coords(distances, shortest_paths):
                combined_plan = []
                combined_plan.extend(ws_action_plan[:len(ws_movement_increments)])
                combined_plan.append(non_wildshape_action)
                combined_plan.append(get_moon_wildshape_action(ws_action_plan))
                return combined_plan
        except TypeError:
            print("FIXME")
            non_wildshape_action.get_eligible_coords(distances, shortest_paths)
        return regular_action_plan

    def calculate_action_plan(self, distances, shortest_paths):
        """
        The point of this strategy is that it tries to combine the regular best result with the best wildshape result for a better result in
        the long-term. If a concentration spell is combined with a wildshape action then the wildshape action would only be evaluated based
        on its HP and its actions would not be taken into account. That's why a best wildshape plan is pre-computed and combined with the
        actual best plan in case the best plan contains a wildshape following a different kind of action.
        :param distances: potentially already pre-computed distances to all coords
        :param shortest_paths: potentially already pre-computed shortest paths to all coords
        :return: list of the following types: np.array, action, bonus action
        """
        if self.best_wildshape_plan_data is None:
            ws_fsm, ws_transition_name_to_action = generate_wildshape_proto_dag(self.combatant)
            if ws_transition_name_to_action:  # Could be out of wildshape uses
                ws_proto_dag, ws_movement_trans_to_coord_and_type, ws_transition_to_eligible_coords = build_action_dag(self.combatant, ws_fsm, ws_transition_name_to_action, distances, shortest_paths)
                if ws_proto_dag is not None:
                    ws_best_sequence, ws_transition_name_to_ms_path = find_best_sequence(self.combatant, ws_proto_dag, ws_transition_name_to_action, ws_transition_to_eligible_coords, ws_movement_trans_to_coord_and_type, distances, shortest_paths)
                    self.best_wildshape_plan_data = ws_transition_name_to_action, ws_movement_trans_to_coord_and_type, ws_best_sequence, ws_transition_name_to_ms_path

        # get_aoe_and_aoo_threat_for_increment.cache_clear()
        proto_dag, transition_name_to_action = generate_proto_dag(self.combatant)
        dag, movement_trans_to_coord_and_type, transition_to_eligible_coords = build_action_dag(self.combatant, proto_dag, transition_name_to_action, distances, shortest_paths)
        if dag is None:
            return None
        best_sequence, transition_name_to_ms_path = find_best_sequence(self.combatant, dag, transition_name_to_action, transition_to_eligible_coords, movement_trans_to_coord_and_type, distances, shortest_paths)
        if best_sequence is None:
            return None
        need_to_combine, non_wildshape_action = evaluate_combination_eligibility(best_sequence, transition_name_to_action)
        regular_plan = translate_sequence_to_actions(self.combatant, distances, shortest_paths, transition_name_to_action, movement_trans_to_coord_and_type, best_sequence, transition_name_to_ms_path)
        if need_to_combine:
            if self.best_wildshape_plan_data is not None:
                wildshape_plan = translate_sequence_to_actions(self.combatant, distances, shortest_paths, *self.best_wildshape_plan_data)
                if non_wildshape_action is None:
                    return wildshape_plan  # The case where there's only the wildshape left in the plan
                regular_plan = self.combine_action_plans(regular_plan, wildshape_plan, transition_name_to_action[non_wildshape_action], distances, shortest_paths)
        return regular_plan
