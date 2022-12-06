from simulator.character import Character
from simulator.attack import Attack
from simulator.dodge import Dodge
from simulator.abilities.rage import Rage
from simulator.movement import Movement, MovementGenerator
from simulator.action import Action
import numpy as np
import logging
import copy

logger = logging.getLogger(__name__)

class Rena(Character):

    def __init__(self):
        rena_attacks = [Attack("Two-handed axe", self,  7, "1d12", 4, Action.ActionClasses.ACTION, "Slashing", 1)]
        super().__init__("Rena", rena_attacks, 61, 15, 1, 40, [], num_attacks=2)
        rage = Rage(self, 3, 2)
        self.actions.append(rage)
        self.rage = self.actions[-1]
        self.basic_attack_cache = rena_attacks[0]

    def get_action(self, battle_map):
        while self.has_action or self.has_bonus_action or self.movement:
            logger.debug(f"Has action {self.has_action}, has_bonus action {self.has_bonus_action}, movement {self.movement}")
            chosen_action = None
            # First rage if not raging
            if not self.rage.is_active() == "Rage" and self.has_bonus_action:
                if self.rage.activate():
                    self.has_bonus_action = False # TODO put this into the action itself
                    logger.debug(f"{self.name} uses bonus action rage", extra={"team": self.team_name})
                    # TODO consider returning None
                    return self.rage

            if self.selected_target is None or not self.selected_target.is_alive():
                # Get new target
                self.selected_target = battle_map.get_nearest_enemy(self)
                if not self.selected_target:
                    return None

            target_position = battle_map.get_character_position(self.selected_target.get_name())
            logger.debug(f"Target is at {target_position} and my cache is {None if self.target_position_cache is None else self.target_position_cache}")
            if not np.array_equal(self.target_position_cache, target_position):
                path = battle_map.get_path_to_enemy(self, self.selected_target)
                self.movement_generator = MovementGenerator(self, Movement.STANDARD, path, True).get_generator()
                self.target_position_cache = target_position

            if not battle_map.are_in_range(self, self.selected_target, self.max_melee_range):
                try:
                    movement = next(self.movement_generator)
                    return movement
                except StopIteration:
                    logger.debug("Out of movement or at destination")
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
            else:
                logger.debug("Is out of range")
            return chosen_action
        logger.debug(f"{self.name} uses the dodge action", extra={"team": self.team_name})
        return Dodge("dodge", self, Action.ActionClasses.ACTION)

    def prompt_aoo(self, moving_character):
        if self.has_reaction:
            self.has_reaction = False #TODO consider moving this to the calling scope
            # chosen_aoo = copy.deepcopy(self.basic_attack_cache)
            chosen_aoo = self.basic_attack_cache
            chosen_aoo.set_target_character(moving_character)
            logger.debug(f"{self.name} taken an AoO {chosen_aoo.get_name()} against {moving_character.get_name()}",
                         extra={"team": self.team_name})
            return chosen_aoo
        return None