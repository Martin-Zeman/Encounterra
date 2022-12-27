from simulator.combatant import Combatant
from simulator.attack import Attack
from simulator.dodge import Dodge
from simulator.abilities.totem_rage import TotemRage
from simulator.movement import Movement, MovementGenerator
from simulator.action import Action
from simulator.misc import DamageType
import numpy as np
import logging
import copy

logger = logging.getLogger(__name__)

class Rena(Combatant):

    def __init__(self):
        rena_attacks = [Attack("Two-handed axe", self,  7, "1d12", 4, Action.ActionClasses.ACTION, DamageType.Slashing, 1)]
        super().__init__("Rena", actions=rena_attacks, hp=61, ac=15, init_bonus=1, speed=40, resistances=[], dc=15, num_attacks=2)
        rage = TotemRage(self, 3, 2)
        self.actions.append(rage)
        self.rage = self.actions[-1]
        self.basic_attack_cache = rena_attacks[0]
        self.has_danger_sense = True

    def get_action(self, battle_map):
        while self.has_action or self.has_bonus_action or self.movement:
            logger.debug(f"Has action {self.has_action}, has_bonus action {self.has_bonus_action}, movement {self.movement}")
            chosen_action = None
            # First rage if not raging
            if not self.rage.is_active() == "Rage" and self.has_bonus_action:
                if self.rage.activate():
                    self.has_bonus_action = False # TODO put this into the action itself
                    logger.debug(f"{self.name} uses bonus action rage", extra={"team": self.team_color})
                    # TODO consider returning None
                    return self.rage

            nearest =  battle_map.get_nearest_enemy(self)
            if self.selected_target is None or not self.selected_target.is_alive() or self.selected_target is not nearest:
                # Get new target
                self.selected_target = nearest
                if not self.selected_target:
                    return None

            target_position = battle_map.get_combatant_position(self.selected_target)
            logger.debug(f"Target is at {target_position} and my cache is {None if self.target_position_cache is None else self.target_position_cache}")
            if not np.array_equal(self.target_position_cache, target_position):
                path = battle_map.get_path_to(self, self.selected_target)
                if not path:
                    logger.debug(f"{self.name} has nowhere to go and uses the dodge action", extra={"team": self.team_color})
                    self.has_action = False
                    return Dodge(self, Action.ActionClasses.ACTION)
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
                            chosen_action.set_target_combatant(self.selected_target)
                            self.curr_num_attacks -= 1
                            logger.debug(f"{self.name} uses action {chosen_action.get_name()} against {self.selected_target.get_name()}", extra={"team": self.team_color})
                            return chosen_action
                        else:
                            self.has_action = False
                            self.multiattack_in_progress = False
            else:
                logger.debug("Is out of range")
            return chosen_action
        logger.debug(f"{self.name} uses the dodge action", extra={"team": self.team_color})
        return Dodge(self, Action.ActionClasses.ACTION)

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            self.has_reaction = False #TODO consider moving this to the calling scope
            # chosen_aoo = copy.deepcopy(self.basic_attack_cache)
            chosen_aoo = self.basic_attack_cache
            chosen_aoo.set_target_combatant(moving_combatant)
            logger.debug(f"{self.name} taken an AoO {chosen_aoo.get_name()} against {moving_combatant.get_name()}",
                         extra={"team": self.team_color})
            return chosen_aoo
        return None