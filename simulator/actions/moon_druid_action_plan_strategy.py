import sys

import numpy as np
from toposort import toposort_flatten

from simulator.actions.action_fsms import generate_action_fsm, generate_wildshape_action_fsm
from simulator.actions.action_plan_strategy import ActionPlanStrategy
from simulator.actions.action_selector import longest_path, build_action_dag, translate_longest_pth_to_actions
from simulator.actions.action_types import Action, BonusAction
from simulator.threat_utils import get_aoe_and_aoo_threat_for_increment


def evaluate_combination_eligibility(actions, transition_name_to_action):
    """
    A helper function which evaluates whether a non-wildshape action precedes a wildshape action in a list of actions.
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


    def combine_action_plans(self, regular_action_plan, ws_action_plain, non_wildshape_action, battle_map, distances, shortest_paths):
        """
        A helper function which combines the regular best action plan with the best wildshape plan.
        :param regular_action_plan: the best overall action plan
        :param ws_action_plain: the best action plan which starts with a wildshape
        :param non_wildshape_action: the first non-wildshape action from the regular action plan
        :param battle_map:
        :param distances: potentially already pre-computed distances to all coords
        :param shortest_paths: potentially already pre-computed shortest paths to all coords
        :return: combined action plan
        """
        current_position = tuple(battle_map.get_combatant_position(self.combatant).get()[0])
        regular_movement_increments = [e.increment for e in regular_action_plan if hasattr(e, "increment")]
        regular_destination = current_position + tuple(np.sum(regular_movement_increments, axis=0)) if regular_movement_increments else (0, 0)
        ws_movement_increments = [e.increment for e in ws_action_plain if hasattr(e, "increment")]
        ws_destination = current_position + tuple(np.sum(ws_movement_increments, axis=0)) if ws_movement_increments else (0, 0)
        if ws_destination != regular_destination and ws_destination in non_wildshape_action.get_eligible_coords(battle_map, distances, shortest_paths):
            combined_plan = []
            combined_plan.extend(ws_action_plain[:len(ws_movement_increments)])
            combined_plan.append(non_wildshape_action)
            combined_plan.append(get_moon_wildshape_action(ws_action_plain))
            return combined_plan
        return regular_action_plan

    def calculate_action_plan(self, battle_map, distances, shortest_paths):
        """
        The point of this strategy is that it tries to combine the regular best result with the best wildshape result for a better result in
        the long-term. If a concentration spell is combined with a wildshape action then the wildshape action would only be evaluated based
        on its HP and its actions would not be taken into account. That's why a best wildshape plan is pre-computed and combined with the
        actual best plan in case the best plan contains a wildshape following a different kind of action.
        :param battle_map:
        :param distances: potentially already pre-computed distances to all coords
        :param shortest_paths: potentially already pre-computed shortest paths to all coords
        :return: list of the following types: np.array, action, bonus action
        """
        if self.best_wildshape_plan_data is None:
            ws_fsm, ws_transition_name_to_action, ws_post_misty_step_actions = generate_wildshape_action_fsm(self.combatant, battle_map)
            ws_dag = build_action_dag(self.combatant, battle_map, ws_fsm, ws_transition_name_to_action, distances, shortest_paths, ws_post_misty_step_actions)
            if ws_dag is not None:
                ws_sorted_states = toposort_flatten(ws_dag.dependencies)
                wildshape_path, ws_transition_name_to_ms_path = longest_path(self.combatant, battle_map, ws_dag, ws_sorted_states, ws_transition_name_to_action, distances, shortest_paths)
                self.best_wildshape_plan_data = wildshape_path, ws_transition_name_to_ms_path, ws_transition_name_to_action

        get_aoe_and_aoo_threat_for_increment.cache_clear()
        fsm, transition_name_to_action, post_misty_step_actions = generate_action_fsm(self.combatant, battle_map)
        dag = build_action_dag(self.combatant, battle_map, fsm, transition_name_to_action, distances, shortest_paths, post_misty_step_actions)
        if dag is None:
            return None
        sorted_states = toposort_flatten(dag.dependencies)
        longest_pth, transition_name_to_ms_path = longest_path(self.combatant, battle_map, dag, sorted_states, transition_name_to_action, distances, shortest_paths)
        if longest_pth is None:
            return None
        need_to_combine, non_wildshape_action = evaluate_combination_eligibility(longest_pth, transition_name_to_action)
        regular_plan = translate_longest_pth_to_actions(self.combatant, battle_map, distances, shortest_paths, transition_name_to_action, longest_pth, transition_name_to_ms_path)
        if need_to_combine:
            if self.best_wildshape_plan_data is not None:
                wildshape_plan = translate_longest_pth_to_actions(self.combatant, battle_map, distances, shortest_paths, self.best_wildshape_plan_data[2], self.best_wildshape_plan_data[0], self.best_wildshape_plan_data[1])
                if non_wildshape_action is None:
                    return [get_moon_wildshape_action(wildshape_plan)]  # The case where there's only the wildshape remaining from the plan
                regular_plan = self.combine_action_plans(regular_plan, wildshape_plan, transition_name_to_action[non_wildshape_action], battle_map, distances, shortest_paths)

        return regular_plan