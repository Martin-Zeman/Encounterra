from simulator.actions.action_selector import get_best_actions
from simulator.utils.state_machine_template import StateMachineTemplate
from simulator.combatant import Combatant
from simulator.actions.movement import GetUpFactory
from simulator.misc import DamageType, SavingThrow, Conditions
from simulator.actions.action_factory import *
from simulator.actions.action_types import *
import logging

logger = logging.getLogger("EncounTroll")




class TotemBarbarian5Lvl(Combatant):

    def __init__(self, effect_tracker, name="TotemBarbarian5Lvl"):
        super().__init__(effect_tracker, name, level=5, hp=61, ac=15, init_bonus=1, spell_to_hit=0, speed=40, resistances=set(), dc=15)
        self.axe = self.add_ability(Action.MELEE_ATTACK,  name="Two-handed axe", combatant=self, to_hit=7, dmg_dice="1d12", dmg_bonus=4, dmg_type=DamageType.Slashing, attack_range=1, max_num=2)
        self.javelin_attack = self.add_ability(Action.RANGED_ATTACK, name="Javelin", combatant=self, to_hit=4, dmg_dice="1d6", dmg_bonus=4, dmg_type=DamageType.Piercing, attack_range=24, crit_range=1)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Two-handed axe", combatant=self, to_hit=7, dmg_dice="1d12", dmg_bonus=4, dmg_type=DamageType.Slashing, attack_range=1)
        self.add_ability(BonusAction.TOTEM_RAGE)
        self.add_ability(Passive.MULTIATTACK, num_attacks=2)
        self.add_ability(Passive.DANGER_SENSE)
        self.axe_recklessly = self.add_ability(Action.RECKLESS_ATTACK, name="Two-handed axe recklessly", combatant=self, to_hit=7, dmg_dice="1d12", dmg_bonus=4, dmg_type=DamageType.Slashing, attack_range=1, max_num=2)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 7
        self.saving_throws[SavingThrow.DEX] = 1
        self.saving_throws[SavingThrow.CON] = 7
        self.saving_throws[SavingThrow.INT] = 0
        self.saving_throws[SavingThrow.WIS] = 0
        self.saving_throws[SavingThrow.CHA] = 1


    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()  # Initialized here to avoid pickling error when multiprocessing
        self.attack_fsm.add_state('1')  # attacked with melee
        self.attack_fsm.add_state('2')  # attacked with melee recklessly
        self.attack_fsm.add_transition(str(self.axe[1]), '0', '1')  # Melee
        self.attack_fsm.add_transition(str(self.axe[1]), '1', 'nop')  # Melee
        self.attack_fsm.add_transition(str(self.axe_recklessly[1]), '0', '2')
        self.attack_fsm.add_transition(str(self.axe_recklessly[1]), '2', 'nop')
        self.attack_fsm.add_transition(str(self.javelin_attack[1]), '0', 'nop')


    def get_action(self, battle_map):
        """
        Calculates the next best action. The algorithm works in two phases. In the first phase when the combatant still has movement left,
        it follows the steps described above. In the second phase, once the combatant reaches the target destination or runs out of movement
        the best action is recalculated every time to react to any possible changes on the battle_map.
        :param battle_map:
        :return: the next best actoid
        """
        if self.is_affected_by(Conditions.PRONE):
            return GetUpFactory().create()
        distances, shortest_paths = battle_map.calc_dijkstra(self)  # Has to be recalculated every time (due to forced movement etc.)
        if self.action_plan:
            if isinstance(self.action_plan[0], MovementIncrement) and self.movement:
                return self.action_plan.pop(0)
        self.action_plan = get_best_actions(self, battle_map, distances, shortest_paths)
        if not self.action_plan:
            return None  # Either no action possible or all actions already used
        return self.action_plan.pop(0)


    def export_resources(self):
        return {
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'curr_rage_uses': self.curr_rage_uses,
            'has_haste_action': self.has_haste_action,
            'attack_fsm_state': self.attack_fsm.state
        }

    def load_resources(self, resources):
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.curr_rage_uses = resources['curr_rage_uses']
        self.attack_fsm.state = resources['attack_fsm_state']

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self} taken an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
