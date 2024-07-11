import copy

from ..abilities.rage import RageFactory
from ..actions.action_types import Action, Reaction, BonusAction, Passive
from ..resources import Uses, ResourceRefreshType
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class, SpellcastingResourceType
import logging

logger = logging.getLogger("Encounterra")


class OathOfVengeancePaladin5Lvl(Combatant):

    name = "Oath of Vengeance Paladin 5th LVL"
    cls = Class.PALADIN.OATH_OF_VENGEANCE
    level = 5
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=44, ac=18, init_bonus=-1, spell_to_hit=5, speed=30, resistances=set(), dc=13)
        self.battleaxe = self.add_ability(Action.MELEE_ATTACK,  name="Battleaxe", combatant=self, to_hit=7, dmg_dice=((1, 8),), dmg_bonus=4, dmg_type=DamageType.Slashing, attack_range=1)
        self.javelin = self.add_ability(Action.RANGED_ATTACK, name="Javelin", combatant=self, to_hit=7, dmg_dice=((1, 6),), dmg_bonus=4, dmg_type=DamageType.Piercing, attack_range=24, crit_range=1, ammo=Uses(4, ResourceRefreshType.NEVER), uses_dex=False)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Battleaxe", combatant=self, to_hit=7, dmg_dice=((1, 8),), dmg_bonus=4, dmg_type=DamageType.Slashing, attack_range=1)
        self.add_ability(Action.LAY_ON_HANDS)
        self.add_ability(Passive.SPELLCASTING, resource_type=SpellcastingResourceType.SPELLSLOTS)
        self.add_ability(Passive.DUELING)
        self.add_ability(Passive.DIVINE_SMITE)
        self.add_ability(Action.BLESS)
        self.add_ability(BonusAction.MISTY_STEP)
        self.add_ability(Action.HOLD_PERSON)
        self.add_ability(Action.CURE_WOUNDS, mod=2)
        self.add_ability(BonusAction.SHIELD_OF_FAITH)
        channel_divinity_uses = Uses(1, ResourceRefreshType.SHORT_REST)
        self.resources[Passive.CHANNEL_DIVINITY] = channel_divinity_uses
        self.add_ability(BonusAction.VOW_OF_ENMITY)
        # self.add_ability(Action.ABJURE_ENEMY, resource=channel_divinity_uses)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 4
        self.saving_throws[SavingThrow.DEX] = -1
        self.saving_throws[SavingThrow.CON] = 2
        self.saving_throws[SavingThrow.INT] = 0
        self.saving_throws[SavingThrow.WIS] = 3
        self.saving_throws[SavingThrow.CHA] = 4
        self.athletics = 7
        self.acrobatics = -1
        self.passive_perception = 11

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_new_state('1')  # attacked with melee
        self.attack_fsm.add_new_state('2')  # attacked with ranged
        self.attack_fsm.add_transition(str(self.battleaxe[1]), '0', '1')
        self.attack_fsm.add_transition(str(self.battleaxe[1]), '1', 'nop')
        self.attack_fsm.add_transition(str(self.javelin[1]), '0', '2')
        self.attack_fsm.add_transition(str(self.javelin[1]), '2', 'nop')

    def export_resources(self):
        return {
            'movement': self.movement,
            'spellslots': self.spellslots.export_resource(),
            'channel_divinity': self.resources[Passive.CHANNEL_DIVINITY].export_resource(),
            'cast_leveled_spell': self.already_cast_leveled_spell_this_turn,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'lay_on_hands_pool': self.resources[Action.LAY_ON_HANDS].export_resource(),
            'attack_fsm_state': self.attack_fsm.state,
            'ammo': copy.deepcopy(self.ammo)
        }

    def import_resources(self, resources):
        self.movement = resources['movement']
        self.spellslots.import_resource(spellslots=resources['spellslots'])
        self.resources[Passive.CHANNEL_DIVINITY].import_resource(uses=resources['channel_divinity'])
        self.already_cast_leveled_spell_this_turn = resources['cast_leveled_spell']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.resources[Action.LAY_ON_HANDS].import_resource(uses=resources['lay_on_hands_pool'])
        self.attack_fsm.state = resources['attack_fsm_state']
        self.ammo = resources['ammo']

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self} taken an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
