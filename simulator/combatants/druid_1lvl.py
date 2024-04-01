import copy
from functools import cache

from ..abilities.wildshape import WildshapeFactory
from ..actions.action_types import Action, Reaction, BonusAction, Passive
from ..actions.moon_druid_action_plan_strategy import MoonDruidActionPlanStrategy
from ..resources import Uses, ResourceRefreshType
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class, SpellcastingResourceType
import logging

logger = logging.getLogger("Encounterra")


class Druid1Lvl(Combatant):

    name = "Druid 1st LVL"
    cls = Class.DRUID.BEFORE_SUBCLASS
    level = 1
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=11, ac=12, init_bonus=1, speed=35, spell_to_hit=5, resistances=set(), dc=13)
        self.quarterstaff = self.add_ability(Action.MELEE_ATTACK, name="Quarterstaff", combatant=self, to_hit=2, dmg_dice="1d8", dmg_bonus=0, dmg_type=DamageType.Bludgeoning, attack_range=1)
        self.shillelagh_quarterstaff = self.add_ability(Action.MELEE_ATTACK, name="Shillelagh Quarterstaff", combatant=self, to_hit=5, dmg_dice="1d8", dmg_bonus=3, dmg_type=DamageType.BludgeoningMagical, attack_range=1, ammo=Uses(0, ResourceRefreshType.NEVER), suppress=True)
        self.add_ability(Reaction.REACTION_ATTACK, name="Quarterstaff", combatant=self, to_hit=2, dmg_dice="1d8", dmg_bonus=0, dmg_type=DamageType.Bludgeoning, attack_range=1)
        self.add_ability(Passive.SPELLCASTING, resource_type=SpellcastingResourceType.SPELLSLOTS)
        self.add_ability(Action.FAERIE_FIRE)
        self.add_ability(Action.THUNDERWAVE)
        self.add_ability(BonusAction.HEALING_WORD, mod=3)
        self.add_ability(BonusAction.SHILLELAGH, original_attack=self.quarterstaff[1], new_attack=self.shillelagh_quarterstaff[1])
        self.danger_zone_attack = self.quarterstaff
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 0
        self.saving_throws[SavingThrow.DEX] = 1
        self.saving_throws[SavingThrow.CON] = 3
        self.saving_throws[SavingThrow.INT] = 4
        self.saving_throws[SavingThrow.WIS] = 5
        self.saving_throws[SavingThrow.CHA] = 1
        self.athletics = 0
        self.acrobatics = -1
        self.passive_perception = 13

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.quarterstaff[1]), '0', 'nop')
        self.attack_fsm.add_transition(str(self.shillelagh_quarterstaff[1]), '0', 'nop')

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                        extra={"team": self.team_color})
            return aoo
        return None

    def export_resources(self):
        return {
            'movement': self.movement,
            'spellslots': self.spellslots.export_resource(),
            'cast_leveled_spell': self.already_cast_leveled_spell_this_turn,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_state_machine': self.attack_fsm.state,
            'ammo': copy.deepcopy(self.ammo)
        }

    def import_resources(self, resources):
        self.movement = resources['movement']
        self.spellslots.import_resource(spellslots=resources['spellslots'])
        self.already_cast_leveled_spell_this_turn = resources['cast_leveled_spell']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.set_state(resources['attack_state_machine'])
        self.ammo = resources['ammo']

