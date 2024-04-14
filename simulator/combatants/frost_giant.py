import copy

from ..actions.action_types import Action, Reaction
from ..resources import ResourceRefreshType, Uses
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Size, Class
import logging

logger = logging.getLogger("Encounterra")


class FrostGiant(Combatant):

    name = "Frost Giant"
    cls = Class.MONSTER.GIANT
    level = 5
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=138, ac=15, init_bonus=-1, spell_to_hit=0, speed=40, immunities={DamageType.Cold}, resistances=set(), dc=0)
        self.size = Size.HUGE
        self.axe = self.add_ability(Action.MELEE_ATTACK,  name="Greataxe", combatant=self, to_hit=9, dmg_dice="3d12", dmg_bonus=6, dmg_type=DamageType.Slashing, attack_range=3)
        self.rock = self.add_ability(Action.RANGED_ATTACK, name="Rock", combatant=self, to_hit=9, dmg_dice="4d10", dmg_bonus=6,
                                            dmg_type=DamageType.Bludgeoning, attack_range=48, crit_range=1, ammo=Uses(2, ResourceRefreshType.NEVER), uses_dex=False)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Greataxe", combatant=self, to_hit=9, dmg_dice="3d12", dmg_bonus=6, dmg_type=DamageType.Slashing, attack_range=3)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 6
        self.saving_throws[SavingThrow.DEX] = -1
        self.saving_throws[SavingThrow.CON] = 8
        self.saving_throws[SavingThrow.INT] = -1
        self.saving_throws[SavingThrow.WIS] = 3
        self.saving_throws[SavingThrow.CHA] = 4
        self.athletics = 6
        self.acrobatics = -1
        self.passive_perception = 13

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_state('1')
        self.attack_fsm.add_transition(str(self.axe[1]), '0', '1')
        self.attack_fsm.add_transition(str(self.axe[1]), '1', 'nop')
        self.attack_fsm.add_transition(str(self.rock[1]), '0', 'nop')

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
            logger.info(f"{self} taken an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
