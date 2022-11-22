from simulator.character import Character
from simulator.attack import Attack
import logging

logger = logging.getLogger(__name__)

class Cyanwrath(Character):

    def __init__(self):
        cyanwrath_attacks = [Attack("Polearm", self, 7, "1d10", 4, "action", "Slashing", [19, 20]),
                             Attack("Butt end of Polearm", self, 7, "1d4", 4, "bonus_action", "Bludgeoning", [19, 20])]
        super().__init__("Cyanwrath", cyanwrath_attacks, 95, 17, 1, 30, ["Lightning"], num_attacks=2)

    def get_action(self, battle_map):
        chosen_action = None
        target_name = battle_map.get_nearest_enemy_name(self)
        for action in self.actions:
            if self.has_action and not action.is_bonus():
                if self.num_attacks and not self.multiattack_in_progress:
                    self.multiattack_in_progress = True
                if self.curr_num_attacks and self.multiattack_in_progress:
                    chosen_action = action
                    chosen_action.set_target_name(target_name)
                    self.curr_num_attacks -= 1
                    logger.debug(f"{self.name} uses action {chosen_action.get_name()} against {target_name}", extra={"team": self.team_name})
                    return chosen_action
                else:
                    self.has_action = False
                    self.multiattack_in_progress = False
            elif self.has_bonus_action and action.is_bonus():
                chosen_action = action
                chosen_action.set_target_name(target_name)
                self.has_bonus_action = False
                logger.debug(f"{self.name} uses action {chosen_action.get_name()} against {target_name}", extra={"team": self.team_name})
                return chosen_action
        return chosen_action