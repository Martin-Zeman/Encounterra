# from simulator.action import Action
from simulator.attack import Attack
import random
import math
import logging

logger = logging.getLogger(__name__)

class Character:

    def __init__(self, name, actions, hp, ac, init_bonus, speed, resistances, num_attacks=1):
        self.name = name
        self.actions = actions
        # self.abilities = []
        self.spells = []
        self.max_hp = hp
        self.curr_hp = hp
        self.ac = ac
        self.init_bonus = init_bonus
        self.ability_dmg_bonus = 0
        self.curr_init = None
        self.has_action = True
        self.has_bonus_action = True
        self.has_reaction = True
        self.num_attacks = num_attacks
        self.curr_num_attacks = num_attacks
        self.movement = speed / 5
        self.resistances = resistances
        self.multiattack_in_progress = False
        self.team_name = ""

    def is_alive(self):
        return self.curr_hp > 0

    def roll_initiative(self):
        self.curr_init = random.randint(1, 20) + self.init_bonus

    def can_react(self):
        return self.has_reaction

    def __get_ability(self, name):
        # TODO: Consider making abilities a dict
        for ability in self.abilities:
            if ability.name == name:
                return ability
        return None

    def get_ability_dmg_bonus(self):
        return self.ability_dmg_bonus

    def set_ability_dmg_bonus(self, dmg_bonus):
        self.ability_dmg_bonus = dmg_bonus


    def receive_dmg(self, dmg, dmg_type):
        if dmg_type in self.resistances:
            dmg = math.floor(dmg/2)
            logger.debug(f"{self.name} is resistant to {dmg_type} and reduced the damage to {dmg}")
        self.curr_hp -= dmg

    def new_round(self):
        self.has_action = True
        self.has_bonus_action = True
        self.curr_num_attacks = self.num_attacks

    def get_name(self):
        return self.name

    def get_curr_hp(self):
        return self.curr_hp

    def get_curr_init(self):
        return self.curr_init

    def reset(self):
        self.has_action = True
        self.has_bonus_action = True
        self.curr_num_attacks = self.num_attacks
        self.curr_hp = self.max_hp
        for action in self.actions:
            action.reset()

    def add_team(self, team_name):
        self.team_name = team_name
