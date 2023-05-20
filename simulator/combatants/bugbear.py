from simulator.utils.state_machine_template import StateMachineTemplate
from simulator.combatant import Combatant
from simulator.actions.movement import MovementGenerator, GetUpFactory
from simulator.misc import DamageType, SavingThrow, Conditions
from simulator.actions.action_factory import *
from simulator.misc import Side
import numpy as np
import logging

logger = logging.getLogger("EncounTroll")


class Bugbear(Combatant):

    def __init__(self, effect_tracker, name="Bugbear"):
        super().__init__(effect_tracker, name, level=1, hp=27, ac=16, init_bonus=2, spell_to_hit=0, speed=30, resistances=set(), dc=0)
        self.morningstar_attack = self.add_ability(Action.MELEE_ATTACK,  name="Morningstar", combatant=self, to_hit=4, dmg_dice="2d8", dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1)
        self.javelin_attack = self.add_ability(Action.RANGED_ATTACK,  name="Javelin", combatant=self, to_hit=4, dmg_dice="1d6", dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=24, crit_range=1)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Morningstar", combatant=self, to_hit=4, dmg_dice="2d8", dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1)
        self.build_attack_fms()
        self.movement_generator = None
        self.selected_target = None
        self.path = None
        self.saving_throws[SavingThrow.STR] = 2
        self.saving_throws[SavingThrow.DEX] = 2
        self.saving_throws[SavingThrow.CON] = 1
        self.saving_throws[SavingThrow.INT] = -1
        self.saving_throws[SavingThrow.WIS] = 0
        self.saving_throws[SavingThrow.CHA] = -1


    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()  # Initialized here to avoid pickling error when multiprocessing
        self.attack_fsm.add_transition(str(self.morningstar_attack[1]), '0', 'nop')  # Melee
        self.attack_fsm.add_transition(str(self.javelin_attack[1]), '0', 'nop')  # Ranged

    def plan_path(self, battle_map, target_position):
        logger.debug(f"Planning path to {self.selected_target} at position {target_position.get()}")
        self.path = battle_map.get_path_to_combatant(self, self.selected_target)
        if not self.path:
            logger.info(f"{self.name} has nowhere to go. Using dodge action", extra={"team": self.team_color})
            raise RuntimeError
        self.movement_generator = MovementGenerator(self, self.path).get_generator()
        self.target_position_cache = target_position

    def get_action(self, battle_map):
        if self.is_affected_by(Conditions.PRONE) and self.movement >= self.speed / 2:
            return GetUpFactory().create()

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

        if not battle_map.are_in_hop_range(self, self.selected_target, 1):
            try:
                movement = next(self.movement_generator)
                logger.debug(f"Moving by {movement}")
                return movement
            except StopIteration:
                # this means that either the path has been exhausted and we're still not in range => ranged attack
                self.movement_generator = None
                if self.has_action:
                    self.javelin_attack[1].action_type = Action.RANGED_ATTACK
                elif self.has_haste_action:
                    self.javelin_attack[1].action_type = HasteAction.HASTE_RANGED_ATTACK
                else:
                    return None
                return self.javelin_attack[1].create(self.selected_target)
        else:
            # Melee attack
            if self.has_action:
                self.morningstar_attack[1].action_type = Action.MELEE_ATTACK
            elif self.has_haste_action:
                self.morningstar_attack[1].action_type = HasteAction.HASTE_MELEE_ATTACK
            else:
                return None
            return self.morningstar_attack[1].create(self.selected_target)



    def new_turn(self):
        super().new_turn()
        self.movement_generator = None

    def export_resources(self):
        return {
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'attack_fsm_state': self.attack_fsm.state
        }

    def load_resources(self, resources):
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.attack_fsm.set_state(resources['attack_fsm_state'])

    def prompt_aoo(self, moving_combatant):
        # only use it if I go before my selected target in initiative so that I can move away and use sentinel+pam
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
