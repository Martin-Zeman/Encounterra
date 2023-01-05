import math

import gymnasium as gym
import random
from gym import Env, spaces
from simulator.action_resolver import *
from simulator.resources import reset_resources
from simulator.effects.effect_tracker import EffectTracker
from simulator.misc import linex_loss
from RL.trainee_faurung import TraineeFaurung
import logging

logger = logging.getLogger(__name__)

"""
Input should be concatenated states of K previous rounds. Both reset and step have to return those.

Encoding of Faurung self:
[hp, has_action, has_bonus_action, has_reaction, x, y, initiative(-4-40), attacks_left, ss1, ss2, ss3, sp]

Encoding of Barbarian self:
[hp, has_action, has_bonus_action, has_reaction, x, y, initiative(-4-40), size(0-5), attacks_left, num_rages, is_raging]

Encoding of the characters:
[#num, is_ally(0/1), health_condition(0-2), [conditions affecting it], x, y, size(0-5), initiative, has_action, has_bonus_action, has reaction]

Encoding of the map:
[x, y, obstacle_type(0-1)...x, y, obstacle_type(0-1)]

Encoding of actions Faurung:
DONE
Movement.STANDARD, x_inc, y_inc
Action.FIREBALL, x, y
Action.FIREBOLT, char#
BonusAction.QUICKENED_FIREBALL, x, y
Action.CHAOSBOLT, char#
Action.HASTE, char#
Action.TWINNED_HASTE, char#, char#
Action.TWINNED_CHAOSBOLT, char#, char#
Action.TWINNED_FIREBOLT, char#, char#
BonusAction.MISTY_STEP, x, y
Reaction.SHIELD
==> Tuple(Discrete(11), Discrete(max(map_size_,num_characters)), Discrete(max(map_size_,num_characters)))
"""


class FaurungEnv(Env):
    def __init__(self, combatants, teams, battle_map, num_rounds=30):
        super(FaurungEnv, self).__init__()

        self.actions = np.array(
            [MetaAction.DONE, Movement.STANDARD, Action.FIREBALL, Action.FIREBOLT, BonusAction.QUICKENED_FIREBALL, Action.CHAOSBOLT,
             Action.HASTE, Action.TWINNED_HASTE, Action.TWINNED_CHAOSBOLT, Action.TWINNED_FIREBOLT,
             BonusAction.MISTY_STEP, Reaction.SHIELD])

        self.action_space = spaces.Tuple(spaces.Discrete(self.actions.shape[0]),
                                         spaces.Discrete(max(battle_map.size, len(combatants))),
                                         spaces.Discrete(max(battle_map.size, len(combatants))))

        self.combatants = combatants
        self.teams = teams
        self.num_rounds = num_rounds
        self.battle_map = battle_map
        self.effect_tracker = EffectTracker()
        self.action_resolver = ActionResolver(combatants, teams, battle_map, self.effect_tracker)
        self.combatant_initial_positions = {ch: self.battle_map.get_combatant_position(ch) for ch in self.combatants}
        self.trainee = None
        self.trainee_hp_start_of_round = None
        self.trainee_hp_end_of_round = None
        self.simulator_engine = None

    def encode_obs(self):
        pass

    def set_trainee(self, trainee):
        assert trainee is not None
        self.trainee = trainee

    def roll_initiative(self):
        for combatant in self.combatants:
            combatant.roll_initiative()

    def order_by_initiative(self):
        def by_initiative(e):
            return e.curr_init

        self.combatants.sort(key=by_initiative, reverse=True)
        logger.debug("--------------INITIATIVE ORDER--------------")
        for combatant in self.combatants:
            logger.debug(f"{combatant} with {combatant.curr_init}")

    def goes_before_in_initiative(self, combatant1, combatant2):
        return True if self.combatants.index(combatant1) < self.combatants.index(combatant2) else False

    def is_only_one_team_standing(self):
        return True if len(self.teams.get_surviving_teams()) == 1 else False


    def reset(self):
        super(FaurungEnv, self).reset()
        self.simulator_engine = self.simulator()

    def soft_reset(self):
        """
        Performs a soft reset of the environment. Which means that it resets the state of the battlefield but does not
        call the reset of the environment
        """
        for combatant in self.combatants:
            reset_resources(combatant)
        self.effect_tracker.reset()
        self.battle_map.reset()
        for combatant in self.combatants:
            # TODO consider making this part of map reset
            self.battle_map.set_combatant_coordinates(combatant, self.combatant_initial_positions[combatant])


    def simulator(self):
        assert self.trainee is not None
        while True:  # loop over multiple combat sessions
            self.roll_initiative()
            self.order_by_initiative()
            logger.debug("--------------START--------------")
            while not self.is_only_one_team_standing():  # loop of turns, represents a combat session
                self.trainee_hp_start_of_round = trainee.curr_hp
                self.effect_tracker.new_turn()
                for combatant in self.combatants:
                    if not combatant.is_alive():
                        if combatant is self.trainee:
                            break  # no point in training further in this combat
                        else:
                            continue
                    combatant.new_turn()
                    effects = self.effect_tracker.get_all_affecting_combatant(combatant)
                    self.action_resolver.resolve_effects(effects, combatant)
                    while True:  # loop of a combatant's turn
                        try:
                            # TODO Need to accumulate dmg done to trainee?
                            if combatant is not self.trainee:
                                action, *args = combatant.get_action(self.battle_map)
                            else:
                                action, arg1, arg1 = yield
                        except TypeError as e:
                            logger.error(f"{combatant} threw {e} for action {action} with {args}")
                        if action is MetaAction.DONE:
                            break
                        if combatant is not self.trainee:
                            self.action_resolver.resolve_action(action, args, combatant)
                        else:
                            yield self.action_resolver.resolve_action_train(action, arg1, arg2, combatant)
                        if not combatant.is_alive():
                            break  # could have died as a result of AoO
                    else:
                        logger.debug(f"Combatant {combatant} is dead. Skipping")
                self.trainee_hp_end_of_round = trainee.curr_hp
                self.print_status()
            self.soft_reset()

    def print_status(self):
        for combatant in self.combatants:
            status = f"alive with {combatant.curr_hp}" if combatant.is_alive() else "dead"
            logger.debug(f"Combatant {combatant} is {status}", extra={"team": self.teams.get_team(combatant)})
        logger.debug(self.battle_map)



    def compute_reward(self, result):
        reward = 0
        # percentage divided by ten -> (0, 10)
        loss_of_hp = 10 * (self.trainee_hp_start_of_round - max(0, self.trainee_hp_end_of_round)) / self.trainee.max_hp
        reward -= loss_of_hp

        # distance to nearest enemy, using linex loss function f(x)=-e^(x - 10) + 2(x -10) + 10
        _, dist = self.battle_map.get_nearest(self.trainee, Side.ENEMY)
        reward += linex_loss(dist)

        # dmg inflicted
        # TODO instead of evaluating the action of the trainee consider just evaluating pre and post-turn status of enemies and allies (% hp loss, CCs)
        reward += result.total_dmg_inflicted

        # TODO add any potential CCs landed
        pass
    def step(self, trainee_action):
        self.simulator_engine.send(trainee_action)
        result = next(self.simulator_engine)
        reward = self.compute_reward(result)
        # TODO encode state as obs
        return obs, reward, done, {}

