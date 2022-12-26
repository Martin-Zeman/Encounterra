from simulator.combatant import Combatant
from simulator.attack import Attack
from simulator.dodge import Dodge
from simulator.action import Action
from simulator.movement import Movement, MovementGenerator
from simulator.misc import DamageType
import numpy as np
import logging
import copy

logger = logging.getLogger(__name__)

class DragonclawCultist(Combatant):

    def __init__(self, name="Dragonclaw"):
        scimitar_attacks = [Attack("Scimitar", self, 5, "1d6", 3, Action.ActionClasses.ACTION, DamageType.Slashing, 1, [20])]
        super().__init__(name, actions=scimitar_attacks, hp=16, ac=14, init_bonus=3, speed=30, resistances=[], dc=0, num_attacks=2)
        self.basic_attack_cache = scimitar_attacks[0]# just a helper
        self.max_melee_range = 1 # TODO: maybe add a lookup here
        self.has_pack_tactics = False
        self.has_fanatical_advantage = False

    def attack_routine(self, battle_map):
        if battle_map.are_in_range(self, self.selected_target, self.max_melee_range):
            attack = self.basic_attack_cache
            logger.debug("Is in range")
            if self.has_action and self.num_attacks and not self.multiattack_in_progress:
                self.multiattack_in_progress = True
                self.has_action = False
            if self.curr_num_attacks and self.multiattack_in_progress:
                attack.set_target_combatant(self.selected_target)
                self.curr_num_attacks -= 1
                logger.debug(f"{self.name} uses action {attack.get_name()} against {self.selected_target.get_name()}",
                             extra={"team": self.team_color})
                return attack
            else:
                self.multiattack_in_progress = False
        else:
            logger.debug("Is out of range")
            return None

    def get_action(self, battle_map):
        while self.has_action or self.movement:
            logger.debug(f"Has action {self.has_action}, movement {self.movement}")
            # chosen_action = None

            if self.selected_target is None or not self.selected_target.is_alive():
                # Get new target
                self.selected_target = battle_map.get_nearest_enemy(self)
                if not self.selected_target:
                    return None

            target_position = battle_map.get_combatant_position(self.selected_target)
            logger.debug(f"Target is at {target_position}")
            dist = battle_map.get_distance(self, self.selected_target)
            if self.movement and self.has_action and dist > 1:
                # I haven't attacked yet and I'm too far away, move into range
                path = battle_map.get_path_to(self, self.selected_target)
                if not path:
                    logger.debug(f"{self.name} has nowhere to go and uses the dodge action", extra={"team": self.team_color})
                    self.has_action = False
                    return Dodge(self, Action.ActionClasses.ACTION)
                self.movement_generator = MovementGenerator(self, Movement.STANDARD, path, True).get_generator()
                try:
                    movement = next(self.movement_generator)
                    logger.debug("Moving")
                    return movement
                except StopIteration:
                    pass #can't go any farther
            elif (self.has_action or self.multiattack_in_progress) and dist <= 1:
                # if I'm in range and I still have an action then attack
                attack = self.attack_routine(battle_map)
                if attack:
                    return attack

            if self.has_action:
                logger.debug(f"{self.name} uses the dodge action", extra={"team": self.team_color})
                self.has_action = False
                return Dodge(self, Action.ActionClasses.ACTION)
            return None

    def prompt_aoo(self, moving_combatant):
        #only use it if I go before my selected target in initiative so that I can move away and use sentinel+pam
        if self.has_reaction:
            self.has_reaction = False #TODO consider moving this to the calling scope
            chosen_aoo = self.basic_attack_cache
            chosen_aoo.set_target_combatant(moving_combatant)
            logger.debug(f"{self.name} took an AoO {chosen_aoo.get_name()} against {moving_combatant.get_name()}",
                         extra={"team": self.team_color})
            return chosen_aoo
        return None

