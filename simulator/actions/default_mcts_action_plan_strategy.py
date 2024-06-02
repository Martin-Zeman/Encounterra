import logging

import numpy as np

from .mcts_action_selector import get_best_mcts_movement_and_action
from ..actions.action_dag import generate_mcts_proto_dag
from ..actions.action_plan_strategy import ActionPlanStrategy
from ..actions.action_selector import find_best_sequence, REGEX_MOVEMENT_PATTERN, build_action_dag
from ..actions.action_types import Movement
from ..actions.movement import MovementGenerator
from ..battle_map import Map

logger = logging.getLogger("Encounterra")


class DefaultMCTSActionPlanStrategy(ActionPlanStrategy):

    def __init__(self, combatant, iterations=None, time_limit=None):
        super().__init__(combatant)
        self.iterations = iterations
        self.time_limit = time_limit

    def get_movement_and_threat_for_next_turn(self, distances, shortest_paths, infeasibility_multiplier=0.3):
        battle_map = Map.get()
        actions = []
        with self.combatant.as_if_has_action() as combatant:
            proto_dag, transition_name_to_action = generate_mcts_proto_dag(combatant)
            dag, movement_trans_to_coord_and_type, transition_to_eligible_coords = build_action_dag(combatant, proto_dag, transition_name_to_action, distances, shortest_paths)
            if dag is None:
                return actions, None

            best_sequence, transition_name_to_ms_path, max_threat = find_best_sequence(combatant, dag, transition_name_to_action, transition_to_eligible_coords, movement_trans_to_coord_and_type, distances, shortest_paths, infeasibility_multiplier)
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
        return actions, max_threat

    def calculate_action_plan(self, distances, shortest_paths):
        """
        Finds chain of movement, action and bonus action (not necessarily in that order) with the highest 'threat_out - threat_in'
        :param distances: potentially already pre-computed distances to all coords
        :param shortest_paths: potentially already pre-computed shortest paths to all coords
        :return: list of the following types: np.array, action, bonus action
        """
        proto_dag, transition_name_to_action = generate_mcts_proto_dag(self.combatant)
        dag, movement_trans_to_coord_and_type, transition_to_eligible_coords = build_action_dag(self.combatant, proto_dag, transition_name_to_action, distances, shortest_paths)
        if dag is None:
            if not self.combatant.is_planning_for_next_turn:
                self.combatant.is_planning_for_next_turn = True
                movement = None
                if self.combatant.movement > 0:  # Explore movement that could benefit next turn's action
                    logger.info("Exploring movement for next turn")
                    movement, _ = self.get_movement_and_threat_for_next_turn(distances, shortest_paths)
                return movement
            return None
        return get_best_mcts_movement_and_action(self.combatant, dag, distances, shortest_paths, transition_name_to_action, transition_to_eligible_coords, movement_trans_to_coord_and_type)
