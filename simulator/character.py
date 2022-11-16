from simulator.action import Action
import random


class Character:

    def __init__(self, name, attacks, hp, ac, init_bonus, speed, team, num_attacks=1):
        self.name = name
        self.attacks = attacks
        self.abilities = []
        self.spells = []
        self.max_hp = hp
        self.curr_hp = hp
        self.ac = ac
        self.init_bonus = init_bonus
        self.curr_init = random.randint(1, 20) + init_bonus
        self.action = True
        self.bonus_action = True
        self.reaction = True
        self.num_attacks = num_attacks
        self.team = team
        self.movement = speed / 5

    def is_alive(self):
        return self.curr_hp > 0

    def can_react(self):
        return self.reaction

    def get_action(self, battle_map):
        target_name = battle_map.get_nearest_enemy_name(self)
        action = Action(self.attacks[0], "sword attack", target_name)
        print(f"{self.name} uses action of type {action.get_type()} against {target_name}")
        return action

    def get_name(self):
        return self.name

    def get_curr_hp(self):
        return self.curr_hp

    def get_curr_init(self):
        return self.curr_init

    def get_team(self):
        return self.team