# from simulator.action import Action
from simulator.attack import Attack
import random
import math

class Character:

    def __init__(self, name, actions, hp, ac, init_bonus, speed, resistances, team, num_attacks=1):
        self.name = name
        self.__actions = actions
        self.abilities = []
        self.spells = []
        self.max_hp = hp
        self.curr_hp = hp
        self.ac = ac
        self.init_bonus = init_bonus
        self.curr_init = random.randint(1, 20) + init_bonus
        self.__has_action = True
        self.__has_bonus_action = True
        self.__has_reaction = True
        self.__num_attacks = num_attacks
        self.__curr_num_attacks = num_attacks
        self.team = team
        self.movement = speed / 5
        self.__resistances = resistances
        self.__multiattack_in_progress = False

    def is_alive(self):
        return self.curr_hp > 0

    def can_react(self):
        return self.reaction

    def get_action(self, battle_map):
        attack = None
        target_name = battle_map.get_nearest_enemy_name(self)
        for action in self.__actions:
            if self.__has_action and not action.is_bonus():
                if self.__num_attacks and not self.__multiattack_in_progress:
                    self.__multiattack_in_progress = True
                if self.__curr_num_attacks and self.__multiattack_in_progress:
                    attack = action.get_instance()
                    attack.set_target_name(target_name)
                    self.__curr_num_attacks -= 1
                    print(f"{self.name} uses action {attack.get_name()} against {target_name}")
                    return attack
                else:
                    self.__has_action = False
                    self.__multiattack_in_progress = False
            elif self.__has_bonus_action and action.is_bonus():
                attack = action.get_instance()
                attack.set_target_name(target_name)
                self.__has_bonus_action = False
                print(f"{self.name} uses action {attack.get_name()} against {target_name}")
                return attack
        return attack

    def receive_dmg(self, dmg, dmg_type):
        if dmg_type in self.__resistances:
            dmg = math.floor(dmg/2)
            print(f"{self.name} is resistant to {dmg_type} and reduced the damage to {dmg}")
        self.curr_hp -= dmg

    def new_round(self):
        self.__has_action = True
        self.__has_bonus_action = True
        self.__curr_num_attacks = self.__num_attacks

    def get_name(self):
        return self.name

    def get_curr_hp(self):
        return self.curr_hp

    def get_curr_init(self):
        return self.curr_init

    def get_team(self):
        return self.team