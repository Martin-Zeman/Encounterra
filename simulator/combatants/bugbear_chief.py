import copy

from ..actions.action_types import Action, Reaction, Passive
from ..resources import Uses, ResourceRefreshType
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class
import logging

logger = logging.getLogger("Encounterra")


class BugbearChief(Combatant):

    name = "Bugbear Chief"
    cls = Class.MONSTER.HUMANOID
    level = 4
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=65, ac=17, init_bonus=2, spell_to_hit=0, speed=30, resistances=set(), dc=0)
        self.morningstar_attack = self.add_ability(Action.MELEE_ATTACK,  name="Morningstar", combatant=self, to_hit=5, dmg_dice="2d8", dmg_bonus=3, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1)
        self.javelin_attack = self.add_ability(Action.RANGED_ATTACK,  name="Javelin", combatant=self, to_hit=4, dmg_dice="1d6", dmg_bonus=3, dmg_type=DamageType.Piercing, attack_range=24, crit_range=1, ammo=Uses(1, ResourceRefreshType.NEVER), uses_dex=False)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Morningstar", combatant=self, to_hit=5, dmg_dice="2d8", dmg_bonus=3, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1)
        self.add_ability(Passive.HEART_OF_HRUGGEK)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 3
        self.saving_throws[SavingThrow.DEX] = 2
        self.saving_throws[SavingThrow.CON] = 2
        self.saving_throws[SavingThrow.INT] = 0
        self.saving_throws[SavingThrow.WIS] = 1
        self.saving_throws[SavingThrow.CHA] = 0
        self.athletics = 3
        self.acrobatics = 2
        self.passive_perception = 11


    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_state('1')
        self.attack_fsm.add_transition(str(self.morningstar_attack[1]), '0', '1')
        self.attack_fsm.add_transition(str(self.morningstar_attack[1]), '1', 'nop')
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
