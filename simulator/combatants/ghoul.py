import copy

from ..actions.action_constants import TO_FACTORY
from ..actions.action_types import Action, Reaction, Passive
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class
import logging

from ..utils.state_machine_template import StateMachineTemplate

logger = logging.getLogger("Encounterra")


class Ghoul(Combatant):

    name = "Ghoul"
    cls = Class.MONSTER.UNDEAD
    level = 1
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=22, ac=12, init_bonus=2, spell_to_hit=0, speed=30, immunities={DamageType.Poison}, dc=10)
        self.bite = self.add_ability(Action.MELEE_ATTACK,  name="Bite", combatant=self, to_hit=2, dmg_dice=[(2, 6)], dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1)
        self.claws = self.add_ability(Action.PARALYZING_MELEE_ATTACK,  name="Claws", combatant=self, to_hit=4, dmg_dice=[(2, 4)], dmg_bonus=2, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1)
        reaction_claws = copy.copy(self.claws[1])
        reaction_claws.action_type = Reaction.REACTION_PARALYZING_MELEE_ATTACK
        self.reaction_factories.append((Reaction.REACTION_PARALYZING_MELEE_ATTACK, reaction_claws))
        self.aoo_factory = self.reaction_factories[-1]
        self.danger_zone_attack = self.reaction_factories[-1]
        self.melee_reaction_range = self.aoo_factory[1].range
        self.add_ability(Passive.CHARM_IMMUNITY)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 1
        self.saving_throws[SavingThrow.DEX] = 2
        self.saving_throws[SavingThrow.CON] = 0
        self.saving_throws[SavingThrow.INT] = -2
        self.saving_throws[SavingThrow.WIS] = 0
        self.saving_throws[SavingThrow.CHA] = -2
        self.athletics = 1
        self.acrobatics = 2
        self.stealth = 2
        self.passive_perception = 10

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        # self.attack_fsm.add_transition(str(self.bite[1]), '0', 'nop')
        self.attack_fsm.add_transition(str(self.claws[1]), '0', 'nop')

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
