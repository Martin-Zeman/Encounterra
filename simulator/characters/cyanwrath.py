from simulator.character import Character
from simulator.attack import Attack
from simulator.dodge import Dodge
from simulator.action import Action
from simulator.movement import Movement, MovementGenerator
import numpy as np
import logging
import copy

logger = logging.getLogger(__name__)

class Cyanwrath(Character):

    def __init__(self):
        cyanwrath_attacks = [Attack("Polearm", self, 7, "1d10", 4, Action.ActionClasses.ACTION, "Slashing", 2, [19, 20]),
                             Attack("Butt end of Polearm", self, 7, "1d4", 4, Action.ActionClasses.BONUS_ACTION, "Bludgeoning", 2, [19, 20])]
        super().__init__("Cyanwrath", cyanwrath_attacks, 95, 17, 1, 30, ["Lightning"], num_attacks=2)
        self.basic_attack_cache = cyanwrath_attacks[0]# just a helper
        self.bonus_attack_cache = cyanwrath_attacks[1]# just a helper
        self.max_melee_range = 2 # TODO: maybe add a lookup here
        self.has_polearm_master = True
        self.has_sentinel = True

    def attack_routine(self, battle_map):
        if battle_map.are_in_range(self, self.selected_target, self.max_melee_range):
            attack = self.basic_attack_cache
            bonus_attack = self.bonus_attack_cache
            logger.debug("Is in range")
            if self.has_action and self.num_attacks and not self.multiattack_in_progress:
                self.multiattack_in_progress = True
                self.has_action = False
            if self.curr_num_attacks and self.multiattack_in_progress:
                attack.set_target_character(self.selected_target)
                self.curr_num_attacks -= 1
                logger.debug(f"{self.name} uses action {attack.get_name()} against {self.selected_target.get_name()}",
                             extra={"team": self.team_name})
                return attack
            else:
                self.multiattack_in_progress = False
            if self.has_bonus_action and self.curr_num_attacks < self.num_attacks:  # if already took the attack action
                bonus_attack.set_target_character(self.selected_target)
                self.has_bonus_action = False
                logger.debug(
                    f"{self.name} uses action {bonus_attack.get_name()} against {self.selected_target.get_name()}",
                    extra={"team": self.team_name})
                return bonus_attack
        else:
            logger.debug("Is out of range")
            return None

    def get_action(self, battle_map):
        while self.has_action or self.has_bonus_action or self.movement:
            logger.debug(f"Has action {self.has_action}, has_bonus action {self.has_bonus_action}, movement {self.movement}")
            # chosen_action = None

            if self.selected_target is None or not self.selected_target.is_alive():
                # Get new target
                self.selected_target = battle_map.get_nearest_enemy(self)
                if not self.selected_target:
                    return None

            target_position = battle_map.get_character_position(self.selected_target.get_name())
            logger.debug(f"Target is at {target_position} and my cache is {None if self.target_position_cache is None else self.target_position_cache}")
            dist = battle_map.get_character_distance(self, self.selected_target)
            if self.movement and self.has_action and dist > 2:
                # I haven't attacked yet and I'm too far away, move into pole-arm range
                path = battle_map.get_path_to_enemy(self, self.selected_target)
                self.movement_generator = MovementGenerator(self, Movement.STANDARD, path, True).get_generator()
                try:
                    movement = next(self.movement_generator)
                    logger.debug("Moving")
                    return movement
                except StopIteration:
                    pass #can't go any farther
            elif (self.has_action or self.multiattack_in_progress) and dist <= 2:
                # if I'm in range and I still have an action then attack
                attack = self.attack_routine(battle_map)
                if attack:
                    return attack
            elif self.movement and not self.has_action and dist <= 2:
                # If I'm in range but no longer have an action then I want to step away
                free_coords = battle_map.get_free_positions_at_distance(self.selected_target, 3, self)
                if free_coords:
                    path = battle_map.get_path_to_coord(self, free_coords[0])
                    self.movement_generator = MovementGenerator(self, Movement.STANDARD, path, True).get_generator()
                    try:
                        movement = next(self.movement_generator)
                        logger.debug("Moving")
                        return movement
                    except StopIteration:
                        pass  # can't go any farther

            # if not np.array_equal(self.target_position_cache, target_position):
            #     path = battle_map.get_path_to_enemy(self, self.selected_target)
            #     self.movement_generator = MovementGenerator(self, Movement.STANDARD, path, True).get_generator()
            #     self.target_position_cache = target_position
            #
            # if not battle_map.are_in_range(self, self.selected_target, self.max_melee_range):
            #     logger.debug("Not in range")
            #     try:
            #         movement = next(self.movement_generator)
            #         logger.debug("Moving")
            #         return movement
            #     except StopIteration:
            #         pass #can't go any farther
            # if battle_map.are_in_range(self, self.selected_target, 1) or not battle_map.are_in_range(self, self.selected_target, 3):
            #     # If I'm either too close or too far move to distance 3
            #     free_coords = battle_map.get_free_positions_at_distance(self.selected_target, 3, self)
            #     if free_coords:
            #         path = battle_map.get_path_to_coord(self, free_coords[0])
            #         self.movement_generator = MovementGenerator(self, Movement.STANDARD, path, True).get_generator()
            #         self.target_position_cache = target_position

            # target_position = battle_map.get_character_position(self.selected_target.get_name())
            # logger.debug(f"Target is at {target_position} and my cache is {None if self.target_position_cache is None else self.target_position_cache}")
            # if not np.array_equal(self.target_position_cache, target_position):
            #     path = battle_map.get_path_to_enemy(self, self.selected_target)
            #     self.movement_generator = MovementGenerator(self, Movement.STANDARD, path, True).get_generator()
            #     self.target_position_cache = target_position
            #
            # if not battle_map.are_in_range(self, self.selected_target, self.max_melee_range):
            #     logger.debug("Not in range")
            #     try:
            #         movement = next(self.movement_generator)
            #         logger.debug("Moving")
            #         return movement
            #     except StopIteration:
            #         pass #can't go any farther
            # elif battle_map.are_in_range(self, self.selected_target, 1):
            #     free_coords = battle_map.get_free_positions_at_distance(self.selected_target, 3, self)
            #     if free_coords:
            #         path = battle_map.get_path_to_coord(self, free_coords[0])
            #         self.movement_generator = MovementGenerator(self, Movement.STANDARD, path, True).get_generator()
            #         self.target_position_cache = target_position

            # if battle_map.are_in_range(self, self.selected_target, self.max_melee_range):
            #     attack = self.basic_attack_cache
            #     bonus_attack = self.bonus_attack_cache
            #     logger.debug("Is in range")
            #     if self.has_action and self.num_attacks and not self.multiattack_in_progress:
            #         self.multiattack_in_progress = True
            #         self.has_action = False
            #     if self.curr_num_attacks and self.multiattack_in_progress:
            #         self.attack.set_target_character(self.selected_target)
            #         self.curr_num_attacks -= 1
            #         logger.debug(f"{self.name} uses action {attack.get_name()} against {self.selected_target.get_name()}", extra={"team": self.team_name})
            #         return attack
            #     else:
            #         self.multiattack_in_progress = False
            #     if self.has_bonus_action and self.curr_num_attacks < self.num_attacks:# if already took the attack action
            #         bonus_attack.set_target_character(self.selected_target)
            #         self.has_bonus_action = False
            #         logger.debug(f"{self.name} uses action {bonus_attack.get_name()} against {self.selected_target.get_name()}", extra={"team": self.team_name})
            #         return bonus_attack
            # else:
            #     logger.debug("Is out of range")
            # return chosen_action
            if self.has_action:
                logger.debug(f"{self.name} uses the dodge action", extra={"team": self.team_name})
                self.has_action = False
                return Dodge("dodge", self, Action.ActionClasses.ACTION)
            return None

    def prompt_aoo(self, moving_character):
        #only use it if I go before my selected target in initiative so that I can move away and use sentinel+pam
        if self.has_reaction and self.round_manager.goes_before_in_initiative(self, self.selected_target):
            self.has_reaction = False #TODO consider moving this to the calling scope
            # chosen_aoo = copy.deepcopy(self.basic_attack_cache)
            chosen_aoo = self.basic_attack_cache
            chosen_aoo.set_target_character(moving_character)
            logger.debug(f"{self.name} took an AoO {chosen_aoo.get_name()} against {moving_character.get_name()}",
                         extra={"team": self.team_name})
            return chosen_aoo
        return None

    def prompt_pam(self, moving_character):
        if self.has_reaction:
            self.has_reaction = False  # TODO consider moving this to the calling scope
            # chosen_aoo = copy.deepcopy(self.basic_attack_cache)
            chosen_aoo = self.basic_attack_cache
            chosen_aoo.set_target_character(moving_character)
            logger.debug(f"{self.name} uses an polearm master attack {chosen_aoo.get_name()} against {moving_character.get_name()}",
                         extra={"team": self.team_name})
            return chosen_aoo
        return None
