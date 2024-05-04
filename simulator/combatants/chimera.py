import copy
import sys

from ..actions.action_types import Action, Reaction
from ..resources import Uses, ResourceRefreshType
from ..spells.spell import SpellStats
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Size, Class
import logging

logger = logging.getLogger("Encounterra")


class Chimera(Combatant):

    name = "Chimera"
    cls = Class.MONSTER.MONSTROSITY
    level = 6
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=114, ac=14, init_bonus=0, spell_to_hit=0, speed=60, resistances=set(), dc=0)
        self.size = Size.LARGE
        self.horns = self.add_ability(Action.MELEE_ATTACK,  name="Horns", combatant=self, to_hit=7, dmg_dice="1d12", dmg_bonus=4, dmg_type=DamageType.Bludgeoning, attack_range=1, crit_range=1)
        self.bite = self.add_ability(Action.MELEE_ATTACK,  name="Bite", combatant=self, to_hit=7, dmg_dice="2d6", dmg_bonus=4, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1)
        self.claws = self.add_ability(Action.MELEE_ATTACK,  name="Claws", combatant=self, to_hit=7, dmg_dice="2d6", dmg_bonus=4, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1)
        self.add_ability(Reaction.REACTION_ATTACK, name="Claws", combatant=self, to_hit=7, dmg_dice="2d6", dmg_bonus=4, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1)
        self.fire_breath = self.add_ability(Action.CONIC_BREATH_WEAPON_ATTACK, recharge=5, dmg_dice='7d8', dmg_type=DamageType.Fire, saving_throw=SavingThrow.DEX, dc=15, target_template=SpellStats.Target.CONE_15, name="Fire Breath")
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 4
        self.saving_throws[SavingThrow.DEX] = 0
        self.saving_throws[SavingThrow.CON] = 4
        self.saving_throws[SavingThrow.INT] = -4
        self.saving_throws[SavingThrow.WIS] = 2
        self.saving_throws[SavingThrow.CHA] = 0
        self.athletics = 4
        self.acrobatics = 0
        self.stealth = 0
        self.passive_perception = 18

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_state('1')
        self.attack_fsm.add_state('2')
        self.attack_fsm.add_state('3')
        self.attack_fsm.add_state('4')
        self.attack_fsm.add_state('5')
        self.attack_fsm.add_state('6')
        self.attack_fsm.add_state('7')
        self.attack_fsm.add_state('8')
        self.attack_fsm.add_state('9')
        self.attack_fsm.add_state('10')
        self.attack_fsm.add_state('11')
        self.attack_fsm.add_transition(str(self.bite[1]), '0', '1')
        self.attack_fsm.add_transition(str(self.horns[1]), '1', '8')
        self.attack_fsm.add_transition(str(self.claws[1]), '8', 'nop')
        self.attack_fsm.add_transition(str(self.claws[1]), '1', '5')
        self.attack_fsm.add_transition(str(self.fire_breath[1]), '5', 'nop')
        self.attack_fsm.add_transition(str(self.horns[1]), '5', 'nop')
        self.attack_fsm.add_transition(str(self.horns[1]), '0', '2')
        self.attack_fsm.add_transition(str(self.bite[1]), '2', '8')
        self.attack_fsm.add_transition(str(self.claws[1]), '2', '6')
        self.attack_fsm.add_transition(str(self.claws[1]), '0', '3')
        self.attack_fsm.add_transition(str(self.bite[1]), '3', '5')
        self.attack_fsm.add_transition(str(self.horns[1]), '3', '6')
        self.attack_fsm.add_transition(str(self.fire_breath[1]), '3', '7')
        self.attack_fsm.add_transition(str(self.fire_breath[1]), '0', '4')
        self.attack_fsm.add_transition(str(self.claws[1]), '4', '11')
        self.attack_fsm.add_transition(str(self.bite[1]), '11', 'nop')
        self.attack_fsm.add_transition(str(self.horns[1]), '11', 'nop')
        self.attack_fsm.add_transition(str(self.bite[1]), '4', '9')
        self.attack_fsm.add_transition(str(self.horns[1]), '4', '10')
        self.attack_fsm.add_transition(str(self.claws[1]), '10', 'nop')
        self.attack_fsm.add_transition(str(self.bite[1]), '10', 'nop')
        self.attack_fsm.add_transition(str(self.horns[1]), '9', 'nop')
        self.attack_fsm.add_transition(str(self.claws[1]), '9', 'nop')
        self.attack_fsm.add_transition(str(self.bite[1]), '6', 'nop')
        self.attack_fsm.add_transition(str(self.fire_breath[1]), '6', 'nop')
        self.attack_fsm.add_transition(str(self.bite[1]), '7', 'nop')
        self.attack_fsm.add_transition(str(self.horns[1]), '7', 'nop')

    def export_resources(self):
        return {
            'movement': self.movement,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_fsm_state': self.attack_fsm.state,
            'ammo': copy.deepcopy(self.ammo),
            'breath': self.resources[Action.CONIC_BREATH_WEAPON_ATTACK].export_resource(),
        }

    def import_resources(self, resources):
        self.movement = resources['movement']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.set_state(resources['attack_fsm_state'])
        self.ammo = resources['ammo']
        self.resources[Action.CONIC_BREATH_WEAPON_ATTACK].import_resource(uses=resources['breath'])

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
