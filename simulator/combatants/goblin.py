import copy

from ..actions.action_types import Action, BonusAction, Reaction
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class
import logging

logger = logging.getLogger("Encounterra")


class Goblin(Combatant):

    type = "Goblin"

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, Class.MONSTER.HUMANOID, level=1, hp=7, ac=15, init_bonus=2, spell_to_hit=0, speed=30, resistances=set(), dc=0)
        self.scimitar_attack = self.add_ability(Action.MELEE_ATTACK,  name="Scimitar", combatant=self, to_hit=4, dmg_dice="1d6", dmg_bonus=2, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1)
        self.shortbow_attack = self.add_ability(Action.RANGED_ATTACK,  name="Shortbow", combatant=self, to_hit=4, dmg_dice="1d6", dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=64, crit_range=1)
        self.nimble_disengage = self.add_ability(BonusAction.CUNNING_DISENGAGE)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Scimitar", combatant=self, to_hit=4, dmg_dice="1d6", dmg_bonus=2, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1)
        self.danger_zone_attack = self.shortbow_attack
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = -1
        self.saving_throws[SavingThrow.DEX] = 2
        self.saving_throws[SavingThrow.CON] = 0
        self.saving_throws[SavingThrow.INT] = 0
        self.saving_throws[SavingThrow.WIS] = -1
        self.saving_throws[SavingThrow.CHA] = -1
        self.athletics = -1
        self.acrobatics = 2
        self.passive_perception = 9


    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.scimitar_attack[1]), '0', 'nop')
        self.attack_fsm.add_transition(str(self.shortbow_attack[1]), '0', 'nop')


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
        # only use it if I go before my selected target in initiative so that I can move away and use sentinel+pam
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
