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
    def __init__(self, state, parent):
        self.state = state
        self.state.node = self
        self.is_terminal = state.is_terminal()
        self.parent = parent
        self.reward = 0.0
        self.children = {}

    def __str__(self):
        s = ["Reward: %s" % self.reward,
             "Movement Threat: %s" % self.state.movement_threat[-1],
             "Is Terminal: %s" % self.is_terminal,
             "Possible Actions: %s" % (self.children.keys())]
        return "%s: {%s}" % (self.__class__.__name__, ', '.join(s))


class MCTS:

    def __init__(self, time_limit: int = None, iteration_limit: int = None):
        self.root = None
        if time_limit is not None:
            if iteration_limit is not None:
                raise ValueError("Cannot have both a time limit and an iteration limit")
            # time taken for each MCTS search in milliseconds
            self.time_limit = time_limit
            self.limit_type = 'time'
        else:
            if iteration_limit is None:
                raise ValueError("Must have either a time limit or an iteration limit")
            # number of iterations of the search
            if iteration_limit < 1:
                raise ValueError("Iteration limit must be greater than one")
            self.search_limit = iteration_limit
            self.limit_type = 'iterations'
        self.rollout_policy = random_policy

    def search(self, initial_state: BaseState = None):
        self.root = TreeNode(initial_state, None)
        root_actions = self.root.state.get_possible_actions()
        for root_action in root_actions:
            new_state = self.root.state.take_action(root_action)
            self.root.children[root_action] = TreeNode(new_state, self.root)

        iterations = 0
        while iterations < self.search_limit:
            for root_action in root_actions:
                depth_one_node = self.root.children[root_action]
                reward = self.rollout_policy(depth_one_node.state)
                self.backpropagate(depth_one_node, reward)
                iterations += 1
                if iterations == self.search_limit:
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


    # def backpropagate(self, node: TreeNode, reward: float):
    #     if reward != -math.inf:
    #         while node:
    #             node.num_visits += 1
    #             if reward > node.reward:
    #                 node.state.maximum_path = copy.copy(node.state.current_path)
    #                 node.reward = reward
    #
    #             # Move to the first parent for the next iteration
    #             node = node.parents[0] if node.parents else None
    #     else:
    #         while node:
    #             node.num_visits += 1
    #             node.reward = -math.inf
    #             node = node.parents[0] if node.parents else None

    def backpropagate(self, node: TreeNode, reward: float):
        if reward != -math.inf:
            while node:
                if reward > node.reward:
                    # Only copy the path for non-root nodes where the reward is updated
                    if node.parent:
                        node.state.maximum_path = copy.copy(node.state.current_path)
                    node.reward = reward

                # Move to the first parent for the next iteration
                node = node.parent
        else:
            while node:
                node.reward = -math.inf
                node = node.parent

    def get_best_sequence(self, node: TreeNode):
        best_sequence = []
        current_node = node

        best_nodes_at_level_one = []
        best_value = -math.inf
        for child in current_node.children.values():
            node_value = child.reward
            if node_value > best_value:
                best_value = node_value
                best_nodes_at_level_one = [child]
            elif node_value == best_value:
                best_nodes_at_level_one.append(child)

        if len(best_nodes_at_level_one) > 1:
            best_node = random.choice(best_nodes_at_level_one)
        else:
            best_node = best_nodes_at_level_one[0]
        action = (action for action, node in current_node.children.items() if node is best_node).__next__()
        best_sequence.append(action)
        best_reward = best_node.reward
        best_sequence.extend(best_node.state.maximum_path)
        return best_sequence, best_reward
