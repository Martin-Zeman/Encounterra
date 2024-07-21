import copy

from ..abilities.action_surge import ActionSurgeFactory
from ..actions.action_types import Action, Reaction, BonusAction, Passive, FreeAction
from ..resources import Uses, ResourceRefreshType
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class
import logging

logger = logging.getLogger("Encounterra")


class Fighter2Lvl(Combatant):

    name = "Fighter 2nd LVL"
    cls = Class.FIGHTER.BEFORE_SUBCLASS
    level = 2
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=20, ac=16, init_bonus=0, spell_to_hit=0, speed=30, resistances=set(), dc=0)
        self.greatsword = self.add_ability(Action.MELEE_ATTACK,  name="Greatsword", combatant=self, to_hit=5, dmg_dice=[(2, 6)], dmg_bonus=3, dmg_type=DamageType.Slashing, attack_range=1, two_handed=True)
        self.handaxe = self.add_ability(Action.RANGED_ATTACK, name="Handaxe", combatant=self, to_hit=5, dmg_dice=[(1, 6)], dmg_bonus=3, dmg_type=DamageType.Slashing, attack_range=12, crit_range=1, uses_dex=False, ammo=Uses(2, ResourceRefreshType.NEVER))
        self.add_ability(Reaction.REACTION_ATTACK,  name="Greatsword", combatant=self, to_hit=5, dmg_dice=[(2, 6)], dmg_bonus=3, dmg_type=DamageType.Slashing, attack_range=1, two_handed=True)
        self.add_ability(BonusAction.SECOND_WIND)
        self.add_ability(FreeAction.ACTION_SURGE)
        self.add_ability(Passive.GREAT_WEAPON_FIGHTING)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 5
        self.saving_throws[SavingThrow.DEX] = 0
        self.saving_throws[SavingThrow.CON] = 4
        self.saving_throws[SavingThrow.INT] = 0
        self.saving_throws[SavingThrow.WIS] = 1
        self.saving_throws[SavingThrow.CHA] = 1
        self.athletics = 5
        self.acrobatics = 0
        self.passive_perception = 13

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.greatsword[1]), '0', 'nop')
        self.attack_fsm.add_transition(str(self.handaxe[1]), '0', 'nop')

    def export_resources(self):
        return {
            'movement': self.movement,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'second_wind_uses': self.resources[BonusAction.SECOND_WIND].export_resource(),
            'action_surge_uses': self.resources[FreeAction.ACTION_SURGE].export_resource(),
            'has_haste_action': self.has_haste_action,
            'attack_fsm_state': self.attack_fsm.state,
            'ammo': copy.deepcopy(self.ammo)
        }

    def import_resources(self, resources):
        self.movement = resources['movement']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.resources[BonusAction.SECOND_WIND].import_resource(uses=resources['second_wind_uses'])
        self.resources[FreeAction.ACTION_SURGE].import_resource(uses=resources['action_surge_uses'])
        self.attack_fsm.state = resources['attack_fsm_state']
        self.ammo = resources['ammo']

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self} taken an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
