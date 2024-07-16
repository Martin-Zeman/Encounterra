import copy

from ..actions.action_types import Action, Reaction
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Size, Class
import logging

logger = logging.getLogger("Encounterra")


class YoungBlueDragon(Combatant):

    name = "Young Blue Dragon"
    cls = Class.MONSTER.DRAGON
    level = 9
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=152, ac=18, init_bonus=0, spell_to_hit=0, speed=80, immunities={DamageType.Lightning}, resistances=set(), dc=0)
        self.size = Size.LARGE
        self.claw = self.add_ability(Action.MELEE_ATTACK,  name="Claw", combatant=self, to_hit=9, dmg_dice=[(2, 6)], dmg_bonus=5, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1)
        self.bite = self.add_ability(Action.MELEE_ATTACK,  name="Bite", combatant=self, to_hit=9, dmg_dice=[(2, 10)], dmg_bonus=5, dmg_type=DamageType.Piercing, attack_range=2, crit_range=1, extra_dmg=[((1, 10), DamageType.Lightning)])
        self.add_ability(Action.LINE_BREATH_WEAPON, recharge=5, dmg_dice=[(10, 10)], dmg_type=DamageType.Lightning, saving_throw=SavingThrow.DEX, dc=16, length=12, width=1,  name="Lightning Breath")
        self.add_ability(Reaction.REACTION_ATTACK,  name="Bite", combatant=self, to_hit=9, dmg_dice=[(2, 10)], dmg_bonus=5, dmg_type=DamageType.Piercing, attack_range=2, crit_range=1, extra_dmg=[((1, 6), DamageType.Lightning)])
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 5
        self.saving_throws[SavingThrow.DEX] = 4
        self.saving_throws[SavingThrow.CON] = 8
        self.saving_throws[SavingThrow.INT] = 2
        self.saving_throws[SavingThrow.WIS] = 5
        self.saving_throws[SavingThrow.CHA] = 7
        self.athletics = 5
        self.acrobatics = 0
        self.stealth = 4
        self.passive_perception = 19

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_new_state('1')
        self.attack_fsm.add_new_state('2')
        self.attack_fsm.add_new_state('3')
        self.attack_fsm.add_new_state('4')
        self.attack_fsm.add_new_state('5')
        self.attack_fsm.add_transition(str(self.claw[1]), '0', '1')
        self.attack_fsm.add_transition(str(self.claw[1]), '1', '3')
        self.attack_fsm.add_transition(str(self.bite[1]), '1', '4')
        self.attack_fsm.add_transition(str(self.bite[1]), '3', 'nop')
        self.attack_fsm.add_transition(str(self.claw[1]), '4', 'nop')
        self.attack_fsm.add_transition(str(self.bite[1]), '0', '2')
        self.attack_fsm.add_transition(str(self.claw[1]), '2', '5')
        self.attack_fsm.add_transition(str(self.claw[1]), '5', 'nop')

    def export_resources(self):
        return {
            'movement': self.movement,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_fsm_state': self.attack_fsm.state,
            'ammo': copy.deepcopy(self.ammo),
            'breath': self.resources[Action.LINE_BREATH_WEAPON].export_resource(),
        }

    def import_resources(self, resources):
        self.movement = resources['movement']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.set_state(resources['attack_fsm_state'])
        self.ammo = resources['ammo']
        self.resources[Action.LINE_BREATH_WEAPON].import_resource(uses=resources['breath'])

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
