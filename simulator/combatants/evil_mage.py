import copy

from ..actions.action_types import Action, BonusAction, Reaction, Passive
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..spellslots import Spellslots, spellslot_factory
from ..misc import DamageType, SavingThrow, Class, SpellcastingResourceType
import logging

logger = logging.getLogger("Encounterra")


class EvilMage(Combatant):

    name = "Evil Mage"
    cls = Class.MONSTER.HUMANOID
    level = 4
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=22, ac=12, init_bonus=2, speed=30, spell_to_hit=5, resistances=set(), dc=13)
        self.staff = self.add_ability(Action.MELEE_ATTACK, name="Quarterstaff", combatant=self, to_hit=1, dmg_dice="1d8", dmg_bonus=-1,
                         dmg_type=DamageType.Bludgeoning, attack_range=1)
        self.add_ability(Reaction.REACTION_ATTACK, name="Quarterstaff", combatant=self, to_hit=1, dmg_dice="1d8", dmg_bonus=-1,
                         dmg_type=DamageType.Bludgeoning, attack_range=1)
        self.shocking_grasp = self.add_ability(Action.SHOCKING_GRASP)
        self.danger_zone_attack = self.shocking_grasp
        self.add_ability(Passive.SPELLCASTING, resource_type=SpellcastingResourceType.SPELLSLOTS, cls=Class.WIZARD.ABJURATION)
        self.add_ability(Action.MAGIC_MISSILE)
        self.add_ability(BonusAction.MISTY_STEP)
        self.add_ability(Action.HOLD_PERSON)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = -1
        self.saving_throws[SavingThrow.DEX] = 2
        self.saving_throws[SavingThrow.CON] = 6
        self.saving_throws[SavingThrow.INT] = 1
        self.saving_throws[SavingThrow.WIS] = 1
        self.saving_throws[SavingThrow.CHA] = 7
        self.athletics = 2
        self.acrobatics = 2
        self.passive_perception = 11

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.staff[1]), '0', 'nop')

    def export_resources(self):
        return {
            'movement': self.movement,
            'spellslots': self.spellslots.export_resource(),
            'cast_leveled_spell': self.already_cast_leveled_spell_this_turn,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_state_machine': self.attack_fsm.state
        }

    def import_resources(self, resources):
        self.movement = resources['movement']
        self.spellslots.import_resource(spellslots=resources['spellslots'])
        self.already_cast_leveled_spell_this_turn = resources['cast_leveled_spell']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.set_state(resources['attack_state_machine'])

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self} taken an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
