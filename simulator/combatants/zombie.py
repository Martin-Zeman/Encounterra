from ..abilities.on_hit_hp_max_reduce_and_heal import OnHitHpMaxReduceAndHeal
from ..actions.action_types import Action, Reaction, Passive
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class
import logging

from ..utils.state_machine_template import StateMachineTemplate

logger = logging.getLogger("Encounterra")


class Zombie(Combatant):

    name = "Zombie"
    cls = Class.MONSTER.UNDEAD
    level = 1
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=22, ac=8, init_bonus=-2, spell_to_hit=0, speed=20, immunities={DamageType.Poison}, dc=0)
        self.slam = self.add_ability(Action.MELEE_ATTACK,  name="Slam", combatant=self, to_hit=3, dmg_dice="1d6", dmg_bonus=1, dmg_type=DamageType.Bludgeoning, attack_range=1, crit_range=1)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Slam", combatant=self, to_hit=3, dmg_dice="1d6", dmg_bonus=1, dmg_type=DamageType.Bludgeoning, attack_range=1, crit_range=1)
        self.add_ability(Passive.UNDEAD_FORTITUDE)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 1
        self.saving_throws[SavingThrow.DEX] = -2
        self.saving_throws[SavingThrow.CON] = 3
        self.saving_throws[SavingThrow.INT] = -4
        self.saving_throws[SavingThrow.WIS] = 0
        self.saving_throws[SavingThrow.CHA] = -3
        self.athletics = 1
        self.acrobatics = -2
        self.stealth = -2
        self.passive_perception = 8

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.slam[1]), '0', 'nop')

    def export_resources(self):
        return {
            'movement': self.movement,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_fsm_state': self.attack_fsm.state,
        }

    def import_resources(self, resources):
        self.movement = resources['movement']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.state = resources['attack_fsm_state']

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self} taken an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
