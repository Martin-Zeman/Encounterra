from simulator.actions.action_types import Action, BonusAction, Reaction, Passive
from simulator.combatant import Combatant
from simulator.actions.movement import MovementGenerator
from simulator.misc import DamageType
from simulator.misc import Side
import logging

logger = logging.getLogger("EncounTroll")


class Cyanwrath(Combatant):

    def __init__(self):
        super().__init__("Cyanwrath", level=9, hp=95, ac=17, init_bonus=1, spell_to_hit=0, speed=30, resistances={DamageType.Lightning},
                         dc=15)
        self.add_ability(Action.MELEE_ATTACK,  name="Polearm", combatant=self, to_hit=7, dmg_dice="1d10", dmg_bonus=4, dmg_type=DamageType.Slashing, attack_range=2, crit_range=2)
        self.add_ability(BonusAction.PAM_BONUS_ATTACKK,  name="Butt end of Polearm", combatant=self, to_hit=7, dmg_dice="1d4", dmg_bonus=4, dmg_type=DamageType.Bludgeoning, attack_range=2, crit_range=2)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Polearm", combatant=self, to_hit=7, dmg_dice="1d10", dmg_bonus=4, dmg_type=DamageType.Slashing, attack_range=2, crit_range=3)
        self.add_ability(BonusAction.PAM_BONUS_ATTACK)
        self.add_ability(Passive.MULTIATTACK, num_attacks=2)
        self.add_ability(Passive.POLEARM_MASTER)
        self.add_ability(Passive.SENTINEL)
        self.melee_reaction_range = 2  # TODO: maybe add a lookup here

    def attack_routine(self, battle_map):
        if battle_map.are_in_hop_range(self, self.selected_target, self.melee_reaction_range):
            logger.info("Is in range")
            if self.has_action and self.curr_num_attacks and not self.multiattack_in_progress:
                self.multiattack_in_progress = True
            if self.curr_num_attacks and self.multiattack_in_progress:
                attack_args = self.attack_args[Action.MELEE_ATTACK]
                attack_args[2] = self.selected_target  # sets the target
                logger.info(f"{self.name} uses action {attack_args[0]} against {self.selected_target}",
                             extra={"team": self.team_color})
                return (self.actions[0], *attack_args)
            else:
                self.multiattack_in_progress = False
            if self.has_bonus_action and self.curr_num_attacks < self.num_attacks:  # if already took the attack action
                attack_args = self.attack_args[BonusAction.PAM_BONUS_ATTACK]
                attack_args[2] = self.selected_target  # sets the target
                logger.info(
                    f"{self.name} uses action {attack_args[0]} against {self.selected_target}",
                    extra={"team": self.team_color})
                return (self.bonus_actions[0], *attack_args)
        else:
            logger.info("Is out of range")
            return (MetaAction.DONE,)

    def get_action(self, battle_map):
        while self.has_action or self.has_bonus_action or self.movement or self.has_haste_action:
            # logger.info(f"Has action {self.has_action}, has_bonus action {self.has_bonus_action}, movement {self.movement}")

            dist = None
            if self.selected_enemy is None or not self.selected_enemy.is_alive():
                # Get new target
                self.selected_target, dist = battle_map.get_nearest(self, Side.ENEMY)
                if not self.selected_target:
                    return (MetaAction.DONE,)

            target_position = battle_map.get_combatant_position(self.selected_target)
            logger.info(f"Target is at {target_position}")
            if not dist:
                dist = battle_map.get_hop_distance(self, self.selected_target)
            if self.movement and self.has_action and dist > 2:
                # I haven't attacked yet and I'm too far away, move into pole-arm range
                path = battle_map.get_path_to_combatant(self, self.selected_target)
                if not path:
                    logger.info(f"{self.name} has nowhere to go and uses the dodge action", extra={"team": self.team_color})
                    return (Action.DODGE,)
                self.movement_generator = MovementGenerator(self, path, True).get_generator()
                try:
                    movement = next(self.movement_generator)
                    logger.debug(f"Moving by {movement}")
                    # logger.info(f"Retuning {Movement.STANDARD, movement}")
                    return (Movement.STANDARD, movement)
                except StopIteration:
                    pass  # can't go any farther
            elif (self.has_action or self.multiattack_in_progress) and dist <= 2:
                # if I'm in range and I still have an action then attack
                attack = self.attack_routine(battle_map)
                if attack:
                    return attack
            elif self.movement and not self.has_action and dist <= 2:
                # If I'm in range but no longer have an action then I want to step away
                logger.info(f"{self.name} wants to gain distance", extra={"team": self.team_color})
                free_coords = battle_map.get_free_coords_at_distance_from_target(self.selected_target, self, 3)
                if free_coords:
                    path = battle_map.get_path_to_coord(self, free_coords[0])
                    self.movement_generator = MovementGenerator(self, path, True).get_generator()
                    try:
                        movement = next(self.movement_generator)
                        logger.debug(f"Moving by {movement}")
                        return (Movement.STANDARD, movement)
                    except StopIteration:
                        pass  # can't go any farther

            if self.has_action:
                logger.info(f"{self.name} uses the dodge action", extra={"team": self.team_color})
                return (Action.DODGE,)
            return (MetaAction.DONE,)
        return (MetaAction.DONE,)

    def prompt_aoo(self, moving_combatant):
        # only use it if I go before my selected target in initiative so that I can move away and use sentinel+pam
        if self.has_reaction and (self.selected_target is None or self.round_manager.goes_before_in_initiative(self, self.selected_target)):
            aoo = self.aoo_factory.create(moving_combatant)
            logger.info(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None

    def prompt_pam(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self.name} uses an polearm master attack {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
