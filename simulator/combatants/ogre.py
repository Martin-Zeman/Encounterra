import copy

from ..actions.action_types import Action, Reaction
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Size, Class
import logging

logger = logging.getLogger("Encounterra")


class Ogre(Combatant):

    type = "Ogre"

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, Class.MONSTER.GIANT, level=1, hp=59, ac=11, init_bonus=-1, spell_to_hit=0, speed=40, resistances=set(), dc=0)
        self.size = Size.LARGE
        self.greatclub_attack = self.add_ability(Action.MELEE_ATTACK,  name="Greatclub", combatant=self, to_hit=6, dmg_dice="2d8", dmg_bonus=4, dmg_type=DamageType.Bludgeoning, attack_range=1, crit_range=1)
        self.javelin_attack = self.add_ability(Action.RANGED_ATTACK,  name="Javelin", combatant=self, to_hit=6, dmg_dice="2d6", dmg_bonus=4, dmg_type=DamageType.Piercing, attack_range=24, crit_range=1, ammo=1)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Greatclub", combatant=self, to_hit=6, dmg_dice="2d8", dmg_bonus=4, dmg_type=DamageType.Bludgeoning, attack_range=1, crit_range=1)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 4
        self.saving_throws[SavingThrow.DEX] = -1
        self.saving_throws[SavingThrow.CON] = 3
        self.saving_throws[SavingThrow.INT] = -3
        self.saving_throws[SavingThrow.WIS] = -2
        self.saving_throws[SavingThrow.CHA] = -2
        self.athletics = 4
        self.acrobatics = -1
        self.is_humanoid = False
        self.passive_perception = 8

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.greatclub_attack[1]), '0', 'nop')
        self.attack_fsm.add_transition(str(self.javelin_attack[1]), '0', 'nop')


    def export_resources(self):
        return {
            'movement': self.movement,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_fsm_state': self.attack_fsm.state,
            'ammo': copy.deepcopy(self.ammo)
        }

    def load_resources(self, resources):
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
