from __future__ import division

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


NORMALIZATION_CONSTANT = 100


def random_policy(state: BaseState) -> float:
    while not state.is_terminal():
        try:
            action = random.choice(state.get_possible_actions())
        except IndexError:
            raise Exception("Non-terminal state has no possible actions: " + str(state))
        state = state.take_action(action)
    reward = state.get_reward() + NORMALIZATION_CONSTANT  # This is to make sure that all sequences have positive rewards
    return reward if state.is_offensive else -math.inf


class TreeNode:
    def __init__(self, state, parents):
        self.state = state
        self.state.node = self
        self.is_terminal = state.is_terminal()
        self.is_fully_expanded = self.is_terminal
        self.parents = parents
        self.numVisits = 0
        self.totalReward = 0
        self.children = {}

    def __str__(self):
        s = ["totalReward: %s" % self.totalReward,
             "numVisits: %d" % self.numVisits,
             "isTerminal: %s" % self.is_terminal,
             "possibleActions: %s" % (self.children.keys())]
        return "%s: {%s}" % (self.__class__.__name__, ', '.join(s))


class MCTS:
    def __init__(self,
                 movement_transition_to_coord_and_type,
                 transition_to_eligible_coords,
                 time_limit: int = None,
                 timeLimit=None,
                 iteration_limit: int = None,
                 iterationLimit=None,
                 exploration_constant: float = None,
                 explorationConstant=math.sqrt(2),
                 rollout_policy=None,
                 rolloutPolicy=random_policy):
        self.movement_transition_to_coord_and_type = movement_transition_to_coord_and_type
        self.state_name_to_state = dict()
        self.transition_to_eligible_coords = transition_to_eligible_coords
        # backwards compatibility
        time_limit = timeLimit if time_limit is None else time_limit
        iteration_limit = iterationLimit if iteration_limit is None else iteration_limit
        exploration_constant = explorationConstant if exploration_constant is None else exploration_constant
        rollout_policy = rolloutPolicy if rollout_policy is None else rollout_policy

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
        self.exploration_constant = exploration_constant
        self.rollout_policy = rollout_policy

    def search(self, initialState: BaseState = None, initial_state: BaseState = None):
        initial_state = initialState if initial_state is None else initial_state
        self.root = TreeNode(initial_state, [])

        root_actions = self.root.state.get_possible_actions()
        for root_action in root_actions:
            depth_one_state = self.root.state.take_action(root_action)
            depth_one_node = TreeNode(depth_one_state, [self.root])
            self.root.children[root_action] = depth_one_node
            if root_action in self.movement_transition_to_coord_and_type.keys():
                self.state_name_to_state[depth_one_state.state_name] = depth_one_state
            reward = self.rollout_policy(depth_one_node.state)
            self.backpropogate(depth_one_node, reward)
        self.root.is_fully_expanded = True

        if self.limit_type == 'time':
            time_limit = time.time() + self.timeLimit / 1000
            while time.time() < time_limit:
                self.execute_round()
        else:
            for i in range(self.search_limit):
                self.execute_round()

        return self.get_best_sequence(self.root, 0)

    def execute_round(self):
        """
            execute a selection-expansion-simulation-backpropagation round
        """
        node = self.select_node(self.root)
        reward = self.rollout_policy(node.state)
        self.backpropogate(node, reward)

    def select_node(self, node: TreeNode) -> TreeNode:
        while not node.is_terminal:
            if node.is_fully_expanded:
                # One they're all expanded, select one using the UCB1
                node = self.get_best_child(node, self.exploration_constant)
            else:
                # Until all children had been expanded, keep picking a random one
                return self.expand(node)
        return node

    def expand(self, node: TreeNode) -> TreeNode:
        actions = node.state.get_possible_actions()
        for action in actions:
            if action not in node.children:
                new_node = TreeNode(node.state.take_action(action), [node])
                if node in self.root.children:
                    for coord_state_names in self.transition_to_eligible_coords[action]:
                        for coord_state_name in coord_state_names:
                            new_node.parents.append(self.state_name_to_state[coord_state_name].node)
                node.children[action] = new_node
                if len(actions) == len(node.children):
                    node.is_fully_expanded = True
                return new_node

        raise Exception("Should never reach here")

    def backpropogate(self, node: TreeNode, reward: float):
        if reward != -math.inf:
            while True:
                node.numVisits += 1
                node.totalReward += reward
                if len(node.parents) > 1:
                    for parent in node.parents[1:]:
                        parent.totalReward += reward
                if not node.parents:
                    break
                node = node.parents[0]
        else:
            while node.parents:
                node.numVisits += 1
                node.totalReward += reward
                if not node.parents:
                    break
                node = node.parents[0]

    def get_best_child(self, node: TreeNode, explorationValue: float, exploration_value: float = None) -> TreeNode:
        exploration_value = explorationValue if exploration_value is None else exploration_value
        best_value = float("-inf")
        best_nodes = []
        for child in node.children.values():
            node_value = child.totalReward / child.numVisits + exploration_value * math.sqrt(math.log(node.numVisits) / child.numVisits)
            if node_value > best_value:
                best_value = node_value
                best_nodes = [child]
            elif node_value == best_value:
                best_nodes.append(child)
        return random.choice(best_nodes)

    def get_best_sequence(self, node: TreeNode, explorationValue: float, exploration_value: float = None):
        # Now the problem is that the best sequences seem to have the lowest reward. Why? Because we keep iterating on the same ones for a long time and their rewards are negative so they keep adding up.
        exploration_value = explorationValue if exploration_value is None else exploration_value
        best_sequence = []
        current_node = node

        while current_node.children.values():
            best_nodes_at_level = []
            best_value = float("-inf")
            for child in current_node.children.values():
                node_value = child.totalReward / child.numVisits + exploration_value * math.sqrt(math.log(current_node.numVisits) / child.numVisits)
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
            current_node = best_node
        return best_sequence
