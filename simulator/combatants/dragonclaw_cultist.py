from simulator.combatant import Combatant
from simulator.attack import Attack
from simulator.dodge import Dodge
from simulator.movement import MovementIncrement, MovementGenerator
from simulator.misc import DamageType
from simulator.action_factory import *
import logging

logger = logging.getLogger(__name__)


class DragonclawCultist(Combatant):

    def __init__(self, name="Dragonclaw"):
        super().__init__(name, level=5, hp=16, ac=14, init_bonus=3, spell_to_hit=0, speed=30, resistances=[], dc=0)
        self.attack_args = {Action.ATTACK: [None, "Scimitar", 5, "1d6", 3, DamageType.Slashing, 1, [20]],
                            Reaction.REACTION_ATTACK: [
                            None, "Scimitar", 5, "1d6", 3, DamageType.Slashing, 1, [20]]}

        self.add_ability(Passive.MULTIATTACK, num_attacks=2)
        self.max_melee_range = 1  # TODO: maybe add a lookup here
        self.has_pack_tactics = True
        self.has_fanatical_advantage = True

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
                return self.actions[0], *attack_args
            else:
                self.multiattack_in_progress = False
        else:
            logger.debug("Is out of range")
            return None,

    def get_action(self, battle_map):
        while self.has_action or self.movement:
            logger.debug(f"Has action {self.has_action}, movement {self.movement}")
            # chosen_action = None

            if self.selected_target is None or not self.selected_target.is_alive():
                # Get new target
                self.selected_target = battle_map.get_nearest_enemy(self)
                if not self.selected_target:
                    return None,

            target_position = battle_map.get_combatant_position(self.selected_target)
            logger.debug(f"Target is at {target_position}")
            dist = battle_map.get_distance(self, self.selected_target)
            if self.movement and self.has_action and dist > 1:
                # I haven't attacked yet and I'm too far away, move into range
                path = battle_map.get_path_to(self, self.selected_target)
                if not path:
                    logger.debug(f"{self.name} has nowhere to go and uses the dodge action", extra={"team": self.team_color})
                    return Action.DODGE,
                self.movement_generator = MovementGenerator(self, path, True).get_generator()
                try:
                    movement = next(self.movement_generator)
                    logger.debug("Moving")
                    return Movement.STANDARD, movement
                except StopIteration:
                    pass  # can't go any farther
            elif (self.has_action or self.multiattack_in_progress) and dist <= 1:
                # if I'm in range and I still have an action then attack
                attack = self.attack_routine(battle_map)
                if attack:
                    return attack

            if self.has_action:
                logger.debug(f"{self.name} uses the dodge action", extra={"team": self.team_color})
                return Action.DODGE,
            return None,

    def prompt_aoo(self, moving_combatant):
        # only use it if I go before my selected target in initiative so that I can move away and use sentinel+pam
        if self.has_reaction:
            attack_args = self.attack_args[Reaction.REACTION_ATTACK]
            attack_args[0] = moving_combatant  # sets the target
            logger.debug(f"{self.name} took an AoO {attack_args[1]} against {moving_combatant}",
                         extra={"team": self.team_color})
            return self.reactions[0], *attack_args
        return None
