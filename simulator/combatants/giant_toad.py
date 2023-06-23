import copy

from simulator.abilities.on_hit_auto_restrained import OnHitAutoRestrained
from simulator.actions.action_types import Action, Reaction
from simulator.utils.state_machine_template import StateMachineTemplate
from simulator.combatant import Combatant
from simulator.misc import DamageType, SavingThrow, Size
import logging

logger = logging.getLogger("EncounTroll")


class GiantToad(Combatant):

    def __init__(self, effect_tracker, name="Giant Toad"):
        super().__init__(effect_tracker, name, level=1, hp=39, ac=11, init_bonus=1, spell_to_hit=0, speed=20, resistances=set(), dc=0)
        self.size = Size.LARGE
        self.bite = self.add_ability(Action.PRE_SWALLOW_BITE,  name="Bite", combatant=self, to_hit=4, dmg_dice="1d10", dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1,\
                                     on_hit=OnHitAutoRestrained(SavingThrow.STR, 13), extra_dmg=[('1d10', DamageType.Poison)])
        self.add_ability(Reaction.REACTION_ATTACK,  name="Bite", combatant=self, to_hit=4, dmg_dice="1d10", dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1,\
                         on_hit=OnHitAutoRestrained(SavingThrow.STR, 13), extra_dmg=[('1d10', DamageType.Poison)])
        # TODO Add the swallow itself
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 2
        self.saving_throws[SavingThrow.DEX] = 2
        self.saving_throws[SavingThrow.CON] = 1
        self.saving_throws[SavingThrow.INT] = -1
        self.saving_throws[SavingThrow.WIS] = 0
        self.saving_throws[SavingThrow.CHA] = -1
        self.athletics = 2
        self.acrobatics = 1


    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.bite[1]), '0', 'nop')  # Melee


    def export_resources(self):
        return {
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_fsm_state': self.attack_fsm.state,
            'constricting_target': self.constricting_target,
            'ammo': copy.deepcopy(self.ammo)
        }

    def load_resources(self, resources):
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.set_state(resources['attack_fsm_state'])
        self.constricting_target = resources['constricting_target']
        self.ammo = resources['ammo']

    def prompt_aoo(self, moving_combatant):
        # only use it if I go before my selected target in initiative so that I can move away and use sentinel+pam
        if self.has_reaction and not self.constricting_target:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
