import copy

from ..actions.action_types import Action, Reaction
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Size, Class
import logging

logger = logging.getLogger("Encounterra")


class BrownBear(Combatant):

    type = "Brown Bear"

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, Class.MONSTER.BEAST, level=1, hp=34, ac=11, init_bonus=0, spell_to_hit=0, speed=40, resistances=set(), dc=0)
        self.size = Size.LARGE
        self.bite = self.add_ability(Action.MELEE_ATTACK,  name="Bite", combatant=self, to_hit=5, dmg_dice="1d8", dmg_bonus=4, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1)
        self.claws = self.add_ability(Action.MELEE_ATTACK,  name="Claws", combatant=self, to_hit=5, dmg_dice="2d6", dmg_bonus=4, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Claws", combatant=self, to_hit=5, dmg_dice="2d6", dmg_bonus=4, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 4
        self.saving_throws[SavingThrow.DEX] = 0
        self.saving_throws[SavingThrow.CON] = 3
        self.saving_throws[SavingThrow.INT] = -4
        self.saving_throws[SavingThrow.WIS] = 1
        self.saving_throws[SavingThrow.CHA] = -2
        self.athletics = 4
        self.acrobatics = 0
        self.passive_perception = 13
        self.is_humanoid = False


    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_state('1')
        self.attack_fsm.add_state('2')
        self.attack_fsm.add_transition(str(self.bite[1]), '0', '1')
        self.attack_fsm.add_transition(str(self.claws[1]), '1', 'nop')
        self.attack_fsm.add_transition(str(self.claws[1]), '0', '2')
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
