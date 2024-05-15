import logging

from .action_types import FreeAction
from .default_action_plan_strategy import DefaultActionPlanStrategy
from ..abilities.action_surge import ActionSurgeFactory
from ..actions.action_dag import generate_proto_dag
from ..actions.action_selector import find_best_sequence, build_action_dag, get_best_movement_and_action

logger = logging.getLogger("Encounterra")


class ActionSurgePlanStrategy(DefaultActionPlanStrategy):

    ACTION_SURGE_TOLERANCE_DELTA = 0.3

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
            if not self.combatant.is_planning_for_next_turn:
                self.combatant.is_planning_for_next_turn = True
                movement = None
                if self.combatant.movement > 0:  # Explore movement that could benefit next turn's action
                    logger.info("Exploring movement for next turn")
                    movement, _ = self.get_movement_and_threat_for_next_turn(distances, shortest_paths)
                if movement:
                    return movement
                elif not self.combatant.has_action and self.combatant.resources[FreeAction.ACTION_SURGE].has_resource() and self.combatant.weapon_dmg_dealt_this_turn > 0:
                    # Using a strict infeasibility_multiplier here to avoid wasting the Action Surge
                    _, max_threat = self.get_movement_and_threat_for_next_turn(distances, shortest_paths, 0)  # TODO check feasibility
                    if max_threat >= self.combatant.weapon_dmg_dealt_this_turn * self.ACTION_SURGE_TOLERANCE_DELTA:
                        return [ActionSurgeFactory(self.combatant).create(None)]
            return None
        best_sequence = get_best_movement_and_action(self.combatant, dag, distances, shortest_paths, transition_name_to_action, transition_to_eligible_coords, movement_trans_to_coord_and_type)
        if best_sequence is None:  # This happens e.g. if the only non-movement actions bring 0 threat
            if not self.combatant.has_action and self.combatant.resources[FreeAction.ACTION_SURGE].has_resource() and self.combatant.weapon_dmg_dealt_this_turn > 0:
                # Using a strict infeasibility_multiplier here to avoid wasting the Action Surge
                _, max_threat = self.get_movement_and_threat_for_next_turn(distances, shortest_paths, 0) # TODO check feasibility
                if max_threat >= self.combatant.weapon_dmg_dealt_this_turn * self.ACTION_SURGE_TOLERANCE_DELTA:
                    return [ActionSurgeFactory(self.combatant).create(None)]
            return None
        return best_sequence
