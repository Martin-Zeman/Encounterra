import copy

from simulator.actions.action_types import Action, BonusAction, Reaction, Passive
from simulator.utils.state_machine_template import StateMachineTemplate
from simulator.combatant import Combatant
from simulator.misc import DamageType, SavingThrow
import logging

logger = logging.getLogger("EncounTroll")


class AssassinRogue5Lvl(Combatant):

    def __init__(self, name="AssassinRogue5Lvl"):
        super().__init__(name, level=5, hp=33, ac=16, init_bonus=4, speed=30, spell_to_hit=0, resistances=set(), dc=15)
        self.rapier = self.add_ability(Action.MELEE_ATTACK, name="Rapier", combatant=self, to_hit=7, dmg_dice="1d8", dmg_bonus=4, dmg_type=DamageType.Piercing, attack_range=1)
        self.shortbow = self.add_ability(Action.RANGED_ATTACK,  name="Shortbow", combatant=self, to_hit=7, dmg_dice="1d6", dmg_bonus=4, dmg_type=DamageType.Piercing, attack_range=64, crit_range=1)
        self.add_ability(Reaction.REACTION_ATTACK, name="Rapier", combatant=self, to_hit=7, dmg_dice="1d8", dmg_bonus=4, dmg_type=DamageType.Piercing, attack_range=1)
        self.danger_zone_attack = self.shortbow
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = -1
        self.saving_throws[SavingThrow.DEX] = 7
        self.saving_throws[SavingThrow.CON] = 1
        self.saving_throws[SavingThrow.INT] = 4
        self.saving_throws[SavingThrow.WIS] = 2
        self.saving_throws[SavingThrow.CHA] = 1
        self.athletics = -1
        self.acrobatics = 7

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.rapier[1]), '0', 'nop')
        self.attack_fsm.add_transition(str(self.shortbow[1]), '0', 'nop')


    def prompt_aoo(self, moving_combatant):
        return None  # Saving reaction for Shield

    def export_resources(self):
        return {
            'movement': self.movement,
            'already_used_sneak_attack_this_turn': self.already_used_sneak_attack_this_turn,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_state_machine': self.attack_fsm.state
        }

    def load_resources(self, resources):
        self.movement = resources['movement']
        self.already_used_sneak_attack_this_turn = resources['already_used_sneak_attack_this_turn']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.set_state(resources['attack_state_machine'])


    def prompt_after_hit_reaction(self, attacking_combatant, attack_roll):
        # TODO Uncanny Dodge
        return None
