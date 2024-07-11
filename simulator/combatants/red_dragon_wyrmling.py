import copy

from ..actions.action_types import Action, Reaction
from ..spells.spell import SpellStats
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class
import logging

logger = logging.getLogger("Encounterra")


class RedDragonWyrmling(Combatant):

    name = "Red Dragon Wyrmling"
    cls = Class.MONSTER.DRAGON
    level = 2
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=74, ac=17, init_bonus=0, spell_to_hit=0, speed=60, immunities={DamageType.Fire}, resistances=set(), dc=0)
        self.bite = self.add_ability(Action.MELEE_ATTACK,  name="Bite", combatant=self, to_hit=6, dmg_dice=((1, 10),), dmg_bonus=4, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1, extra_dmg=[((1, 6), DamageType.Fire)])
        self.add_ability(Action.CONIC_BREATH_WEAPON, recharge=5, dmg_dice=((7, 6),), dmg_type=DamageType.Fire, saving_throw=SavingThrow.DEX, dc=13, target_template=SpellStats.Target.CONE_15,  name="Fire Breath")
        self.add_ability(Reaction.REACTION_ATTACK,  name="Bite", combatant=self, to_hit=6, dmg_dice=((1, 10),), dmg_bonus=4, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1, extra_dmg=[((1, 6), DamageType.Fire)])
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 4
        self.saving_throws[SavingThrow.DEX] = 2
        self.saving_throws[SavingThrow.CON] = 5
        self.saving_throws[SavingThrow.INT] = 1
        self.saving_throws[SavingThrow.WIS] = 2
        self.saving_throws[SavingThrow.CHA] = 4
        self.athletics = 4
        self.acrobatics = 0
        self.stealth = 2
        self.passive_perception = 14

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.bite[1]), '0', 'nop')

    def export_resources(self):
        return {
            'movement': self.movement,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_fsm_state': self.attack_fsm.state,
            'ammo': copy.deepcopy(self.ammo),
            'breath': self.resources[Action.CONIC_BREATH_WEAPON].export_resource(),
        }

    def import_resources(self, resources):
        self.movement = resources['movement']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.set_state(resources['attack_fsm_state'])
        self.ammo = resources['ammo']
        self.resources[Action.CONIC_BREATH_WEAPON].import_resource(uses=resources['breath'])

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
