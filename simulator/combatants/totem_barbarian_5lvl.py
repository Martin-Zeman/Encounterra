from simulator.combatant import Combatant
from simulator.actions.movement import MovementGenerator
from simulator.feasibility import get_feasible_actions
from simulator.misc import DamageType
from simulator.action_factory import *
from simulator.action_types import *
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.misc import Side
import numpy as np
import logging

logger = logging.getLogger(__name__)


class TotemBarbarian5Lvl(Combatant):

    def __init__(self, effect_tracker, name="TotemBarbarian5Lvl"):
        super().__init__(effect_tracker, name, level=5, hp=61, ac=15, init_bonus=1, spell_to_hit=0, speed=40, resistances=set(), dc=15)
        self.add_ability(Action.ATTACK,  name="Two-handed axe", combatant=self, to_hit=7, dmg_dice="1d12", dmg_bonus=4, dmg_type=DamageType.Slashing, attack_range=1, attack_type=AttackFactory.Type.MELEE)
        self.javelin_attack = self.add_ability(Action.ATTACK, name="Javelin", combatant=self, to_hit=4, dmg_dice="1d6", dmg_bonus=4, dmg_type=DamageType.Piercing, attack_range=24, crit_range=[20], attack_type=AttackFactory.Type.RANGED)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Two-handed axe", combatant=self, to_hit=7, dmg_dice="1d12", dmg_bonus=4, dmg_type=DamageType.Slashing, attack_range=1, attack_type=AttackFactory.Type.MELEE)
        self.add_ability(BonusAction.TOTEM_RAGE)
        self.add_ability(Passive.MULTIATTACK, num_attacks=2)
        self.add_ability(Passive.DANGER_SENSE)
        self.add_ability(Action.RECKLESS_ATTACK, name="Two-handed axe recklessly", combatant=self, to_hit=7, dmg_dice="1d12", dmg_bonus=4, dmg_type=DamageType.Slashing, attack_range=1, attack_type=AttackFactory.Type.MELEE)
        self.movement_generator = None
        self.selected_target = None
        self.path = None


    # def attack_routine(self, battle_map):
    #     if battle_map.are_in_range(self, self.selected_target, 1):
    #         logger.debug("Is in range")
    #         # if self.curr_num_attacks == self.num_attacks and not self.reckless_attack_active:
    #         #     logger.debug(f"{self} uses Reckless Attack", extra={"team": self.team_color})
    #         #     return (FreeAction.RECKLESS_ATTACK,)
    #         if self.has_action and self.curr_num_attacks and not self.multiattack_in_progress:
    #             self.multiattack_in_progress = True
    #         if self.curr_num_attacks and self.multiattack_in_progress:
    #             attack_args = self.attack_args[Action.ATTACK]
    #             attack_args[2] = self.selected_target  # sets the target
    #             logger.debug(f"{self} uses action {attack_args[0]} against {self.selected_target}",
    #                          extra={"team": self.team_color})
    #             return (Action.ATTACK, *attack_args)
    #         else:
    #             self.multiattack_in_progress = False
    #     else:
    #         logger.debug("Is out of range")
    #         return (MetaAction.DONE,)

    def plan_path(self, battle_map, target_copmbatant, target_position):
        logger.debug(f"{self} plan_path 1")
        self.path = battle_map.get_path_to(self, target_copmbatant)
        logger.debug(f"{self} plan_path 2")
        if not self.path:
            logger.debug(f"{self.name} has nowhere to go. Using dodge action", extra={"team": self.team_color})
            raise RuntimeError
        logger.debug(f"{self} plan_path 3")
        self.movement_generator = MovementGenerator(self, self.path).get_generator()
        logger.debug(f"{self} plan_path 4")
        self.target_position_cache = target_position
        logger.debug(f"{self} plan_path 5")

    def get_action(self, battle_map):
        logger.debug(f"{self} get_action 1")
        feasible_actions = get_feasible_actions(self.action_factories, self, battle_map)
        feasible_bonus_actions = get_feasible_actions(self.bonus_action_factories, self, battle_map)
        logger.debug(f"{self} get_action 1a feasible_bonus_actions = {feasible_bonus_actions}")
        feasible_haste_actions = get_feasible_actions(self.haste_action_factories, self, battle_map)
        # feasible_free_actions = get_feasible_actions(self.free_actions, self, battle_map)
        if len(feasible_actions) > 0 or len(feasible_bonus_actions) > 0 or len(feasible_haste_actions) > 0:# or len(feasible_free_actions > 0):
            logger.debug(f"{self} get_action 2")
            try:
                feasible_actions = list(filter(lambda item: item is not None, [fa[1].create_best(self, battle_map) for fa in feasible_actions]))
                feasible_bonus_actions = list(filter(lambda item: item is not None, [fa[1].create_best(self, battle_map) for fa in feasible_bonus_actions]))
                feasible_haste_actions = list(filter(lambda item: item is not None, [fa[1].create_best(self, battle_map) for fa in feasible_haste_actions]))
            except:
                print("FIXME")
            # feasible_free_actions = [fa[1].create_best(self, battle_map) for fa in feasible_free_actions]

            logger.debug(f"{self} get_action 3")
            action_threats = [(fa.calculate_threat(self, battle_map), fa) for fa in feasible_actions]
            bonus_action_threats = [(fba.calculate_threat(self, battle_map), fba) for fba in feasible_bonus_actions]
            haste_action_threats = [(fha.calculate_threat(self, battle_map), fha) for fha in feasible_haste_actions]

            # action_threats.sort(key=lambda a: a[0], reverse=True)
            # bonus_action_threats.sort(key=lambda a: a[0], reverse=True)
            # haste_action_threats.sort(key=lambda a: a[0], reverse=True)
            all_actions = action_threats
            all_actions.extend(bonus_action_threats)
            all_actions.extend(haste_action_threats)
            logger.debug(f"{self} get_action 4")
            all_actions.sort(key=lambda a: a[0], reverse=True)
            try:
                logger.debug(f"{self} get_action 5")
                selected_action = all_actions[0][1]
                logger.debug(f"{self} get_action 6")
                # logger.debug(f"{self} uses {selected_action}")
            except IndexError:
                logger.debug(f"{self} get_action 7 DONE")
                return None
            if ActoidFlags.IS_ATTACK_LIKE in selected_action.actoid_type:
                logger.debug(f"{self} get_action 8")
                target_position = battle_map.get_combatant_position(selected_action.target_combatant)
                if not np.array_equal(self.target_position_cache, target_position):
                    logger.debug(f"{self} get_action 9")
                    # if the target moved, recalculate path
                    try:
                        logger.debug(f"{self} get_action 10 {target_position}")
                        self.plan_path(battle_map, selected_action.target_combatant, target_position)
                        logger.debug(f"{self} get_action 11")
                    except RuntimeError:
                        logger.debug(f"{self} get_action 12 DONE")
                        return None
                else:
                    logger.debug(f"{self} get_action 13")
                    self.movement_generator = MovementGenerator(self, self.path).get_generator()

                logger.debug(f"{self} get_action 14")
                if not battle_map.are_in_range(self, selected_action.target_combatant, selected_action.factory.range):
                    logger.debug(f"{self} get_action 15")
                    try:
                        movement = next(self.movement_generator)
                        logger.verbose(f"Moving by {movement}")
                        return movement
                    except StopIteration:
                        # this means that either the path has been exhausted and we're still not in range => ranged attack
                        logger.debug(f"{self} get_action 16")
                        self.movement_generator = None
                        if self.has_action:
                            logger.debug(f"{self} get_action 17")
                            self.javelin_attack[1].action_type = Action.ATTACK
                        elif self.has_haste_action:
                            self.javelin_attack[1].action_type = HasteAction.HASTE_ATTACK
                        else:
                            logger.debug(f"{self} get_action 18 DONE")
                            return None
                        logger.debug(f"{self} get_action 19")
                        return self.javelin_attack[1].create(self.selected_target)
            # if notselected_action.factory.range
            logger.debug(f"{self} get_action 20 {selected_action}")
            return selected_action

            # while enemies and self.movement and not self.movement_generator_cache and not self.nowhere_to_go:
            #     free_coords = battle_map.get_free_coords_at_distance(enemies[0], self, int(self.movement + dist[0]))
            #     if not free_coords:
            #         # logger.debug(f"{self.name} has nowhere to go to")
            #         self.nowhere_to_go = True
            #         break
            #     path = battle_map.get_path_to(self, free_coords[0])
            #     self.movement_generator_cache = MovementGenerator(self, path).get_generator()
            #
            # if self.movement and self.movement_generator_cache:
            #     try:
            #         movement = next(self.movement_generator_cache)
            #         logger.debug("Trying to get distance")
            #         return movement
            #     except StopIteration:
            #         self.movement_generator_cache = None
        else:
            return None


        # while self.has_action or self.has_bonus_action or self.movement or self.has_haste_action:
        #     # logger.debug(f"Has action {self.has_action}, has_bonus action {self.has_bonus_action}, movement {self.movement}")
        #     # First rage if not raging
        #     if not self.rage_active and self.curr_rage_uses and self.has_bonus_action:
        #         logger.debug(f"{self} uses bonus action rage", extra={"team": self.team_color})
        #         return (BonusAction.TOTEM_RAGE,)
        #
        #     nearest, _ = battle_map.get_nearest(self, Side.ENEMY)
        #     if self.selected_target is None or not self.selected_target.is_alive() or self.selected_target is not nearest:
        #         # Get new target
        #         self.selected_target = nearest
        #         if not self.selected_target:
        #             return (MetaAction.DONE,)
        #
        #     target_position = battle_map.get_combatant_position(self.selected_target)
        #     logger.debug(
        #         f"Target is at {target_position} and my cache is {None if self.target_position_cache is None else self.target_position_cache}")
        #     if not np.array_equal(self.target_position_cache, target_position):
        #         path = battle_map.get_path_to(self, self.selected_target)
        #         if not path:
        #             logger.debug(f"{self} has nowhere to go and uses the dodge action", extra={"team": self.team_color})
        #             return (Action.DODGE,)
        #         self.movement_generator = MovementGenerator(self, path, True).get_generator()
        #         self.target_position_cache = target_position
        #
        #     if not battle_map.are_in_range(self, self.selected_target, self.max_melee_range):
        #         try:
        #             movement = next(self.movement_generator)
        #             return (Movement.STANDARD, movement)
        #         except StopIteration:
        #             if self.has_haste_action and not battle_map.are_in_range(self, self.selected_target, self.max_melee_range):
        #                 logger.debug(f"{self} uses haste dash", extra={"team": self.team_color})
        #                 return (HasteAction.HASTE_DASH,)
        #             elif self.has_haste_action:
        #                 attack_args = self.attack_args[Action.ATTACK]
        #                 attack_args[2] = self.selected_target  # sets the target
        #                 logger.debug(f"{self} takes a haste attack", extra={"team": self.team_color})
        #                 return (HasteAction.HASTE_ATTACK, *attack_args)
        #             logger.debug("Out of movement or at destination")
        #             pass  # can't go any farther
        #
        #     if self.has_action or self.multiattack_in_progress:
        #         # if I'm in range and I still have an action then attack
        #         attack = self.attack_routine(battle_map)
        #         if attack:
        #             return attack
        #     elif self.has_haste_action:
        #         attack_args = self.attack_args[Action.ATTACK]
        #         attack_args[2] = self.selected_target  # sets the target
        #         logger.debug(f"{self} takes a haste attack", extra={"team": self.team_color})
        #         return (HasteAction.HASTE_ATTACK, *attack_args)
        #     elif self.has_action:
        #         logger.debug(f"{self} uses the dodge action", extra={"team": self.team_color})
        #         return (Action.DODGE,)
        #     else:
        #         return (MetaAction.DONE,)
        # return (MetaAction.DONE,)


    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.debug(f"{self} taken an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
