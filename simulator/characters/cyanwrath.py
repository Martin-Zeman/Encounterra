from simulator.character import Character
from simulator.attack import Attack
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
        self.max_melee_range = 2 # TODO: maybe add a lookup here

    def get_action(self, battle_map):
        while self.has_action or self.has_bonus_action or self.movement:
            logger.debug(f"Has action {self.has_action}, has_bonus action {self.has_bonus_action}, movement {self.movement}")
            chosen_action = None

            if self.selected_target is None or not self.selected_target.is_alive():
                # Get new target
                self.selected_target = battle_map.get_nearest_enemy(self)
                if not self.selected_target:
                    return chosen_action

            target_position = battle_map.get_character_position(self.selected_target.get_name())
            logger.debug(f"Target is at {target_position} and my cache is {None if self.target_position_cache is None else self.target_position_cache}")
            if not np.array_equal(self.target_position_cache, target_position):
                path = battle_map.get_path_to_enemy(self, self.selected_target)
                self.movement_generator = MovementGenerator(self, Movement.STANDARD, path, True).get_generator()
                self.target_position_cache = target_position

            if not battle_map.are_in_range(self, self.selected_target, self.max_melee_range):
                logger.debug("Not in range")
                try:
                    movement = next(self.movement_generator)
                    logger.debug("Moving")
                    return movement
                except StopIteration:
                    pass #can't go any farther
            if battle_map.are_in_range(self, self.selected_target, self.max_melee_range):
                logger.debug("Is in range")
                for action in self.actions:
                    if self.has_action and action.is_action():
                        if self.num_attacks and not self.multiattack_in_progress:
                            self.multiattack_in_progress = True
                        if self.curr_num_attacks and self.multiattack_in_progress:
                            chosen_action = action
                            chosen_action.set_target_character(self.selected_target)
                            self.curr_num_attacks -= 1
                            logger.debug(f"{self.name} uses action {chosen_action.get_name()} against {self.selected_target.get_name()}", extra={"team": self.team_name})
                            return chosen_action
                        else:
                            self.has_action = False
                            self.multiattack_in_progress = False
                    elif self.has_bonus_action and action.is_bonus() and self.curr_num_attacks < self.num_attacks:
                        chosen_action = action
                        chosen_action.set_target_character(self.selected_target)
                        self.has_bonus_action = False
                        logger.debug(f"{self.name} uses action {chosen_action.get_name()} against {self.selected_target.get_name()}", extra={"team": self.team_name})
                        return chosen_action
            else:
                logger.debug("Is out of range")
            return chosen_action
        return None

    def prompt_aoo(self, character):
        if self.has_reaction:
            self.has_reaction = False #TODO consider moving this to the calling scope
            chosen_aoo = copy.deepcopy(self.basic_attack_cache)
            chosen_aoo.set_target_character(character)
            logger.debug(f"{self.name} taken an AoO {chosen_aoo.get_name()} against {character.get_name()}",
                         extra={"team": self.team_name})
            return chosen_aoo
        return None
