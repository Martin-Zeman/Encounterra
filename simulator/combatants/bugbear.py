import copy

from simulator.actions.action_selector import get_best_actions
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
        self.javelin_attack = self.add_ability(Action.RANGED_ATTACK,  name="Javelin", combatant=self, to_hit=4, dmg_dice="1d6", dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=24, crit_range=1, ammo=1)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Morningstar", combatant=self, to_hit=4, dmg_dice="2d8", dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1)
        self.build_attack_fms()
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

    def get_action(self, battle_map):
        """
        Calculates the next best action. The algorithm works in two phases. In the first phase when the combatant still has movement left,
        it follows the steps described above. In the second phase, once the combatant reaches the target destination or runs out of movement
        the best action is recalculated every time to react to any possible changes on the battle_map.
        :param battle_map:
        :return: the next best actoid
        """
        if self.is_affected_by(Conditions.PRONE):
            return GetUpFactory().create()
        distances, shortest_paths = battle_map.calc_dijkstra(self)  # Has to be recalculated every time (due to forced movement etc.)
        if self.action_plan:
            if isinstance(self.action_plan[0], MovementIncrement) and self.movement:
                return self.action_plan.pop(0)
        self.action_plan = get_best_actions(self, battle_map, distances, shortest_paths)
        if not self.action_plan:
            return None  # Either no action possible or all actions already used
        return self.action_plan.pop(0)


    def export_resources(self):
        return {
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_fsm_state': self.attack_fsm.state,
            'ammo': copy.deepcopy(self.ammo)
        }

    def load_resources(self, resources):
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.set_state(resources['attack_fsm_state'])
        self.ammo = resources['ammo']

    def prompt_aoo(self, moving_combatant):
        # only use it if I go before my selected target in initiative so that I can move away and use sentinel+pam
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
