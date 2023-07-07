from simulator.actions.action_types import Action, Reaction, Passive
from simulator.combatant import Combatant
from simulator.misc import DamageType, SavingThrow
import logging

from simulator.utils.state_machine_template import StateMachineTemplate

logger = logging.getLogger("EncounTroll")


class DragonclawCultist(Combatant):

    def __init__(self, name="Dragonclaw"):
        super().__init__(name, level=5, hp=16, ac=14, init_bonus=3, spell_to_hit=0, speed=30, resistances=set(), dc=0)
        self.scimitar = self.add_ability(Action.MELEE_ATTACK,  name="Scimitar", combatant=self, to_hit=5, dmg_dice="1d6", dmg_bonus=3, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Scimitar", combatant=self, to_hit=5, dmg_dice="1d6", dmg_bonus=3, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1)
        self.add_ability(Passive.PACK_TACTICS)
        self.add_ability(Passive.FANATIC_ADVANTAGE)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = -1
        self.saving_throws[SavingThrow.DEX] = 3
        self.saving_throws[SavingThrow.CON] = 1
        self.saving_throws[SavingThrow.INT] = 0
        self.saving_throws[SavingThrow.WIS] = 2
        self.saving_throws[SavingThrow.CHA] = 1
        self.athletics = -1
        self.acrobatics = 3


    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_state('1')
        self.attack_fsm.add_transition(str(self.scimitar[1]), '0', '1')  # Melee
        self.attack_fsm.add_transition(str(self.scimitar[1]), '1', 'nop')  # Melee


    def new_turn(self):
        super().new_turn()
        self.already_used_fanatic_advantage = False

    def export_resources(self):
        return {
            'movement': self.movement,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_fsm_state': self.attack_fsm.state,
            'already_used_fanatic_advantage': self.already_used_fanatic_advantage
        }

    def load_resources(self, resources):
        self.movement = resources['movement']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.state = resources['attack_fsm_state']
        self.already_used_fanatic_advantage = resources['already_used_fanatic_advantage']

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self} taken an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
