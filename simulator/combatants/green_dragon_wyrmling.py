import copy

from setuptools.config.setupcfg import Target

from ..abilities.on_hit_saving_throw_dmg import OnHitSavingThrowDmg
from ..actions.action_types import Action, Reaction
from ..spells.spell import SpellStats
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Size, Class
import logging

logger = logging.getLogger("Encounterra")


class GreenDragonWyrmling(Combatant):

    name = "Green Dragon Wyrmling"
    cls = Class.MONSTER.DRAGON
    level = 2
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=38, ac=17, init_bonus=1, spell_to_hit=0, speed=60, immunities={DamageType.Poison}, resistances=set(), dc=0)
        self.bite = self.add_ability(Action.MELEE_ATTACK,  name="Bite", combatant=self, to_hit=4, dmg_dice="1d10", dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1, extra_dmg=[('1d6', DamageType.Poison)])
        self.add_ability(Action.CONIC_BREATH_WEAPON, recharge=5, dmg_dice='6d6', dmg_type=DamageType.Poison, saving_throw=SavingThrow.CON, dc=11, target_template=SpellStats.Target.CONE_15,  name="Poison Breath")
        self.add_ability(Reaction.REACTION_ATTACK,  name="Bite", combatant=self, to_hit=4, dmg_dice="1d10", dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1, extra_dmg=[('1d6', DamageType.Poison)])
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 2
        self.saving_throws[SavingThrow.DEX] = 3
        self.saving_throws[SavingThrow.CON] = 3
        self.saving_throws[SavingThrow.INT] = 2
        self.saving_throws[SavingThrow.WIS] = 2
        self.saving_throws[SavingThrow.CHA] = 3
        self.athletics = 2
        self.acrobatics = 1
        self.stealth = 3
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
