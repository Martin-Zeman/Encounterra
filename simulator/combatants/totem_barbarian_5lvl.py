from simulator.actions.action_fsms import AttackStateMachineTemplate
from simulator.combatant import Combatant
from simulator.actions.movement import MovementGenerator, GetUpFactory
from simulator.feasibility import get_feasible_factories
from simulator.misc import DamageType, SavingThrow, Conditions
from simulator.action_factory import *
from simulator.action_types import *
from simulator.actions.actoid import ActoidFlags
import numpy as np
import logging

logger = logging.getLogger(__name__)




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
        self.movement_generator = None
        self.selected_target = None
        self.path = None
        self.saving_throws[SavingThrow.STR] = 7
        self.saving_throws[SavingThrow.DEX] = 1
        self.saving_throws[SavingThrow.CON] = 7
        self.saving_throws[SavingThrow.INT] = 0
        self.saving_throws[SavingThrow.WIS] = 0
        self.saving_throws[SavingThrow.CHA] = 1


    def build_attack_fms(self):
        self.attack_fsm = AttackStateMachineTemplate()  # Initialized here to avoid pickling error when multiprocessing
        self.attack_fsm.add_state('1')  # attacked with melee
        self.attack_fsm.add_state('2')  # attacked with melee recklessly
        self.attack_fsm.add_transition(str(self.axe[1]), '0', '1')  # Melee
        self.attack_fsm.add_transition(str(self.axe[1]), '1', 'nop')  # Melee
        self.attack_fsm.add_transition(str(self.axe_recklessly[1]), '0', '2')
        self.attack_fsm.add_transition(str(self.axe_recklessly[1]), '2', 'nop')
        self.attack_fsm.add_transition(str(self.javelin_attack[1]), '0', 'nop')


    def plan_path(self, battle_map, target_combatant, target_position):
        self.path = battle_map.get_path_to(self, target_combatant)
        if not self.path:
            logger.info(f"{self.name} has nowhere to go. Using dodge action", extra={"team": self.team_color})
            raise RuntimeError
        self.movement_generator = MovementGenerator(self, self.path).get_generator()
        self.target_position_cache = target_position

    def get_action(self, battle_map):
        if self.is_affected_by(Conditions.PRONE) and self.movement >= self.speed / 2:
            return GetUpFactory().create()
        # TODO if it gets surrounded it will not attack and just dodge
        # TODO Figure out how to avoid recalculating this all the time. Maybe I could separate plan_turn and get action. plan_turn would be
        #  called once and get_action multiple times like now
        # TODO Reckless attack still seems to pay off even against many enemies, this is suspicious
        feasible_action_factories = get_feasible_factories(self.action_factories, self, battle_map)
        feasible_bonus_action_factories = get_feasible_factories(self.bonus_action_factories, self, battle_map)
        feasible_haste_action_factories = get_feasible_factories(self.haste_action_factories, self, battle_map)
        if len(feasible_action_factories) > 0 or len(feasible_bonus_action_factories) > 0 or len(feasible_haste_action_factories) > 0:
            feasible_actions = list(filter(lambda item: item is not None, [f[1].create_best(self, battle_map) for f in feasible_action_factories]))
            feasible_bonus_actions = list(filter(lambda item: item is not None, [f[1].create_best(self, battle_map) for f in feasible_bonus_action_factories]))
            feasible_haste_actions = list(filter(lambda item: item is not None, [f[1].create_best(self, battle_map) for f in feasible_haste_action_factories]))

            action_threats = [(fa.calculate_threat(self, battle_map), fa) for fa in feasible_actions]
            bonus_action_threats = [(fba.calculate_threat(self, battle_map), fba) for fba in feasible_bonus_actions]
            haste_action_threats = [(fha.calculate_threat(self, battle_map), fha) for fha in feasible_haste_actions]

            # action_threats.sort(key=lambda a: a[0], reverse=True)
            # bonus_action_threats.sort(key=lambda a: a[0], reverse=True)
            # haste_action_threats.sort(key=lambda a: a[0], reverse=True)
            all_actions = action_threats
            all_actions.extend(bonus_action_threats)
            all_actions.extend(haste_action_threats)
            all_actions.sort(key=lambda a: a[0], reverse=True)
            try:
                selected_action = all_actions[0][1]
                # logger.info(f"{self} uses {selected_action}")
            except IndexError:
                return None
            if ActoidFlags.IS_ATTACK_LIKE in selected_action.actoid_type:
                target_position = battle_map.get_combatant_position(selected_action.target_combatant)
                if not np.array_equal(self.target_position_cache, target_position):
                    # if the target moved, recalculate path
                    try:
                        self.plan_path(battle_map, selected_action.target_combatant, target_position)
                    except RuntimeError:
                        return None

                if not battle_map.are_in_hop_range(self, selected_action.target_combatant, selected_action.factory.range):
                    try:
                        movement = next(self.movement_generator)
                        logger.debug(f"Moving by {movement}")
                        return movement
                    except StopIteration:
                        # this means that either the path has been exhausted and we're still not in range => ranged attack
                        self.movement_generator = None
                        if self.has_action:
                            self.javelin_attack[1].action_type = Action.RANGED_ATTACK
                        elif self.has_haste_action:
                            self.javelin_attack[1].action_type = HasteAction.HASTE_RANGED_ATTACK
                        else:
                            return None
                        return self.javelin_attack[1].create_best(self, battle_map)
            if selected_action is self.javelin_attack:
                print("FIXME")
            return selected_action

        else:
            return None

    def new_turn(self):
        super().new_turn()
        self.movement_generator = None


    def export_resources(self):
        return {
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'curr_rage_uses': self.curr_rage_uses
        }

    def load_resources(self, resources):
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.curr_rage_uses = resources['curr_rage_uses']

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self} taken an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
