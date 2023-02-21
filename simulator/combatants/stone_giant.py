from simulator.abilities.on_hit_prone import OnHitProne
from simulator.combatant import Combatant
from simulator.actions.movement import MovementGenerator, GetUpFromProne
from simulator.feasibility import get_feasible_actions
from simulator.misc import DamageType, SavingThrow, Conditions
from simulator.action_factory import *
from simulator.action_types import *
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.misc import Side
import numpy as np
import logging

logger = logging.getLogger(__name__)


class StoneGiant(Combatant):

    def __init__(self, effect_tracker, name="Stone Giant"):
        super().__init__(effect_tracker, name, level=5, hp=126, ac=17, init_bonus=2, spell_to_hit=0, speed=40, resistances=set(), dc=17)
        club = self.add_ability(Action.ATTACK,  name="Greatclub", combatant=self, to_hit=9, dmg_dice="3d8", dmg_bonus=6, dmg_type=DamageType.Bludgeoning, attack_range=3, attack_type=AttackFactory.Type.MELEE, max_num=2)
        self.rock_attack = self.add_ability(Action.ATTACK, name="Rock", combatant=self, to_hit=9, dmg_dice="4d10", dmg_bonus=6,
                                            dmg_type=DamageType.Bludgeoning, attack_range=48, crit_range=[20],
                                            attack_type=AttackFactory.Type.RANGED, ammo=2, on_hit=OnHitProne(SavingThrow.STR, 17))
        self.add_ability(Reaction.REACTION_ATTACK,  name="Greatclub", combatant=self, to_hit=9, dmg_dice="3d8", dmg_bonus=6, dmg_type=DamageType.Bludgeoning, attack_range=15, attack_type=AttackFactory.Type.MELEE)
        self.add_ability(Passive.MULTIATTACK, num_attacks=2)
        self.movement_generator = None
        self.selected_target = None
        self.path = None
        self.saving_throws[SavingThrow.STR][0] = 6
        self.saving_throws[SavingThrow.DEX][0] = 5
        self.saving_throws[SavingThrow.CON][0] = 8
        self.saving_throws[SavingThrow.INT][0] = 0
        self.saving_throws[SavingThrow.WIS][0] = 4
        self.saving_throws[SavingThrow.CHA][0] = -1


    def plan_path(self, battle_map, target_copmbatant, target_position):
        self.path = battle_map.get_path_to(self, target_copmbatant)
        if not self.path:
            logger.debug(f"{self.name} has nowhere to go. Using dodge action", extra={"team": self.team_color})
            raise RuntimeError
        self.movement_generator = MovementGenerator(self, self.path).get_generator()
        self.target_position_cache = target_position

    def get_action(self, battle_map):
        if self.is_affected_by(Conditions.PRONE) and self.movement >= self.speed / 2:
            return GetUpFromProne()

        # TODO add the knock prone effect to the rock
        # TODO prevent it from throwing a rock once it's used a club
        feasible_action_factories = get_feasible_actions(self.action_factories, self, battle_map)
        feasible_bonus_action_factories = get_feasible_actions(self.bonus_action_factories, self, battle_map)
        feasible_haste_action_factories = get_feasible_actions(self.haste_action_factories, self, battle_map)
        # feasible_free_actions = get_feasible_actions(self.free_actions, self, battle_map)
        if len(feasible_action_factories) > 0 or len(feasible_bonus_action_factories) > 0 or len(feasible_haste_action_factories) > 0:# or len(feasible_free_actions > 0):
            feasible_actions = list(filter(lambda item: item is not None, [f[1].create_best(self, battle_map) for f in feasible_action_factories]))
            feasible_bonus_actions = list(filter(lambda item: item is not None, [f[1].create_best(self, battle_map) for f in feasible_bonus_action_factories]))
            feasible_haste_actions = list(filter(lambda item: item is not None, [f[1].create_best(self, battle_map) for f in feasible_haste_action_factories]))
            # feasible_free_actions = [fa[1].create_best(self, battle_map) for fa in feasible_free_actions]

            action_threats = [(fa.calculate_threat(self, battle_map), fa) for fa in feasible_actions]
            bonus_action_threats = [(fba.calculate_threat(self, battle_map), fba) for fba in feasible_bonus_actions]
            haste_action_threats = [(fha.calculate_threat(self, battle_map), fha) for fha in feasible_haste_actions]

            # action_threats.sort(key=lambda a: a[0], reverse=True)
            # bonus_action_threats.sort(key=lambda a: a[0], reverse=True)
            # haste_action_threats.sort(key=lambda a: a[0], reverse=True)
            all_actions = action_threats
            all_actions.extend(bonus_action_threats)
            all_actions.extend(haste_action_threats)
            all_actions.sort(key=lambda a: a[0], reverse=True)
            try:
                selected_action = all_actions[0][1]
                # logger.debug(f"{self} uses {selected_action}")
            except IndexError:
                return None
            if ActoidFlags.IS_ATTACK_LIKE in selected_action.actoid_type:
                target_position = battle_map.get_combatant_position(selected_action.target_combatant)
                if not np.array_equal(self.target_position_cache, target_position):
                    # if the target moved, recalculate path
                    try:
                        self.plan_path(battle_map, selected_action.target_combatant, target_position)
                    except RuntimeError:
                        return None
                else:
                    self.movement_generator = MovementGenerator(self, self.path).get_generator()

                if not battle_map.are_in_range(self, selected_action.target_combatant, selected_action.factory.range):
                    try:
                        movement = next(self.movement_generator)
                        logger.verbose(f"Moving by {movement}")
                        return movement
                    except StopIteration:
                        # this means that either the path has been exhausted and we're still not in range => ranged attack
                        self.movement_generator = None
                        if self.has_action:
                            self.rock_attack[1].action_type = Action.ATTACK
                        elif self.has_haste_action:
                            self.rock_attack[1].action_type = HasteAction.HASTE_ATTACK
                        else:
                            return None
                        return self.rock_attack[1].create(self.selected_target)
            return selected_action

        else:
            return None


    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.debug(f"{self} taken an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
