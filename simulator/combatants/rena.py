from simulator.combatant import Combatant
from simulator.movement import MovementGenerator
from simulator.misc import DamageType
from simulator.action_factory import *
import numpy as np
import logging

logger = logging.getLogger(__name__)


class Rena(Combatant):

    def __init__(self):
        super().__init__("Rena", level=5, hp=61, ac=15, init_bonus=1, spell_to_hit=0, speed=40, resistances=[], dc=15)
        self.attack_args = {Action.ATTACK: [None, "Two-handed axe",  7, "1d12", 4, DamageType.Slashing, 1],
                            Reaction.REACTION_ATTACK: [None, "Two-handed axe",  7, "1d12", 4, DamageType.Slashing, 1]}
        self.add_ability(BonusAction.TOTEM_RAGE, uses=3, rage_bonus=2)
        self.add_ability(Passive.MULTIATTACK, num_attacks=2)
        self.add_ability(Passive.DANGER_SENSE)


    def attack_routine(self, battle_map):
        if battle_map.are_in_range(self, self.selected_target, self.max_melee_range):
            logger.debug("Is in range")
            if self.has_action and self.curr_num_attacks and not self.multiattack_in_progress:
                self.multiattack_in_progress = True
            if self.curr_num_attacks and self.multiattack_in_progress:
                attack_args = self.attack_args[Action.ATTACK]
                attack_args[0] = self.selected_target  # sets the target
                logger.debug(f"{self.name} uses action {attack_args[1]} against {self.selected_target}",
                             extra={"team": self.team_color})
                return Action.ATTACK, *attack_args
            else:
                self.multiattack_in_progress = False
        else:
            logger.debug("Is out of range")
            return None,

    def get_action(self, battle_map):
        while self.has_action or self.has_bonus_action or self.movement:
            logger.debug(f"Has action {self.has_action}, has_bonus action {self.has_bonus_action}, movement {self.movement}")
            # First rage if not raging
            if not self.rage_active and self.curr_rage_uses and self.has_bonus_action:
                logger.debug(f"{self.name} uses bonus action rage", extra={"team": self.team_color})
                return BonusAction.TOTEM_RAGE,

            nearest = battle_map.get_nearest_enemy(self)
            if self.selected_target is None or not self.selected_target.is_alive() or self.selected_target is not nearest:
                # Get new target
                self.selected_target = nearest
                if not self.selected_target:
                    return None,

            target_position = battle_map.get_combatant_position(self.selected_target)
            logger.debug(
                f"Target is at {target_position} and my cache is {None if self.target_position_cache is None else self.target_position_cache}")
            if not np.array_equal(self.target_position_cache, target_position):
                path = battle_map.get_path_to(self, self.selected_target)
                if not path:
                    logger.debug(f"{self.name} has nowhere to go and uses the dodge action", extra={"team": self.team_color})
                    return Action.DODGE,
                self.movement_generator = MovementGenerator(self, path, True).get_generator()
                self.target_position_cache = target_position

            if not battle_map.are_in_range(self, self.selected_target, self.max_melee_range):
                try:
                    movement = next(self.movement_generator)
                    return movement
                except StopIteration:
                    logger.debug("Out of movement or at destination")
                    pass  # can't go any farther

            if self.has_action or self.multiattack_in_progress:
                # if I'm in range and I still have an action then attack
                attack = self.attack_routine(battle_map)
                if attack:
                    return attack
            else:
                logger.debug("Is out of range")
            return None,
        logger.debug(f"{self.name} uses the dodge action", extra={"team": self.team_color})
        return Action.DODGE,

    def reset(self):
        super().reset()
        self.rage_active = False  # TODO Remove this
        self.rage_uses = 3  # TODO Remove this

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            attack_args = self.attack_args[Reaction.REACTION_ATTACK]
            attack_args[0] = moving_combatant  # sets the target

            chosen_aoo = self.basic_attack_cache
            chosen_aoo.set_target_combatant(moving_combatant)
            logger.debug(f"{self.name} taken an AoO {attack_args[1]} against {moving_combatant}",
                         extra={"team": self.team_color})
            return chosen_aoo
        return None
