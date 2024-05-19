from __future__ import division

import copy
import math
import random
import time

from abc import ABC, abstractmethod


class BaseState(ABC):
    """
    Baseclass for all states of a Monte Carlo Tree Search.

    This describes the state of the game/world, and the actions that can be taken from it.
    """

    @abstractmethod
    def get_possible_actions(self) -> [any]:
        """
        Returns a list of all possible actions that can be taken from this state.

        Returns
        -------
        [any]: a list of all possible actions that can be taken from this state
        """
        raise NotImplementedError()

    @abstractmethod
    def take_action(self, action: any) -> 'BaseState':
        """
        Returns the state that results from taking the given action.

        Parameters
        ----------
        action: [any] the action to take

        Returns
        -------
        BaseState: the state that results from taking the given action
        """
        raise NotImplementedError()

    @abstractmethod
    def is_terminal(self) -> bool:
        """
        Returns whether this state is a terminal state.

        Returns
        -------
        bool: whether this state is a terminal state
        """
        raise NotImplementedError()

    @abstractmethod
    def get_reward(self) -> float:
        """
        Returns the reward for this state. Only needed for terminal states.

        Returns
        -------
        float: the reward for this state
        """
        # only needed for terminal states
        raise NotImplementedError()


def random_policy(state: BaseState) -> float:
    state.current_path.clear()
    while not state.is_terminal():
        try:
            action = random.choice(state.get_possible_actions())
            state.current_path.append(action)
        except IndexError:
            raise Exception("Non-terminal state has no possible actions: " + str(state))
        state = state.take_action(action)
    reward = state.get_reward()
    return reward if state.is_offensive else -math.inf


class TreeNode:
    def __init__(self, state, parents):
        self.state = state
        self.state.node = self
        self.is_terminal = state.is_terminal()
        self.is_fully_expanded = self.is_terminal
        self.parents = parents
        self.num_visits = 0
        self.reward = 0.0
        self.children = {}

    def __str__(self):
        s = ["Reward: %s" % self.reward,
             "Movement Threat: %s" % self.state.movement_threat[-1],
             "Num Visits: %d" % self.num_visits,
             "Is Terminal: %s" % self.is_terminal,
             "Possible Actions: %s" % (self.children.keys())]
        return "%s: {%s}" % (self.__class__.__name__, ', '.join(s))


class MCTS:
    ITERATIONS = 1000
    EXPLORATION_CONSTANT = 2.0
    def __init__(self,
                 movement_transition_to_coord_and_type,
                 transition_to_eligible_coords,
                 time_limit: int = None,
                 iteration_limit: int = None,
                 rollout_policy=random_policy):
        self.movement_transition_to_coord_and_type = movement_transition_to_coord_and_type
        self.state_coord_to_state = dict()
        self.transition_to_eligible_coords = transition_to_eligible_coords
        self.normalizing_offset = 0

        self.root = None
        if time_limit is not None:
            if iteration_limit is not None:
                raise ValueError("Cannot have both a time limit and an iteration limit")
            # time taken for each MCTS search in milliseconds
            self.timeLimit = time_limit
            self.limit_type = 'time'
        else:
            if iteration_limit is None:
                raise ValueError("Must have either a time limit or an iteration limit")
            # number of iterations of the search
            if iteration_limit < 1:
                raise ValueError("Iteration limit must be greater than one")
            self.search_limit = iteration_limit
            self.limit_type = 'iterations'
        self.exploration_constant = MCTS.EXPLORATION_CONSTANT
        self.rollout_policy = rollout_policy

    def search(self, initialState: BaseState = None, initial_state: BaseState = None):
        initial_state = initialState if initial_state is None else initial_state
        self.root = TreeNode(initial_state, [])

        # First we expand all the nodes at depth=1, noting the minimum reward (which is negative) to be used as an offset later
        root_actions = self.root.state.get_possible_actions()
        depth_one_states = len(root_actions)*[None]  # Pre-allocation
        # lowest_depth_one_movement_threat = math.inf
        for idx, root_action in enumerate(root_actions):
            new_state = self.root.state.take_action(root_action)
            depth_one_states[idx] = new_state
            # if new_state.movement_threat[-1] < lowest_depth_one_movement_threat:
            #     lowest_depth_one_movement_threat = new_state.movement_threat[-1]
        # assert lowest_depth_one_movement_threat <= 0
        # self.normalizing_offset = -lowest_depth_one_movement_threat
        # At the same time, we build up the dict to deal with DAG's multiple parent case between depth 1 and 2
        for idx, root_action in enumerate(root_actions):
            depth_one_node = TreeNode(depth_one_states[idx], [self.root])
            self.root.children[root_action] = depth_one_node
            if root_action in self.movement_transition_to_coord_and_type.keys():
                self.state_coord_to_state[depth_one_states[idx].coord] = depth_one_states[idx]
            # if depth_one_node.state.coord[0] == 9 and (depth_one_node.state.coord[1] == 8 or depth_one_node.state.coord[1] == 7):
            #     print("FIXME")
            reward = self.rollout_policy(depth_one_node.state)# + self.normalizing_offset
            self.backpropogate(depth_one_node, reward)
        self.root.is_fully_expanded = True

        iterations = 0
        while iterations < MCTS.ITERATIONS:
            for root_action in root_actions:
                depth_one_node = self.root.children[root_action]
                reward = self.rollout_policy(depth_one_node.state)# + self.normalizing_offset
                # if reward >= 9.673592499999998:
                #     print("FIXME")
                self.backpropogate(depth_one_node, reward)
                iterations += 1
                if iterations == MCTS.ITERATIONS:
                    break

        # for i in range(MCTS.ITERATIONS):
        #     self.execute_round()
        # if self.limit_type == 'time':
        #     time_limit = time.time() + self.timeLimit / 1000
        #     while time.time() < time_limit:
        #         self.execute_round()
        # else:
        #     for i in range(self.search_limit):
        #         self.execute_round()

        return self.get_best_sequence(self.root)

    # def execute_round(self):
    #     """
    #         execute a selection-expansion-simulation-backpropagation round
    #     """
    #     node = self.select_node(self.root)
    #     reward = self.rollout_policy(node.state) + self.normalizing_offset
    #     self.backpropogate(node, reward)


    # def select_node(self, node: TreeNode) -> TreeNode:
    #     while not node.is_terminal:
    #         if node.is_fully_expanded:
    #             # Once they're all expanded, select one using the UCB1
    #             node = self.get_best_child(node, self.exploration_constant)
    #         else:
    #             # Unexpanded nodes have UCB1=inf, just expand them in order
    #             return self.expand(node)
    #     return node

    # def expand(self, node: TreeNode) -> TreeNode:
    #     actions = node.state.get_possible_actions()
    #     for action in actions:
    #         if action not in node.children:
    #             new_node = TreeNode(node.state.take_action(action), [node])
    #             if node in self.root.children.values():
    #                 for state_coord in self.transition_to_eligible_coords[action]:
    #                     try:
    #                         new_node.parents.append(self.state_coord_to_state[state_coord].node)
    #                     except KeyError:
    #                         pass  # For priority actions...
    #             node.children[action] = new_node
    #             if len(actions) == len(node.children):
    #                 node.is_fully_expanded = True
    #             return new_node
    #
    #     raise Exception("Should never reach here")

    def backpropogate(self, node: TreeNode, reward: float):
        if reward != -math.inf:
            while node:
                node.num_visits += 1
                if reward > node.reward:
                    node.state.maximum_path = copy.copy(node.state.current_path)
                    node.reward = reward

                # Update other parents if there are more than one
                # for parent in node.parents[1:]:
                #     parent.num_visits += 1
                #     parent.reward = max(parent.reward, reward)

                # Move to the first parent for the next iteration
                node = node.parents[0] if node.parents else None
        else:
            while node:
                node.num_visits += 1
                node.reward = -math.inf
                node = node.parents[0] if node.parents else None

    # def get_best_child(self, node: TreeNode, explorationValue: float, exploration_value: float = None) -> TreeNode:
    #     exploration_value = explorationValue if exploration_value is None else exploration_value
    #     best_value = -math.inf
    #     best_nodes = []
    #     for child in node.children.values():
    #         try:
    #             # node_value = child.totalReward / child.num_visits + exploration_value * math.sqrt(math.log(node.num_visits) / child.num_visits)
    #             node_value = child.reward + child.state.movement_threat[-1] + exploration_value * math.sqrt(child.num_visits) * math.sqrt(math.log(node.num_visits))
    #         except ValueError:
    #             print("FIXME")
    #         if node_value > best_value:
    #             best_value = node_value
    #             best_nodes = [child]
    #         elif node_value == best_value:
    #             best_nodes.append(child)
    #     return random.choice(best_nodes)

    def get_best_sequence(self, node: TreeNode):
        best_sequence = []
        current_node = node
        best_reward = -math.inf

        # while current_node.children.values():
        best_nodes_at_level = []
        best_value = -math.inf
        for child in current_node.children.values():
            node_value = child.reward# + child.state.movement_threat[-1]
            if node_value > best_value:
                best_value = node_value
                best_nodes_at_level = [child]
            elif node_value == best_value:
                best_nodes_at_level.append(child)

        if len(best_nodes_at_level) > 1:
            best_node = random.choice(best_nodes_at_level)
        else:
            best_node = best_nodes_at_level[0]
        action = (action for action, node in current_node.children.items() if node is best_node).__next__()
        best_sequence.append(action)
        # current_node = best_node
        best_reward = best_node.reward# + best_node.state.movement_threat[-1]
        best_sequence.extend(best_node.state.maximum_path)
        return best_sequence, best_reward
