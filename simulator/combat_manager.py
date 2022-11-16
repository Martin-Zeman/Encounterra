from simulator.action import *
import random
from dpr_calculator import parse_dmg_dice

class CombatManager:

    def __init__(self, characters):
        self.characters = characters

    def resolve_action(self, action):
        target = None
        for character in self.characters:
            if character.get_name() == action.get_target_name():
                target = character

        if not target:
            print(f"No target found for action {action.get_name()}")
            return

        if action.get_type() != "ATTACK":
            print("Non-attack actions not supported yet")
            return

        # if self.hp <= 0:
        #     return False
        rolled = random.randint(1, 20)
        multiplier = 1
        if rolled == 1:
            print("Natural 1 rolled!")
            return
        elif rolled in action.get_attack().crit_range:
            multiplier = 2
        if rolled + action.get_attack().to_hit >= target.ac:
            num_dice, dice_size = parse_dmg_dice(action.get_attack().dmg_dice)
            dmg_dice_sum = 0
            for i in range(num_dice):
                dmg_dice_sum += random.randint(1, dice_size)
            total_dmg = multiplier * dmg_dice_sum + action.get_attack().dmg_bonus
            print(f"Attack hits for {total_dmg}")
            target.curr_hp -= total_dmg
