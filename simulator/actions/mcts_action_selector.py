import copy
import logging

import numpy as np

from .action_selector import decode_ms_path_to_actions
from .action_types import MovementThreatType, BonusAction, MOVEMENT_THREAT_TO_MOVEMENT
from .movement import MovementGenerator
from ..battle_map import Map
from .actoid import ActoidFlags
from .mcts import BaseState, MCTS
from ..misc import get_factory_of_type
from ..threat_interfaces import AttackThreatModifier
from ..threat_utils import accumulate_threat_along_path, calc_threat_for_path_with_misty_step


logger = logging.getLogger("Encounterra")


def get_best_mcts_movement_and_action(combatant, dag, distances, shortest_paths, transition_name_to_action, transition_to_eligible_coords, movement_trans_to_coord_and_type, stop_after_first=True):
    """
    Uses find_best_action to get the next movement and action
    :param combatant: the combatant
    :param dag: the action tree
    :param distances: potentially already pre-computed distances to all coords
    :param shortest_paths: potentially already pre-computed shortest paths to all coords
    :param transition_name_to_action: dictionary mapping of non-movement types to actions
    :param transition_to_eligible_coords: dictionary mapping of transition to eligible coordinates for that transition
    :param movement_trans_to_coord_and_type: mapping from movement transition -> coord, MovementThreatType
    :param stop_after_first: Should the sequence be cut after the first non-movement action?
    :return: list of the following types: np.array, action, bonus action
    """
    actions = []
    battle_map = Map.get()
    best_sequence, transition_name_to_ms_path, _ = find_best_mcts_sequence(combatant, dag, transition_name_to_action, transition_to_eligible_coords, movement_trans_to_coord_and_type, distances, shortest_paths)
    combatant.best_sequence = best_sequence
    if not best_sequence:  # TODO Can it return this?
        return None
    for transition in best_sequence:
        if transition == "dummy":
            continue  # TODO Can this still happen? Yes it can
        try:
            action = transition_name_to_action[transition]
            actions.append(action)
            if stop_after_first:
                break  # One non-movement action is enough, we need to recalculate anyway
        except KeyError:
            coord, movement_threat_type = movement_trans_to_coord_and_type[transition]
            path = battle_map.get_path_to_coord(combatant, np.array(coord), distances, shortest_paths, movement_threat_type != MovementThreatType.DISENGAGED)
            movement_generator = MovementGenerator(combatant, path, MOVEMENT_THREAT_TO_MOVEMENT[movement_threat_type]).get_generator()
            actions.extend(movement_generator)

            if movement_threat_type == MovementThreatType.MISTY_STEPPED:
                ms_factory = get_factory_of_type(combatant.bonus_action_factories, BonusAction.MISTY_STEP)
                decode_ms_path_to_actions(combatant, battle_map.get_combatant_position(combatant).get()[0], transition_name_to_ms_path[transition], actions, ms_factory)
    return actions


def find_best_mcts_sequence(combatant, dag, transition_name_to_action, transition_to_eligible_coords, movement_transition_to_coord_and_type, distances, shortest_paths, infeasibility_multiplier=0.5):
    """
    Finds the path through the DAG which represents the movement and actions with the highest calculated threat.
    We're taking advantage of the fact that as a result of the DFS traversal the coordinates in generated sequences are block-wise.
    Therefore, we can process the sequences by these coord-wise blocks and only call as_if_combatant_position once per block.
    To achieve this, coord_to_sequence_ids needs mapping between a target coordinate to all sequence ids which contain it, needs to be
    built.
    :param combatant: the combatant for whom the DAG is modeled
    :param dag: finite state machine representing all possible actions for combatant
    :param transition_name_to_action: dict mapping non-movement transition names -> action objects
    :param transition_to_eligible_coords: dict mapping non-movement transition names -> their eligible coordinates
    :param movement_transition_to_coord_and_type: dict mapping movement transition names -> target coord, MovementThreatType
    :param distances: potentially already pre-computed distances to all coords
    :param shortest_paths: potentially already pre-computed shortest paths to all coords
    :return: the best sequence MCTS was able to find
    """
    battle_map = Map.get()
    effect_to_coords = {e: e.get_affected_coords() for e in battle_map.effect_tracker.get_aoe_effects()}
    transition_name_to_ms_path = dict()
    current_coord = battle_map.get_combatant_position(combatant).get()[0]
    # sequence_to_threat = dict()  # Overall threat score of a sequence: sequence idx -> [movement threat, action threat]
    try:
        del movement_transition_to_coord_and_type[f"ms_({current_coord[0]}, {current_coord[1]})"]  # Removing Misty Step to current coordinate
    except KeyError:
        pass

    existing_attack_delta_effects = [eadf for eadf in battle_map.effect_tracker.get_affecting_combatant(combatant) if isinstance(eadf, AttackThreatModifier)]

    class MCTState(BaseState):

        def __init__(self, coord, movement_type, state_name, delta_action, first_feasibility_check_done=False, cumulative_threat=0, movement_threat=(0,)):
            BaseState.__init__(self)
            self.coord = coord
            self.movement_type = movement_type
            self.state_name = state_name
            self.delta_action = delta_action
            self.first_feasibility_check_done = first_feasibility_check_done
            self.cumulative_threat = cumulative_threat
            self.movement_threat = movement_threat
            self.node = None
            self.is_offensive = False
            self.current_path = []
            self.maximum_path = []

        def get_possible_actions(self) -> [any]:
            return [tx for tx, _ in dag.forward_transitions[self.state_name]]

        def take_action(self, mcts_action: any) -> 'BaseState':
            for tx, target_state in dag.forward_transitions[self.state_name]:
                if tx == mcts_action:
                    new_state = copy.copy(self)
                    try:
                        try:
                            new_state.coord, new_state.movement_type = movement_transition_to_coord_and_type[mcts_action]
                        except TypeError:
                            print("FIXME")
                        path = battle_map.get_path_to_coord(combatant, new_state.coord, distances, shortest_paths, True)
                        if path is not None:  # Note that an empty path is still a valid one
                            match new_state.movement_type:
                                case MovementThreatType.STANDARD:
                                    movement_threat = accumulate_threat_along_path(path, combatant, effect_to_coords)
                                case MovementThreatType.DISENGAGED:
                                    movement_threat = accumulate_threat_along_path(path, combatant, effect_to_coords, disengaged=True)
                                case MovementThreatType.DODGED:
                                    movement_threat = accumulate_threat_along_path(path, combatant, effect_to_coords, dodged=True)
                                case MovementThreatType.MISTY_STEPPED:
                                    movement_threat, misty_step_path = calc_threat_for_path_with_misty_step(path, combatant, effect_to_coords)  # TODO align this with accumulate_threat_along_path
                                    transition_name_to_ms_path["ms_" + str(new_state.coord)] = misty_step_path
                                case _:
                                    logger.error(f"Unknown movement type {new_state.movement_type}")
                                    movement_threat = accumulate_threat_along_path(path, combatant, effect_to_coords)
                            new_state.cumulative_threat += movement_threat[-1]
                            new_state.movement_threat = movement_threat
                    except KeyError:
                        pass
                    try:  # Is it a transition which represents a (bonus) action?
                        action = transition_name_to_action[mcts_action]
                        battle_map.clear_caches()
                        with battle_map.as_if_combatant_position(combatant, np.array(self.coord)):
                            with battle_map.replace_combatant_if_action_by_wildshaped(action, combatant, self.coord) as did_transform:
                                feasibility_multiplier = 1
                                if ActoidFlags.LOCATION_INDEPENDENT not in action.actoid_flags:
                                    if not self.first_feasibility_check_done:  # The first location-dependent action after movement has an eligible movement predecessor guaranteed
                                        try:
                                            feasibility_multiplier = 1 if distances[self.coord[0] * battle_map.size + self.coord[1]] <= combatant.movement else infeasibility_multiplier
                                        except TypeError:
                                            print("FIXME")
                                        new_state.first_feasibility_check_done = True
                                    else:  # Can only be > 1 since the movement is skipped with try-except
                                        eligible_coords = transition_to_eligible_coords[mcts_action]
                                        if not eligible_coords:
                                            continue  # e.g. when there's no place to hide
                                        if not self.first_feasibility_check_done:  # The case where a location-dependent action follows a location-independent action
                                            feasibility_multiplier = 1 if self.coord in eligible_coords and distances[self.coord[0] * battle_map.size + self.coord[1]] <= combatant.movement else infeasibility_multiplier
                                            new_state.first_feasibility_check_done = True
                                        else:  # Two location-dependent actions in succession
                                            remaining_dist = battle_map.get_hop_distance_coords(np.array(eligible_coords), np.array([self.coord]))  # This is a simplification, but good enough
                                            feasibility_multiplier = 1 if remaining_dist <= combatant.movement - distances[self.coord[0] * battle_map.size + self.coord[1]] else infeasibility_multiplier
                                threat = action.calculate_threat(consider_dist=(not did_transform), movement_threat=self.movement_threat)
                                if self.delta_action:
                                    delta_threat = self.delta_action.calculate_threat_for_attack(combatant, action)
                                    threat += delta_threat
                                    # sequence_idx_to_transition_step_threat[idx][delta_action_t_idx] += delta_threat
                                if isinstance(action, AttackThreatModifier):
                                    new_state.delta_action = action
                                    # delta_action_t_idx = t_idx
                                for existing_delta_effect in existing_attack_delta_effects:
                                    threat += existing_delta_effect.calculate_threat_for_attack(combatant, action)
                                threat *= feasibility_multiplier
                                if threat > 0:
                                    new_state.is_offensive = True
                                new_state.cumulative_threat += threat  # Overwrite the movement threat tuple with the final movement and transition total
                                new_state.cumulative_threat += 0.01 if np.array_equal(np.array(self.coord), current_coord) else 0  # Small bias towards current position prevents oscillations
                    except KeyError:  # or different kind which represents some type of movement
                        pass  # Skipping

                    new_state.state_name = target_state
                    return new_state
            return self  # TODO is this ok?

        def is_terminal(self) -> bool:
            return self.state_name not in dag.forward_transitions.keys()

        def get_reward(self) -> float:
            return self.cumulative_threat

    current_state = MCTState(current_coord, None, dag.state, None)
    searcher = MCTS(time_limit=combatant.action_plan_strategy.time_limit, iteration_limit=combatant.action_plan_strategy.iterations)
    best_sequence, max_threat = searcher.search(initial_state=current_state)
    # logger.info(f"{combatant}'s num DAG states: {len(dag.states)}")
    logger.info(f"{combatant}'s best sequence: {best_sequence} with threat: {max_threat}")
    return best_sequence, transition_name_to_ms_path, max_threat
