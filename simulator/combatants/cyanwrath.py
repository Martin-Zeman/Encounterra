from simulator.combatant import Combatant
from simulator.action_factory import *
from simulator.movement import MovementGenerator
from simulator.misc import DamageType
import logging

logger = logging.getLogger(__name__)


class Cyanwrath(Combatant):

    def __init__(self):
        super().__init__("Cyanwrath", level=9, hp=95, ac=17, init_bonus=1, spell_to_hit=0, speed=30, resistances=[DamageType.Lightning],
                         dc=15)
        self.attack_args = {Action.ATTACK: [None, "Polearm", 7, "1d10", 4, DamageType.Slashing, 2, [19, 20]],
                            BonusAction.PAM_BONUS_ATTACK: [None, "Butt end of Polearm", 7, "1d4", 4, DamageType.Bludgeoning, 2,
                                    [19, 20]],
                            Reaction.REACTION_ATTACK: [None, "Polearm", 7, "1d10", 4, DamageType.Slashing, 2, [19, 20]]}
        self.add_ability(BonusAction.PAM_BONUS_ATTACK)
        self.add_ability(Passive.MULTIATTACK, num_attacks=2)
        self.add_ability(Passive.POLEARM_MASTER)
        self.add_ability(Passive.SENTINEL)
        self.max_melee_range = 2  # TODO: maybe add a lookup here

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
            if self.has_bonus_action and self.curr_num_attacks < self.num_attacks:  # if already took the attack action
                attack_args = self.attack_args[BonusAction.PAM_BONUS_ATTACK]
                attack_args[0] = self.selected_target  # sets the target
                logger.debug(
                    f"{self.name} uses action {attack_args[1]} against {self.selected_target}",
                    extra={"team": self.team_color})
                return self.bonus_actions[0], *attack_args
        else:
            logger.debug("Is out of range")
            return None,

    def get_action(self, battle_map):
        while self.has_action or self.has_bonus_action or self.movement:
            logger.debug(f"Has action {self.has_action}, has_bonus action {self.has_bonus_action}, movement {self.movement}")
            # chosen_action = None

            if self.selected_target is None or not self.selected_target.is_alive():
                # Get new target
                self.selected_target = battle_map.get_nearest_enemy(self)
                if not self.selected_target:
                    return None,

            target_position = battle_map.get_combatant_position(self.selected_target)
            logger.debug(f"Target is at {target_position}")
            dist = battle_map.get_distance(self, self.selected_target)
            if self.movement and self.has_action and dist > 2:
                # I haven't attacked yet and I'm too far away, move into pole-arm range
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
            elif (self.has_action or self.multiattack_in_progress) and dist <= 2:
                # if I'm in range and I still have an action then attack
                attack = self.attack_routine(battle_map)
                if attack:
                    return attack
            elif self.movement and not self.has_action and dist <= 2:
                # If I'm in range but no longer have an action then I want to step away
                logger.debug(f"{self.name} wants to gain distance", extra={"team": self.team_color})
                free_coords = battle_map.get_free_coords_at_distance(self.selected_target, 3, self)
                if free_coords:
                    path = battle_map.get_path_to(self, free_coords[0])
                    self.movement_generator = MovementGenerator(self, path, True).get_generator()
                    try:
                        movement = next(self.movement_generator)
                        logger.debug("Moving")
                        return Movement.STANDARD, movement
                    except StopIteration:
                        pass  # can't go any farther

            if self.has_action:
                logger.debug(f"{self.name} uses the dodge action", extra={"team": self.team_color})
                return Action.DODGE,
            return None,

    def prompt_aoo(self, moving_combatant):
        # only use it if I go before my selected target in initiative so that I can move away and use sentinel+pam
        if self.has_reaction and self.round_manager.goes_before_in_initiative(self, self.selected_target):
            attack_args = self.attack_args[Reaction.REACTION_ATTACK]
            attack_args[0] = moving_combatant  # sets the target
            logger.debug(f"{self.name} took an AoO {attack_args[1]} against {moving_combatant}",
                         extra={"team": self.team_color})
            return self.reactions[0], *attack_args
        return None

    def prompt_pam(self, moving_combatant):
        if self.has_reaction:
            attack_args = self.attack_args[Reaction.REACTION_ATTACK]
            attack_args[0] = moving_combatant  # sets the target
            logger.debug(f"{self.name} uses an polearm master attack {attack_args[1]} against {moving_combatant}",
                         extra={"team": self.team_color})
            return self.reactions[0], *attack_args
        return None
