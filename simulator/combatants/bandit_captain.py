import copy

from ..actions.action_types import Action, Reaction, Passive
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class, get_factory_of_type
import logging

logger = logging.getLogger("Encounterra")


class BanditCaptain(Combatant):

    type = "Bandit Captain"

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, Class.MONSTER.HUMANOID, level=4, hp=65, ac=15, init_bonus=3, spell_to_hit=0, speed=30, resistances=set(), dc=0)
        self.scimitar = self.add_ability(Action.MELEE_ATTACK,  name="Scimitar", combatant=self, to_hit=5, dmg_dice="1d6", dmg_bonus=3, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1)
        self.dagger = self.add_ability(Action.MELEE_ATTACK,  name="Dagger", combatant=self, to_hit=5, dmg_dice="1d4", dmg_bonus=3, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1)
        self.dagger_throw = self.add_ability(Action.RANGED_ATTACK, name="Thrown Dagger", combatant=self, to_hit=4, dmg_dice="1d4", dmg_bonus=3, dmg_type=DamageType.Piercing, attack_range=12, crit_range=1, ammo=10)
        self.add_ability(Reaction.REACTION_ATTACK, name="Scimitar", combatant=self, to_hit=5, dmg_dice="1d6", dmg_bonus=3, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1)
        self.add_ability(Reaction.PARRY, ac=2)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 4
        self.saving_throws[SavingThrow.DEX] = 5
        self.saving_throws[SavingThrow.CON] = 2
        self.saving_throws[SavingThrow.INT] = 2
        self.saving_throws[SavingThrow.WIS] = 2
        self.saving_throws[SavingThrow.CHA] = 2
        self.athletics = 4
        self.acrobatics = 3
        self.passive_perception = 10


    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_state('1')
        self.attack_fsm.add_state('2')
        self.attack_fsm.add_state('3')
        self.attack_fsm.add_transition(str(self.scimitar[1]), '0', '1')
        self.attack_fsm.add_transition(str(self.scimitar[1]), '1', '2')
        self.attack_fsm.add_transition(str(self.dagger[1]), '2', 'nop')
        self.attack_fsm.add_transition(str(self.dagger_throw[1]), '0', '3')
        self.attack_fsm.add_transition(str(self.dagger_throw[1]), '3', 'nop')


    def export_resources(self):
        return {
            'movement': self.movement,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_fsm_state': self.attack_fsm.state,
            'ammo': copy.deepcopy(self.ammo)
        }

    def load_resources(self, resources):
        self.movement = resources['movement']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.set_state(resources['attack_fsm_state'])
        self.ammo = resources['ammo']

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None

    def prompt_after_hit_reaction(self, attack, attacking_combatant, attack_roll):
        if self.has_reaction and attack_roll < self.ac + 2:
            parry_factory = get_factory_of_type(self.reaction_factories, Reaction.PARRY)
            return parry_factory.create() if parry_factory else None
        elif attack_roll >= self.ac + 2:
            logger.info("Parry would not suffice")
        return None
