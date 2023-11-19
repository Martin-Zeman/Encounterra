from ..abilities.on_hit_hp_max_reduce import OnHitHpMaxReduce
from ..actions.action_types import Action, Reaction, Passive
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class
import logging

from ..utils.state_machine_template import StateMachineTemplate

logger = logging.getLogger("Encounterra")


class VampireSpawn(Combatant):

    type = "Vampire Spawn"

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, Class.MONSTER.HUMANOID, level=5, hp=82, ac=15, init_bonus=3, spell_to_hit=0, speed=30, resistances={DamageType.Slashing, DamageType.Piercing, DamageType.Bludgeoning}, dc=0)
        self.claws = self.add_ability(Action.MELEE_ATTACK,  name="Claws", combatant=self, to_hit=6, dmg_dice="2d4", dmg_bonus=3, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1)
        self.bite = self.add_ability(Action.VAMPIRIC_BITE,  name="Bite", combatant=self, to_hit=6, dmg_dice="1d6", dmg_bonus=3, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1, on_hit=OnHitHpMaxReduce('2d6', DamageType.Necrotic, 1))
        self.grapple = self.add_ability(Action.GRAPPLE_ATTACK, name="Claw Grapple", combatant=self, to_hit=6, follow_up_attack=self.bite[1])
        self.add_ability(Reaction.REACTION_ATTACK,  name="Claws", combatant=self, to_hit=6, dmg_dice="2d4", dmg_bonus=3, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1)
        self.add_ability(Passive.REGENERATION, hp=10, suppression_dmg_type=DamageType.Radiant)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 3
        self.saving_throws[SavingThrow.DEX] = 6
        self.saving_throws[SavingThrow.CON] = 3
        self.saving_throws[SavingThrow.INT] = 0
        self.saving_throws[SavingThrow.WIS] = 3
        self.saving_throws[SavingThrow.CHA] = 1
        self.athletics = 3
        self.acrobatics = 3
        self.stealth = 6
        self.passive_perception = 13

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_state('1')
        self.attack_fsm.add_state('2')
        self.attack_fsm.add_transition(str(self.grapple[1]), '0', '1')
        self.attack_fsm.add_transition(str(self.bite[1]), '1', 'nop')
        self.attack_fsm.add_transition(str(self.claws[1]), '1', 'nop')

        self.attack_fsm.add_transition(str(self.claws[1]), '0', '2')
        self.attack_fsm.add_transition(str(self.claws[1]), '2', 'nop')

    def export_resources(self):
        return {
            'movement': self.movement,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_fsm_state': self.attack_fsm.state,
        }

    def load_resources(self, resources):
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
