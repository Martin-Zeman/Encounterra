from simulator.combatants.dragonclaw_cultist import DragonclawCultist
from simulator.combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from simulator.combatants.cyanwrath import Cyanwrath
from simulator.map import *
from simulator.round_manager import *
from simulator.teams import Teams
from RL.faurung_env import FaurungEnv
from RL.trainee_faurung import TraineeFaurung
from simulator.logging.log_formatter import LogFormatter
import os
import gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.evaluation import evaluate_policy

class TrainingSession:

    def __init__(self):
        self.combatants = []
        self.battle_map = None
        self.map_size = 15
        self.statistic_collector = None
        self.character_type_counter = {
            TraineeFaurung: 1,
            TotemBarbarian5Lvl: 1,
            DragonclawCultist: 1,
            Cyanwrath: 1
        }
        self.teams = Teams()
        self.battle_map = Map(self.map_size, self.teams)
        self.env = None
        self.trainee = None

    def add_combatant(self, combatant_type, team, is_trainee=False):
        try:
            curr_count = self.character_type_counter[combatant_type]
        except KeyError:
            logger.error("Unknown combatant type")
            return

        match combatant_type.__name__:
            case "TraineeFaurung":
                self.combatants.append(TraineeFaurung())
            case "TotemBarbarian5Lvl":
                self.combatants.append(TotemBarbarian5Lvl())
            case "Cyanwrath":
                self.combatants.append(Cyanwrath())
            case "DragonclawCultist":
                self.combatants.append(DragonclawCultist("DragonclawCultist " + str(curr_count)))
            case _:
                logger.error("Unknown combatant type")
                return
        if is_trainee:
            self.trainee = self.combatants[-1]
        self.character_type_counter[combatant_type] += 1
        self.teams.add_combatant_to_team(self.combatants[-1], team)

    def init_env(self):
        assert self.trainee is not None
        env = FaurungEnv(self.combatants, self.teams, self.battle_map)
        for combatant in self.combatants:
            combatant.set_round_manager(self.env)
        env.set_trainee(self.trainee)
        return env

    def test(self, num_episodes):
        env = self.init_env()

        for episode in range(1, num_episodes + 1):
            _ = env.reset()
            done = False
            score = 0

            while not done:
                # Take a random action
                action = env.action_space.sample()
                obs, reward, done, info = env.step(action)
                score += reward
            env.print_status()
            logger.info(f"Episode: {episode} Score: {score}")
        env.close()

    def simulate(self, num_episodes):
        env = self.init_env()
        model_load_path = os.path.join(os.getcwd(), 'saved_models', 'faurung.zip')
        model = PPO.load(model_load_path, env=env)

        for episode in range(1, num_episodes + 1):
            obs = env.reset()
            done = False
            score = 0

            while not done:
                action = model.predict(obs)
                obs, reward, done, info = env.step(action)
                score += reward
            env.print_status()
            logger.info(f"Episode: {episode} Score: {score}")
        env.close()

    def train(self, total_timesteps):
        env = self.init_env()

        log_path = os.path.join(os.getcwd(), 'logs')
        model_save_path = os.path.join(os.getcwd(), 'saved_models', 'faurung')
        model_load_path = os.path.join(os.getcwd(), 'saved_models', 'faurung.zip')

        env = DummyVecEnv([lambda: env])
        # model = PPO("MlpPolicy", env, verbose=2, tensorboard_log=log_path)
        model = PPO.load(model_load_path, env=env)

        model.learn(total_timesteps=total_timesteps)
        model.save(model_save_path)
        env.close()

    def evaluate(self):
        assert self.trainee is not None
        env = FaurungEnv(self.combatants, self.teams, self.battle_map)
        for combatant in self.combatants:
            combatant.set_round_manager(self.env)
        env.set_trainee(self.trainee)
        model_load_path = os.path.join(os.getcwd(), 'saved_models', 'faurung.zip')
        env = DummyVecEnv([lambda: env])
        model = PPO.load(model_load_path, env=env)
        result = evaluate_policy(model, env, n_eval_episodes=10, render=False)
        logger.info(result)
        env.close()


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setFormatter(LogFormatter())
    logger.addHandler(stdout_handler)
    session = TrainingSession()
    # session.add_combatant(Cyanwrath, Teams.Color.RED)
    # session.add_combatant(Faurung, Teams.Color.BLUE)
    session.add_combatant(TraineeFaurung, Teams.Color.BLUE, is_trainee=True)
    # session.add_combatant(TotemBarbarian5Lvl, Teams.Color.BLUE)
    session.add_combatant(DragonclawCultist, Teams.Color.RED)
    session.add_combatant(DragonclawCultist, Teams.Color.RED)
    session.add_combatant(DragonclawCultist, Teams.Color.RED)
    session.add_combatant(DragonclawCultist, Teams.Color.RED)
    session.train(90000)
    # session.evaluate()
    # session.simulate(1)