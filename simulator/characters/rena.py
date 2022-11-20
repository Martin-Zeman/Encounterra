from simulator.character import Character
from simulator.attack import Attack
from simulator.abilities.rage import Rage
import logging

logger = logging.getLogger(__name__)

class Rena(Character):

    def __init__(self):
        rena_attacks = [Attack("Two-handed axe", self,  7, "1d12", 4, "action", "Slashing")]
        super().__init__("Rena", rena_attacks, 61, 15, 1, 40, [], num_attacks=2)
        rage = Rage(self, 3, 2)
        self.actions.append(rage)

    def get_action(self, battle_map):
        chosen_action = None
        target_name = battle_map.get_nearest_enemy_name(self)
        # First rage if not raging
        for action in self.actions:
            if action.get_name() == "Rage" and self.has_bonus_action:
                if action.activate():
                    self.has_bonus_action = False # TODO put this into the action itself
                    logger.debug(f"{self.name} uses bonus action {action.get_name()}", extra={"team": self.team_name})
                    return action
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
        return chosen_action