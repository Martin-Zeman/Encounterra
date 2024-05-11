import logging

import numpy as np

from ..actions.action_dag import generate_proto_tree
from ..actions.action_plan_strategy import ActionPlanStrategy
from ..actions.action_selector import find_best_sequence, REGEX_MOVEMENT_PATTERN, build_action_tree, get_best_movement_and_action
from ..actions.action_types import Movement
from ..actions.movement import MovementGenerator
from ..battle_map import Map

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

    def get_movement_and_threat_for_next_turn(self, distances, shortest_paths, infeasibility_multiplier=0.5):
        battle_map = Map.get()
        actions = []
        with self.combatant.as_if_has_action() as combatant:
            proto_tree, transition_name_to_action = generate_proto_tree(combatant)
            tree, movement_trans_to_coord_and_type, transition_to_eligible_coords = build_action_tree(combatant, proto_tree, transition_name_to_action, distances, shortest_paths)
            if tree is None:
                return actions, None

            best_sequence, transition_name_to_ms_path, _ = find_best_sequence(combatant, tree, transition_name_to_action, transition_to_eligible_coords, movement_trans_to_coord_and_type, distances, shortest_paths, infeasibility_multiplier)
            if not best_sequence:
                return actions, None
            for action in best_sequence:
                if action == "dummy":
                    continue
                match = REGEX_MOVEMENT_PATTERN.search(action)
                if match:
                    _, x, y = match.groups()
                    path = battle_map.get_path_to_coord(combatant, np.array([int(x), int(y)]), distances, shortest_paths, True)
                    movement_generator = MovementGenerator(combatant, path, Movement.STANDARD).get_generator()
                    actions.extend(list(movement_generator)[:self.combatant.movement])  # Unpack the movement generator
        return actions, None

    def calculate_action_plan(self, distances, shortest_paths):
        """
        Finds chain of movement, action and bonus action (not necessarily in that order) with the highest 'threat_out - threat_in'
        :param distances: potentially already pre-computed distances to all coords
        :param shortest_paths: potentially already pre-computed shortest paths to all coords
        :return: list of the following types: np.array, action, bonus action
        """
        proto_tree, transition_name_to_action = generate_proto_tree(self.combatant)
        tree, movement_trans_to_coord_and_type, transition_to_eligible_coords = build_action_tree(self.combatant, proto_tree, transition_name_to_action, distances, shortest_paths)
        if tree is None:
            movement = None
            if self.combatant.movement > 0:  # Explore movement that could benefit next turn's action
                movement, _ = self.get_movement_and_threat_for_next_turn(distances, shortest_paths)
            return movement
        # return translate_sequence_to_actions(self.combatant, distances, shortest_paths, transition_name_to_action, movement_trans_to_coord_and_type, best_sequence, transition_name_to_ms_path)
        return get_best_movement_and_action(self.combatant, tree, distances, shortest_paths, transition_name_to_action, transition_to_eligible_coords, movement_trans_to_coord_and_type)
