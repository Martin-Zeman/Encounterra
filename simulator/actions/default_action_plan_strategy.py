import logging

import numpy as np

from ..actions.action_dag import generate_proto_dag
from ..actions.action_plan_strategy import ActionPlanStrategy
from ..actions.action_selector import find_best_sequence, build_action_dag, REGEX_MOVEMENT_PATTERN, \
    decode_ms_path_to_actions
from ..actions.action_types import Movement, MovementThreatType, BonusAction
from ..actions.movement import MovementGenerator
from ..battle_map import Map
from ..misc import get_factory_of_type

logger = logging.getLogger("Encounterra")


def translate_sequence_to_actions(combatant, distances, shortest_paths, transition_name_to_action, movement_trans_to_coord_and_type, sequence, transition_name_to_ms_path):
    """
    Translates the string form of the longest path back to action objects
    :param combatant: the combatant for whom the actions are translated
    :param distances: potentially already pre-computed distances to all coords
    :param shortest_paths: potentially already pre-computed shortest paths to all coords
    :param transition_name_to_action: dictionary mapping of non-movement types to actions
    :param movement_trans_to_coord_and_type: mapping from movement transition -> coord, MovementThreatType
    :param sequence: list of best actions as strings
    :param transition_name_to_ms_path: dictionary mapping of transition names to paths that may include a Misty Step (can be empty)
    :return: list of the following types: np.array, action, bonus action
    """
    actions = []
    battle_map = Map.get()
    for transition in sequence:
        if transition == "dummy":
            continue
        try:
            actions.append(transition_name_to_action[transition])
        except KeyError:
            coord, movement_type = movement_trans_to_coord_and_type[transition]
            match movement_type:
                case MovementThreatType.STANDARD | MovementThreatType.DODGED:
                    path = battle_map.get_path_to_coord(combatant,  np.array(coord), distances, shortest_paths, True)
                    movement_generator = MovementGenerator(combatant, path, Movement.STANDARD).get_generator()
                    actions.extend(movement_generator)  # Unpack the movement generator
                case MovementThreatType.DISENGAGED:
                    path = battle_map.get_path_to_coord(combatant, np.array(coord), distances, shortest_paths, False)
                    movement_generator = MovementGenerator(combatant, path, Movement.DISENGAGED).get_generator()
                    actions.extend(movement_generator)  # Unpack the movement generator
                case MovementThreatType.MISTY_STEPPED:
                    ms_factory = get_factory_of_type(combatant.bonus_action_factories, BonusAction.MISTY_STEP)
                    decode_ms_path_to_actions(combatant, battle_map.get_combatant_position(combatant).get()[0], transition_name_to_ms_path[transition], actions, ms_factory)
                    # TODO also unpack actions
                case _:
                    logger.error(f"Unknown movement type {movement_type}")
    return actions


class DefaultActionPlanStrategy(ActionPlanStrategy):

    def get_movement_and_threat_for_next_turn(self, distances, shortest_paths, infeasibility_multiplier=0.5):
        actions = []
        battle_map = Map.get()
        with self.combatant.as_if_has_action() as combatant:
            proto_dag, transition_name_to_action = generate_proto_dag(combatant)
            dag, movement_trans_to_coord_and_type, transition_to_eligible_coords = build_action_dag(combatant, proto_dag, transition_name_to_action, distances, shortest_paths)
            if dag is None:
                return None, None
            best_sequence, transition_name_to_ms_path, max_threat = find_best_sequence(combatant, dag, transition_name_to_action, transition_to_eligible_coords, movement_trans_to_coord_and_type, distances, shortest_paths, infeasibility_multiplier)
            if best_sequence is None:
                return None, None
            for action in best_sequence:
                if action == "dummy":
                    continue
                match = REGEX_MOVEMENT_PATTERN.search(action)
                if match:
                    _, x, y = match.groups()
                    path = battle_map.get_path_to_coord(combatant, np.array([int(x), int(y)]), distances, shortest_paths, True)
                    movement_generator = MovementGenerator(combatant, path, Movement.STANDARD).get_generator()
                    actions.extend(movement_generator)  # TODO: Align with MCTS?

        return actions, max_threat

    def calculate_action_plan(self, distances, shortest_paths):
        """
        Finds chain of movement, action and bonus action (not necessarily in that order) with the highest 'threat_out - threat_in'
        :param distances: potentially already pre-computed distances to all coords
        :param shortest_paths: potentially already pre-computed shortest paths to all coords
        :return: list of the following types: np.array, action, bonus action
        """
        proto_dag, transition_name_to_action = generate_proto_dag(self.combatant)
        dag, movement_trans_to_coord_and_type, transition_to_eligible_coords = build_action_dag(self.combatant, proto_dag, transition_name_to_action, distances, shortest_paths)
        if dag is None:
            movement = None
            if self.combatant.movement > 0:  # Explore movement that could benefit next turn's action
                movement, _ = self.get_movement_and_threat_for_next_turn(distances, shortest_paths)
            return movement
        best_sequence, transition_name_to_ms_path, _ = find_best_sequence(self.combatant, dag, transition_name_to_action, transition_to_eligible_coords, movement_trans_to_coord_and_type, distances, shortest_paths)
        if best_sequence is None:
            return None
        return translate_sequence_to_actions(self.combatant, distances, shortest_paths, transition_name_to_action, movement_trans_to_coord_and_type, best_sequence, transition_name_to_ms_path)
