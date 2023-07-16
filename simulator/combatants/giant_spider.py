import copy

from simulator.abilities.on_hit_saving_throw_dmg import OnHitSavingThrowDmg
from simulator.actions.action_types import Action, Reaction
from simulator.utils.state_machine_template import StateMachineTemplate
from simulator.combatant import Combatant
from simulator.misc import DamageType, SavingThrow, Size
import logging

logger = logging.getLogger("EncounTroll")


class GiantSpider(Combatant):

    def __init__(self, name="Giant Spider"):
        super().__init__(name, level=1, hp=26, ac=14, init_bonus=3, spell_to_hit=0, speed=30, resistances=set(), dc=0)
        self.size = Size.LARGE
        self.bite_attack = self.add_ability(Action.MELEE_ATTACK,  name="Bite", combatant=self, to_hit=5, dmg_dice="1d8", dmg_bonus=3,\
                                            dmg_type=DamageType.Piercing, attack_range=1, crit_range=1,\
                                            on_hit=OnHitSavingThrowDmg("Bite Venom", SavingThrow.CON, 11, "2d8", DamageType.Poison))
        self.add_ability(Reaction.REACTION_ATTACK,  name="Morningstar", combatant=self, to_hit=4, dmg_dice="2d8", dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1)
        # TODO Add Web attack
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 2
        self.saving_throws[SavingThrow.DEX] = 3
        self.saving_throws[SavingThrow.CON] = 1
        self.saving_throws[SavingThrow.INT] = -4
        self.saving_throws[SavingThrow.WIS] = 0
        self.saving_throws[SavingThrow.CHA] = -3
        self.athletics = 2
        self.acrobatics = 3
        self.is_humanoid = False
        self.passive_perception = 10


    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.bite_attack[1]), '0', 'nop')  # Melee


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
        # only use it if I go before my selected target in initiative so that I can move away and use sentinel+pam
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
