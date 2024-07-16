import copy

from ..actions.action_types import Action, BonusAction, Reaction, Passive
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class
import logging

logger = logging.getLogger("Encounterra")


class Kobold(Combatant):

    name = "Kobold"
    cls = Class.MONSTER.HUMANOID
    level = 1
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=5, ac=12, init_bonus=2, spell_to_hit=0, speed=30, resistances=set(), dc=0)
        self.dagger = self.add_ability(Action.MELEE_ATTACK,  name="Dagger", combatant=self, to_hit=4, dmg_dice=[(1, 4)], dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1, uses_dex=True)
        self.sling = self.add_ability(Action.RANGED_ATTACK,  name="Sling", combatant=self, to_hit=4, dmg_dice=[(1, 4)], dmg_bonus=2, dmg_type=DamageType.Bludgeoning, attack_range=24, crit_range=1)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Dagger", combatant=self, to_hit=4, dmg_dice=[(1, 4)], dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1)
        self.danger_zone_attack = self.sling
        self.add_ability(Passive.PACK_TACTICS)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = -2
        self.saving_throws[SavingThrow.DEX] = 2
        self.saving_throws[SavingThrow.CON] = -1
        self.saving_throws[SavingThrow.INT] = -1
        self.saving_throws[SavingThrow.WIS] = -2
        self.saving_throws[SavingThrow.CHA] = -1
        self.athletics = -2
        self.acrobatics = 2
        self.passive_perception = 8

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.dagger[1]), '0', 'nop')
        self.attack_fsm.add_transition(str(self.sling[1]), '0', 'nop')

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
            logger.info(f"{self} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
