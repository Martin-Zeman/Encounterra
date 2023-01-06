from gymnasium import Env, spaces
from simulator.action_resolver import *
from simulator.resources import reset_resources
from simulator.effects.effect_tracker import EffectTracker
from simulator.misc import linex_loss, Size, Conditions
from simulator.combatant import Combatant
from sklearn.preprocessing import OrdinalEncoder, OneHotEncoder, LabelEncoder
import numpy as np
import logging

logger = logging.getLogger(__name__)

"""
Input should be concatenated states of K previous rounds. Both reset and step have to return those.

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
==> MultiDiscrete(np.array([self.actions.shape[0], max(battle_map.size, len(combatants)), max(battle_map.size, len(combatants))]))

Encoding of Faurung self:
[hp, has_action, has_bonus_action, has_reaction, x, y, [conditions affecting it], initiative(-4-40), attacks_left, ss1, ss2, ss3, sp]
sizes:
[1, 1, 1, 1, 1, 1, 15, 1, 1, 1, 1, 1, 1] -> 27

Encoding of the characters:
[#num, is_ally(0/1), health_condition(0-2), x, y, [conditions affecting it], initiative, has_action, has_bonus_action, has reaction, size(0-5)]
[1, 1, 1, 1, 1, 15, 1, 1, 1, 1, 1] -> 25

Encoding of the map:
[[terrain_type(1-3)...terrain_type(1-3)], ..., [terrain_type(1-3)...terrain_type(1-3)]]
map_size ** 2
"""


class FaurungEnv(Env):
    def __init__(self, combatants, teams, battle_map):
        super(FaurungEnv, self).__init__()

        self.actions = np.array(
            [MetaAction.DONE, Movement.STANDARD, Action.FIREBALL, Action.FIREBOLT, BonusAction.QUICKENED_FIREBALL, Action.CHAOSBOLT,
             Action.HASTE, Action.TWINNED_HASTE, Action.TWINNED_CHAOSBOLT, Action.TWINNED_FIREBOLT,
             BonusAction.MISTY_STEP, Reaction.SHIELD])
        faurung_observation_space = np.array([2000, 2, 2, 2, battle_map.size, battle_map.size, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 50, 4, 3, 2, 5])
        self.faurung_offset = faurung_observation_space.shape[0]
        combatant_observation_space = np.array([20, 2, len(Combatant.State), battle_map.size, battle_map.size, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 50, 2, 2, 2, len(Size)])
        self.combatant_offset = combatant_observation_space.shape[0]
        map_observation_space = np.array([len(Terrain)] * battle_map.size)
        self.observation_space = spaces.MultiDiscrete(np.concatenate((faurung_observation_space, combatant_observation_space, map_observation_space)))
        self.action_space = spaces.MultiDiscrete(np.array([self.actions.shape[0], max(battle_map.size, len(combatants)), max(battle_map.size, len(combatants))]))

        self.combatants = combatants
        self.teams = teams
        self.battle_map = battle_map
        self.effect_tracker = EffectTracker()
        self.action_resolver = ActionResolver(combatants, teams, battle_map, self.effect_tracker)
        self.combatant_initial_positions = {ch: self.battle_map.get_combatant_position(ch) for ch in self.combatants}
        self.trainee = None
        self.trainee_hp_end_of_round = None
        self.simulator_engine = None
        self.start_of_turn_hp = None

    def encode_obs(self):
        obs = np.zeros(self.observation_shape[0], dtype=int)
        obs[0] = self.trainee.curr_hp + 500
        obs[1:4] = np.array([self.trainee.has_action, self.trainee.has_bonus_action, self.trainee.has_reaction], dtype=int)
        obs[4:6] = self.battle_map.get_combatant_position(self.trainee).astype(int)
        ohe = OneHotEncoder()
        cnds = np.array([c.value for c in Conditions])
        ohe.fit(cnds.reshape(-1, 1))
        # encode all existing conditions as one hot vector, then do a bitwise or on them column-wise (summing them up)
        # the result will be a matrix of shape (1, #cnds) so we'll convert it into array and drop the extra dimension
        obs[6:21] = np.squeeze(np.asarray(ohe.transform(np.array([c.value for c in self.trainee.conditions]).reshape(-1, 1)).sum(axis=0))).astype(int)
        obs[21] = self.trainee.curr_init
        obs[22] = self.trainee.curr_num_attacks
        obs[23] = self.trainee.spellslots.get_spellslots(1)
        obs[24] = self.trainee.spellslots.get_spellslots(2)
        obs[25] = self.trainee.spellslots.get_spellslots(3)
        obs[26] = self.trainee.curr_sorcery_points
        offset = self.faurung_offset
        assert offset == 27
        assert self.combatant_offset == 25
        for i, combatant in enumerate(self.combatants):
            if combatant is self.trainee:
                continue
            obs[offset] = i  # TODO do I need this?
            obs[offset + 1] = 1 if self.team.are_allies(combatant, self.trainee) else 0
            obs[offset + 2] = combatant.condition.value
            obs[offset + 3:offset + 5] = self.battle_map.get_combatant_position(combatant).astype(int)
            obs[offset + 5:offset + 20] = np.squeeze(np.asarray(ohe.transform(np.array([c.value for c in self.trainee.conditions]).reshape(-1, 1)).sum(axis=0))).astype(int)
            obs[offset + 20] = combatant.curr_init
            obs[offset + 21:offset + 24] = np.array([self.trainee.has_action, self.trainee.has_bonus_action, self.trainee.has_reaction], dtype=int)
            obs[offset + 24] = combatant.size
            offset += self.combatant_offset
        obs[offset:] = self.battle_map.terrain_encoding.flatten()
        return obs

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
        for combatant in self.combatants:
            reset_resources(combatant)
        self.effect_tracker.reset()
        self.battle_map.reset()
        for combatant in self.combatants:
            # TODO consider making this part of map reset
            self.battle_map.set_combatant_coordinates(combatant, self.combatant_initial_positions[combatant])
        return self.encode_obs()

    def simulator(self):
        assert self.trainee is not None
        self.roll_initiative()
        self.order_by_initiative()
        logger.debug("--------------START--------------")
        while True:  # loop of turns, represents a combat session, i.e. one episode
            self.effect_tracker.new_turn()
            for combatant in self.combatants:
                if not combatant.is_alive():
                    if combatant is self.trainee:
                        break  # no point in training further in this combat
                    else:
                        continue
                combatant.new_turn()
                self.start_of_turn_hp = {c: c.curr_hp for c in self.combatants}
                effects = self.effect_tracker.get_all_affecting_combatant(combatant)
                self.action_resolver.resolve_effects(effects, combatant)
                if combatant.is_affected_by_any(Conditions.STUNNED, Conditions.PARALYZED, Conditions.PETRIFIED,
                                                Conditions.UNCONSCIOUS):
                    logger.debug(f"{combatant} is affected by a condition which prevents any action. Skipping turn")
                    continue
                while True:  # loop of a combatant's turn
                    try:
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

    def print_status(self):
        for combatant in self.combatants:
            status = f"alive with {combatant.curr_hp}" if combatant.is_alive() else "dead"
            logger.debug(f"Combatant {combatant} is {status}", extra={"team": self.teams.get_team(combatant)})
        logger.debug(self.battle_map)



    def compute_reward(self, result):
        reward = 0
        if result is ActionResult.UNFEASIBLE:
            reward -= 100
        elif result is ActionResult.FEASIBLE:
            reward += 10

        enemy_hp_loss = 0
        ally_hp_loss = 0
        for combatant in self.combatants:
            loss = percentage_hp_loss(self.start_of_turn_hp[combatant], combatant)
            if combatant is self.trainee:
                trainee_loss_of_hp = loss
            elif self.teams.are_enemies(combatant, self.trainee):
                enemy_hp_loss += loss
            else:
                ally_hp_loss += loss
        reward += enemy_hp_loss
        reward -= ally_hp_loss / 2
        reward -= trainee_loss_of_hp * 2

        # distance to nearest enemy, using linex loss function f(x)=-e^(x - 10) + 2(x -10) + 10
        _, dist = self.battle_map.get_nearest(self.trainee, Side.ENEMY)
        reward += linex_loss(dist)
        return reward

    def step(self, trainee_action):
        done = False

        self.simulator_engine.send(trainee_action)
        result = next(self.simulator_engine)
        reward = self.compute_reward(result)

        if self.is_only_one_team_standing():
            done = True
        obs = self.encode_obs()
        return obs, reward, done, {}

