import copy

from ..actions.action_types import Action, Reaction, Passive
from ..resources import Uses, ResourceRefreshType
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class
import logging

logger = logging.getLogger("Encounterra")


class Rogue2Lvl(Combatant):

    name = "Rogue 2nd LVL"
    cls = Class.ROGUE.BEFORE_SUBCLASS
    level = 2
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=15, ac=14, init_bonus=3, speed=30, spell_to_hit=0, resistances=set(), dc=13)
        self.rapier = self.add_ability(Action.MELEE_ATTACK, name="Rapier", combatant=self, to_hit=5, dmg_dice="1d8", dmg_bonus=3, dmg_type=DamageType.Piercing, attack_range=1, uses_dex=True)
        self.shortbow = self.add_ability(Action.RANGED_ATTACK,  name="Shortbow", combatant=self, to_hit=5, dmg_dice="1d6", dmg_bonus=3, dmg_type=DamageType.Piercing, attack_range=64, crit_range=1, ammo=Uses(20, ResourceRefreshType.NEVER))
        self.add_ability(Reaction.REACTION_ATTACK, name="Rapier", combatant=self, to_hit=5, dmg_dice="1d8", dmg_bonus=3, dmg_type=DamageType.Piercing, attack_range=1)
        self.add_ability(Passive.CUNNING_ACTION)
        self.add_ability(Passive.SNEAK_ATTACK)
        self.danger_zone_attack = self.shortbow
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = -1
        self.saving_throws[SavingThrow.DEX] = 5
        self.saving_throws[SavingThrow.CON] = 1
        self.saving_throws[SavingThrow.INT] = 4
        self.saving_throws[SavingThrow.WIS] = 1
        self.saving_throws[SavingThrow.CHA] = 1
        self.athletics = -1
        self.acrobatics = 5
        self.stealth = 7
        self.passive_perception = 11

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.rapier[1]), '0', 'nop')
        self.attack_fsm.add_transition(str(self.shortbow[1]), '0', 'nop')

    def new_turn(self):
        super().new_turn()
        self.already_used_sneak_attack_this_turn = False

    def on_end_of_turn(self):
        super().on_end_of_turn()
        self.already_used_sneak_attack_this_turn = False

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
            'already_used_sneak_attack_this_turn': self.already_used_sneak_attack_this_turn,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_state_machine': self.attack_fsm.state,
            'ammo': copy.deepcopy(self.ammo)
        }

    def import_resources(self, resources):
        self.movement = resources['movement']
        self.already_used_sneak_attack_this_turn = resources['already_used_sneak_attack_this_turn']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.set_state(resources['attack_state_machine'])
        self.ammo = resources['ammo']
