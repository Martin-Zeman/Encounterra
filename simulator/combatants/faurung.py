import copy

from simulator.actions.action_selector import get_best_actions
from simulator.utils.state_machine_template import StateMachineTemplate
from simulator.combatant import Combatant
from simulator.actions.movement import MovementGenerator, GetUpFactory
from simulator.spellslots import Spellslots, Class
from simulator.misc import CombatantArchetype, DamageType, get_factory_of_type, SavingThrow, Conditions
from simulator.action_factory import *
from simulator.spells.spell import SpellStats
from simulator.feasibility import get_feasible_factories
import logging
import numpy as np

logger = logging.getLogger(__name__)


class Faurung(Combatant):

    def __init__(self, effect_tracker, name="Faurung"):
        super().__init__(effect_tracker, name, level=5, hp=43, ac=16, init_bonus=2, speed=30, spell_to_hit=7, resistances=set(), dc=15)
        self.staff = self.add_ability(Action.MELEE_ATTACK, name="Staff of Defence", combatant=self, to_hit=2, dmg_dice="1d8", dmg_bonus=-1,
                         dmg_type=DamageType.Bludgeoning, attack_range=1)
        self.add_ability(Reaction.REACTION_ATTACK, name="Staff of Defence", combatant=self, to_hit=2, dmg_dice="1d8", dmg_bonus=-1,
                         dmg_type=DamageType.Bludgeoning, attack_range=1)
        self.add_ability(Action.FIREBALL)
        self.firebolt = self.add_ability(Action.FIREBOLT)
        self.danger_zone_attack = self.firebolt
        self.add_ability(Action.HASTE)
        self.add_ability(BonusAction.MISTY_STEP)
        self.add_ability(Reaction.SHIELD)
        self.add_ability(Passive.METAMAGIC, sorcery_points=5)
        self.add_ability(MetaAction.QUICKENED_SPELL)
        self.add_ability(MetaAction.TWINNED_SPELL)
        self.build_attack_fms()
        self.spellslots = Spellslots(Class.SORCERER, 5)
        self.archetype = CombatantArchetype.RANGED
        self.movement_generator_cache = None
        self.nowhere_to_go = False
        self.saving_throws[SavingThrow.STR] = -1
        self.saving_throws[SavingThrow.DEX] = 2
        self.saving_throws[SavingThrow.CON] = 6
        self.saving_throws[SavingThrow.INT] = 1
        self.saving_throws[SavingThrow.WIS] = 1
        self.saving_throws[SavingThrow.CHA] = 7

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()  # Initialized here to avoid pickling error when multiprocessing
        self.attack_fsm.add_transition(str(self.staff[1]), '0', 'nop')

    def get_action(self, battle_map):
        distances, shortest_paths = battle_map.calc_dijkstra(self)  # Has to be recalculated every time (due to forced movement etc.)
        if self.action_plan:
            if isinstance(self.action_plan[0], MovementIncrement) and self.movement:
                return self.action_plan.pop(0)
        self.action_plan = get_best_actions(self, battle_map, distances, shortest_paths)
        if not self.action_plan:
            return None  # Either no action possible or all actions already used
        return self.action_plan.pop(0)

    def new_turn(self):
        super().new_turn()
        self.nowhere_to_go = False
        self.movement_generator_cache = None

    def prompt_aoo(self, moving_combatant):
        return None

    def export_resources(self):
        return {
            'spellslots': copy.deepcopy(self.spellslots),
            'sorcery_points': self.curr_sorcery_points,
            'cast_leveled_spell': self.already_cast_leveled_spell_this_turn,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'attack_state_machine': self.attack_fsm.state
        }

    def load_resources(self, resources):
        self.spellslots = resources['spellslots']
        self.curr_sorcery_points = resources['sorcery_points']
        self.already_cast_leveled_spell_this_turn = resources['cast_leveled_spell']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.attack_fsm.set_state(resources['attack_state_machine'])


    def prompt_after_hit_reaction(self, attacking_combatant, attack_roll):
        if self.spellslots.get_spellslots(1) and self.has_reaction and attack_roll < self.dc + 5:
            shield_factory = get_factory_of_type(self.reaction_factories, Reaction.SHIELD)
            # logger.info(f"{self.name} casts Shield", extra={"team": self.team_color})
            return shield_factory.create() if shield_factory else None
        elif attack_roll >= self.dc + 5:
            logger.info("Shield would not suffice")
        elif self.has_reaction:
            logger.info(f"{self.name} cannot cast Shield. Out of spellslots.", extra={"team": self.team_color})
        return None
