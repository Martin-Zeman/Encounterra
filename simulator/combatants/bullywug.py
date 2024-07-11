import copy

from ..actions.action_types import Action, Reaction
from ..resources import Uses, ResourceRefreshType
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class
import logging

logger = logging.getLogger("Encounterra")


class Bullywug(Combatant):

    name = "Bullywug"
    cls = Class.MONSTER.HUMANOID
    level = 1
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=11, ac=15, init_bonus=1, spell_to_hit=0, speed=20, resistances=set(), dc=0)
        self.bite = self.add_ability(Action.MELEE_ATTACK,  name="Bite", combatant=self, to_hit=3, dmg_dice=((1, 4),), dmg_bonus=1, dmg_type=DamageType.Bludgeoning, attack_range=1, crit_range=1)
        self.spear = self.add_ability(Action.MELEE_ATTACK,  name="Spear", combatant=self, to_hit=3, dmg_dice=((1, 6),), dmg_bonus=1, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1)
        self.spear_throw = self.add_ability(Action.RANGED_ATTACK, name="Spear Throw", combatant=self, to_hit=3, dmg_dice=((1, 6),), dmg_bonus=1, dmg_type=DamageType.Piercing, attack_range=12, crit_range=1, ammo=Uses(1, ResourceRefreshType.NEVER), uses_dex=False)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Spear", combatant=self, to_hit=3, dmg_dice=((1, 6),), dmg_bonus=1, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 1
        self.saving_throws[SavingThrow.DEX] = 2
        self.saving_throws[SavingThrow.CON] = 1
        self.saving_throws[SavingThrow.INT] = -2
        self.saving_throws[SavingThrow.WIS] = 0
        self.saving_throws[SavingThrow.CHA] = -2
        self.athletics = 1
        self.stealth = 3
        self.acrobatics = 2
        self.passive_perception = 10

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_new_state('1')
        self.attack_fsm.add_new_state('2')
        self.attack_fsm.add_transition(str(self.bite[1]), '0', '1')
        self.attack_fsm.add_transition(str(self.spear[1]), '1', 'nop')
        self.attack_fsm.add_transition(str(self.spear_throw[1]), '1', 'nop')
        self.attack_fsm.add_transition(str(self.spear[1]), '0', '2')
        self.attack_fsm.add_transition(str(self.spear_throw[1]), '0', '2')
        self.attack_fsm.add_transition(str(self.bite[1]), '2', 'nop')

    def export_resources(self):
        return {
            'movement': self.movement,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_fsm_state': self.attack_fsm.state,
            'ammo': copy.deepcopy(self.ammo)
        }

    def import_resources(self, resources):
        self.movement = resources['movement']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.set_state(resources['attack_fsm_state'])
        self.ammo = resources['ammo']

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
