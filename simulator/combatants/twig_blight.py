import copy

from ..actions.action_types import Action, Reaction, Passive
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class, Size
import logging

logger = logging.getLogger("Encounterra")


class TwigBlight(Combatant):

    type = "Twig Blight"

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, Class.MONSTER.PLANT, level=1, hp=4, ac=13, init_bonus=1, spell_to_hit=0, speed=20, resistances=set(), dc=0)
        self.claws = self.add_ability(Action.MELEE_ATTACK,  name="Claws", combatant=self, to_hit=3, dmg_dice="1d4", dmg_bonus=1, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Claws", combatant=self, to_hit=3, dmg_dice="1d4", dmg_bonus=1, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1)
        self.add_ability(Passive.BLINDSIGHT)
        self.build_attack_fms()
        self.size = Size.SMALL
        self.saving_throws[SavingThrow.STR] = -2
        self.saving_throws[SavingThrow.DEX] = 1
        self.saving_throws[SavingThrow.CON] = 1
        self.saving_throws[SavingThrow.INT] = -3
        self.saving_throws[SavingThrow.WIS] = -1
        self.saving_throws[SavingThrow.CHA] = -4
        self.athletics = -2
        self.acrobatics = 1
        self.passive_perception = 9


    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.claws[1]), '0', 'nop')  # Melee


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
            logger.info(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
