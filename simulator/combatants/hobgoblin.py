import copy

from ..abilities.on_hit_martial_advantage import OnHitMartialAdvantage
from ..actions.action_types import Action, Reaction, Passive
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class
import logging

logger = logging.getLogger("Encounterra")


class Hobgoblin(Combatant):

    name = "Hobgoblin"
    cls = Class.MONSTER.HUMANOID
    level = 1
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=11, ac=18, init_bonus=1, spell_to_hit=0, speed=30, resistances=set(), dc=0)
        self.longsword = self.add_ability(Action.MELEE_ATTACK,  name="Longsword", combatant=self, to_hit=3, dmg_dice="1d8", dmg_bonus=1, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1, on_hit=[OnHitMartialAdvantage(DamageType.Slashing)])
        self.longbow = self.add_ability(Action.RANGED_ATTACK,  name="Longbow", combatant=self, to_hit=3, dmg_dice="1d8", dmg_bonus=1, dmg_type=DamageType.Piercing, attack_range=120, crit_range=1, on_hit=[OnHitMartialAdvantage(DamageType.Piercing)])
        self.add_ability(Reaction.REACTION_ATTACK,  name="Longsword", combatant=self, to_hit=3, dmg_dice="1d8", dmg_bonus=1, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1)
        self.danger_zone_attack = self.longbow
        self.add_ability(Passive.MARTIAL_ADVANTAGE)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 1
        self.saving_throws[SavingThrow.DEX] = 1
        self.saving_throws[SavingThrow.CON] = 1
        self.saving_throws[SavingThrow.INT] = 0
        self.saving_throws[SavingThrow.WIS] = 0
        self.saving_throws[SavingThrow.CHA] = -1
        self.athletics = 1
        self.acrobatics = 2
        self.passive_perception = 10

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.longsword[1]), '0', 'nop')
        self.attack_fsm.add_transition(str(self.longbow[1]), '0', 'nop')

    def new_turn(self):
        super().new_turn()
        self.resources[Passive.MARTIAL_ADVANTAGE].reset()

    def reset(self):
        super().reset()
        self.resources[Passive.MARTIAL_ADVANTAGE].reset()

    def export_resources(self):
        return {
            'movement': self.movement,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_fsm_state': self.attack_fsm.state,
            'martial_advantage': self.resources[Passive.MARTIAL_ADVANTAGE].export_resource(),
            'ammo': copy.deepcopy(self.ammo)
        }

    def import_resources(self, resources):
        self.movement = resources['movement']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.set_state(resources['attack_fsm_state'])
        self.resources[Passive.MARTIAL_ADVANTAGE].import_resource(uses=resources['martial_advantage'])
        self.ammo = resources['ammo']

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
