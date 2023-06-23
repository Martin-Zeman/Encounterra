import logging

from toposort import toposort_flatten

from simulator.actions.action_fsms import generate_action_fsm
from simulator.actions.action_plan_strategy import ActionPlanStrategy
from simulator.actions.action_selector import longest_path, build_action_dag, translate_longest_pth_to_actions, extract_movement
from simulator.threat_utils import get_aoe_and_aoo_threat_for_increment

logger = logging.getLogger("EncounTroll")


class DefaultActionPlanStrategy(ActionPlanStrategy):

    def get_movement_for_next_turn(self, battle_map, distances, shortest_paths):
        # logger.info(f"{self.combatant} still has movement left")  # TODO FIXME
        with self.combatant.as_if_new_turn() as combatant:
            get_aoe_and_aoo_threat_for_increment.cache_clear()
            fsm, transition_name_to_action, post_misty_step_actions = generate_action_fsm(combatant, battle_map)
            fsm, transition_name_to_action, post_misty_step_actions = generate_action_fsm(combatant, battle_map)
            dag = build_action_dag(combatant, battle_map, fsm, transition_name_to_action, distances, shortest_paths,
                                   post_misty_step_actions)
            if dag is None:
                return None
            sorted_states = toposort_flatten(dag.dependencies)
            longest_pth, transition_name_to_ms_path = longest_path(combatant, battle_map, dag, sorted_states, transition_name_to_action,
                                                                   distances, shortest_paths)
            if longest_pth is None:
                return None
        return extract_movement(self.combatant, battle_map, distances, shortest_paths, longest_pth)

    def calculate_action_plan(self, battle_map, distances, shortest_paths):
        """
        Finds chain of movement, action and bonus action (not necessarily in that order) with the highest 'threat_out - threat_in'
        :param battle_map:
        :param distances: potentially already pre-computed distances to all coords
        :param shortest_paths: potentially already pre-computed shortest paths to all coords
        :return: list of the following types: np.array, action, bonus action
        """
        # start_time = time.time()
        get_aoe_and_aoo_threat_for_increment.cache_clear()
        fsm, transition_name_to_action, post_misty_step_actions = generate_action_fsm(self.combatant, battle_map)
        dag = build_action_dag(self.combatant, battle_map, fsm, transition_name_to_action, distances, shortest_paths, post_misty_step_actions)
        if dag is None:
            movement = None
            if self.combatant.movement > 0:  # Explore movement that could benefit next turn's action
                movement = self.get_movement_for_next_turn(battle_map, distances, shortest_paths)
            return movement
        sorted_states = toposort_flatten(dag.dependencies)
        longest_pth, transition_name_to_ms_path = longest_path(self.combatant, battle_map, dag, sorted_states, transition_name_to_action, distances, shortest_paths)
        if longest_pth is None:
            return None
        # logger.info(f"{self.combatant}'s plan {longest_pth}")# TODO FIXME
        # print("---get_action_plan took %s seconds ---" % (time.time() - start_time))
        return translate_longest_pth_to_actions(self.combatant, battle_map, distances, shortest_paths, transition_name_to_action, longest_pth, transition_name_to_ms_path)
