import copy

from ..actions.action_types import Action, BonusAction, Reaction, Passive, MetaAction
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, get_factory_of_type, SavingThrow, Class, SpellcastingResourceType
import logging

logger = logging.getLogger("Encounterra")


class DraconicSorcerer3Lvl(Combatant):

    name = "Draconic Sorcerer 3rd LVL"
    cls = Class.SORCERER.DRACONIC_BLOODLINE
    level = 3
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=23, ac=15, init_bonus=2, speed=30, spell_to_hit=5, resistances=set(), dc=13)
        self.quarterstaff = self.add_ability(Action.MELEE_ATTACK, name="Quarterstaff", combatant=self, to_hit=1, dmg_dice=[(1, 8)], dmg_bonus=-1, dmg_type=DamageType.Bludgeoning, attack_range=1)
        self.add_ability(Reaction.REACTION_ATTACK, name="Quarterstaff", combatant=self, to_hit=1, dmg_dice=[(1, 8)], dmg_bonus=-1, dmg_type=DamageType.Bludgeoning, attack_range=1)
        self.firebolt = self.add_ability(Action.FIREBOLT)
        self.add_ability(Action.RAY_OF_FROST)
        self.danger_zone_attack = self.firebolt
        self.add_ability(Passive.DRACONIC_RESILIENCE)
        self.add_ability(Passive.SPELLCASTING, resource_type=SpellcastingResourceType.SPELLSLOTS)
        self.add_ability(BonusAction.MISTY_STEP)
        self.add_ability(Action.SCORCHING_RAY)
        self.add_ability(Reaction.SHIELD)
        self.add_ability(Passive.METAMAGIC, sorcery_points=self.level)
        self.add_ability(MetaAction.QUICKENED_SPELL)
        self.add_ability(MetaAction.TWINNED_SPELL)
        self.add_ability(Action.HOLD_PERSON)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = -1
        self.saving_throws[SavingThrow.DEX] = 2
        self.saving_throws[SavingThrow.CON] = 4
        self.saving_throws[SavingThrow.INT] = 1
        self.saving_throws[SavingThrow.WIS] = 1
        self.saving_throws[SavingThrow.CHA] = 5
        self.athletics = -1
        self.acrobatics = 2
        self.passive_perception = 11

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.quarterstaff[1]), '0', 'nop')

    def prompt_aoo(self, moving_combatant):
        return None  # Saving reaction for Shield

    def export_resources(self):
        return {
            'movement': self.movement,
            'spellslots': self.spellslots.export_resource(),
            'sorcery_points': self.resources[Passive.METAMAGIC].export_resource(),
            'cast_leveled_spell': self.already_cast_leveled_spell_this_turn,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_state_machine': self.attack_fsm.state
        }

    def import_resources(self, resources):
        self.movement = resources['movement']
        self.spellslots.import_resource(spellslots=resources['spellslots'])
        self.resources[Passive.METAMAGIC].import_resource(uses=resources['sorcery_points'])
        self.already_cast_leveled_spell_this_turn = resources['cast_leveled_spell']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.set_state(resources['attack_state_machine'])

    def prompt_after_hit_reaction(self, attacker, attack, attack_roll):
        if self.spellslots.has_resource(level=1) and self.has_reaction and attack_roll < self.ac + 5:
            shield_factory = get_factory_of_type(self.reaction_factories, Reaction.SHIELD)
            # logger.info(f"{self.name} casts Shield", extra={"team": self.team_color})
            return shield_factory.create() if shield_factory else None
        elif attack_roll >= self.ac + 5:
            logger.info("Shield would not suffice")
        elif self.has_reaction:
            logger.info(f"{self.name} cannot cast Shield. Out of spellslots.", extra={"team": self.team_color})
        return None
