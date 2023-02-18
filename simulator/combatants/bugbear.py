from simulator.combatant import Combatant
from simulator.actions.movement import MovementGenerator
from simulator.misc import DamageType
from simulator.action_factory import *
from simulator.misc import Side
import numpy as np
import logging

logger = logging.getLogger(__name__)


class Bugbear(Combatant):

    def __init__(self, effect_tracker, name="Bugbear"):
        super().__init__(effect_tracker, name, level=1, hp=27, ac=16, init_bonus=2, spell_to_hit=0, speed=30, resistances=set(), dc=0)
        self.morningstar_attack = self.add_ability(Action.ATTACK,  name="Morningstar", combatant=self, to_hit=4, dmg_dice="2d8", dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=1, crit_range=[20], attack_type=AttackFactory.Type.MELEE)
        self.javelin_attack = self.add_ability(Action.ATTACK,  name="Javelin", combatant=self, to_hit=4, dmg_dice="1d6", dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=24, crit_range=[20], attack_type=AttackFactory.Type.RANGED)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Morningstar", combatant=self, to_hit=4, dmg_dice="2d8", dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=1, crit_range=[20], attack_type=AttackFactory.Type.MELEE)
        self.movement_generator = None
        self.selected_target = None
        self.path = None

    def plan_path(self, battle_map, target_position):
        self.path = battle_map.get_path_to(self, self.selected_target)
        if not self.path:
            logger.debug(f"{self.name} has nowhere to go. Using dodge action", extra={"team": self.team_color})
            raise RuntimeError
        # logger.debug(f"Planned path: {self.path}")
        self.movement_generator = MovementGenerator(self, self.path).get_generator()
        self.target_position_cache = target_position


    def get_action(self, battle_map):
        # TODO investigate non-feasible movements
        if self.selected_target is None or not self.selected_target.is_alive():
            # Get new target
            self.selected_target, _, target_position = battle_map.get_nearest(self, Side.ENEMY)
        if not self.selected_target:
            return None

        target_position = battle_map.get_combatant_position(self.selected_target)
        if not np.array_equal(self.target_position_cache, target_position):
            # if the target moved, recalculate path
            try:
                self.plan_path(battle_map, target_position)
            except RuntimeError:
                return None
        else:
            self.movement_generator = MovementGenerator(self, self.path).get_generator()

        if not battle_map.are_in_range(self, self.selected_target, 1):
            try:
                movement = next(self.movement_generator)
                logger.verbose(f"Moving by {movement}")
                return movement
            except StopIteration:
                # this means that either the path has been exhausted and we're still not in range => ranged attack
                self.movement_generator = None
                if self.has_action:
                    self.javelin_attack[1].action_type = Action.ATTACK
                elif self.has_haste_action:
                    self.javelin_attack[1].action_type = HasteAction.HASTE_ATTACK
                else:
                    return None
                return self.javelin_attack[1].create(self.selected_target)
        else:
            # Melee attack
            if self.has_action:
                self.morningstar_attack[1].action_type = Action.ATTACK
            elif self.has_haste_action:
                self.morningstar_attack[1].action_type = HasteAction.HASTE_ATTACK
            else:
                return None
            return self.morningstar_attack[1].create(self.selected_target)



    def new_turn(self):
        super().new_turn()
        self.movement_generator = None
        # self.selected_target = None

    def prompt_aoo(self, moving_combatant):
        # only use it if I go before my selected target in initiative so that I can move away and use sentinel+pam
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.debug(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
