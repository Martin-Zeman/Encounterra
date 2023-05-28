import copy

from simulator.abilities.on_hit_prone import OnHitProne
from simulator.utils.state_machine_template import StateMachineTemplate
from simulator.combatant import Combatant
from simulator.misc import DamageType, SavingThrow, Size
import numpy as np
import logging

logger = logging.getLogger("EncounTroll")




class StoneGiant(Combatant):

    def __init__(self, effect_tracker, name="Stone Giant"):
        super().__init__(effect_tracker, name, level=5, hp=126, ac=17, init_bonus=2, spell_to_hit=0, speed=40, resistances=set(), dc=17)
        self.size = Size.HUGE
        self.club = self.add_ability(Action.MELEE_ATTACK,  name="Greatclub", combatant=self, to_hit=9, dmg_dice="3d8", dmg_bonus=6, dmg_type=DamageType.Bludgeoning, attack_range=3)
        self.rock = self.add_ability(Action.RANGED_ATTACK, name="Rock", combatant=self, to_hit=9, dmg_dice="4d10", dmg_bonus=6,
                                            dmg_type=DamageType.Bludgeoning, attack_range=48, crit_range=1, ammo=2, on_hit=OnHitProne(SavingThrow.STR, 17))
        self.add_ability(Reaction.REACTION_ATTACK,  name="Greatclub", combatant=self, to_hit=9, dmg_dice="3d8", dmg_bonus=6, dmg_type=DamageType.Bludgeoning, attack_range=15)
        self.build_attack_fms()
        self.add_ability(Passive.MULTIATTACK, num_attacks=2)
        self.melee_reaction_range = 3
        self.saving_throws[SavingThrow.STR] = 6
        self.saving_throws[SavingThrow.DEX] = 5
        self.saving_throws[SavingThrow.CON] = 8
        self.saving_throws[SavingThrow.INT] = 0
        self.saving_throws[SavingThrow.WIS] = 4
        self.saving_throws[SavingThrow.CHA] = -1


    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_state('1')
        self.attack_fsm.add_transition(str(self.club[1]), '0', '1')
        self.attack_fsm.add_transition(str(self.club[1]), '1', 'nop')
        self.attack_fsm.add_transition(str(self.rock[1]), '0', 'nop')


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


    def new_turn(self):
        super().new_turn()
        self.movement_generator = None

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self} taken an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
