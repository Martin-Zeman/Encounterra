import logging

import numpy as np

from simulator.actions.action_fsms import generate_action_fsm
from simulator.actions.action_plan_strategy import ActionPlanStrategy
from simulator.actions.action_selector import find_best_sequence, build_action_dag, translate_sequence_to_actions, REGEX_MOVEMENT_PATTERN
from simulator.actions.action_types import Movement
from simulator.actions.movement import MovementGenerator
from simulator.battle_map import Map

logger = logging.getLogger("Encounterra")

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


class DefaultActionPlanStrategy(ActionPlanStrategy):

    def get_movement_for_next_turn(self, distances, shortest_paths):
        # logger.info(f"{self.combatant} still has movement left")  # TODO FIXME
        with self.combatant.as_if_has_action() as combatant:
            # get_aoe_and_aoo_threat_for_increment.cache_clear()
            fsm, transition_name_to_action = generate_action_fsm(combatant)
            dag, movement_trans_to_coord_and_type = build_action_dag(combatant, fsm, transition_name_to_action, distances, shortest_paths)
            if dag is None:
                return None
            best_sequence, transition_name_to_ms_path = find_best_sequence(combatant, dag, transition_name_to_action, movement_trans_to_coord_and_type, distances, shortest_paths)
            if best_sequence is None:
                return None
        return extract_movement(self.combatant, distances, shortest_paths, best_sequence)

    def calculate_action_plan(self, distances, shortest_paths):
        """
        Finds chain of movement, action and bonus action (not necessarily in that order) with the highest 'threat_out - threat_in'
        :param distances: potentially already pre-computed distances to all coords
        :param shortest_paths: potentially already pre-computed shortest paths to all coords
        :return: list of the following types: np.array, action, bonus action
        """
        # start_time = time.time()
        # get_aoe_and_aoo_threat_for_increment.cache_clear()
        fsm, transition_name_to_action = generate_action_fsm(self.combatant)
        dag, movement_trans_to_coord_and_type = build_action_dag(self.combatant, fsm, transition_name_to_action, distances, shortest_paths)
        if dag is None:
            movement = None
            if self.combatant.movement > 0:  # Explore movement that could benefit next turn's action
                movement = self.get_movement_for_next_turn(distances, shortest_paths)
            return movement
        best_sequence, transition_name_to_ms_path = find_best_sequence(self.combatant, dag, transition_name_to_action, movement_trans_to_coord_and_type, distances, shortest_paths)
        if best_sequence is None:
            return None
        # logger.info(f"{self.combatant}'s plan {longest_pth}")# TODO FIXME
        # print("---get_action_plan took %s seconds ---" % (time.time() - start_time))
        return translate_sequence_to_actions(self.combatant, distances, shortest_paths, transition_name_to_action, best_sequence, transition_name_to_ms_path)
