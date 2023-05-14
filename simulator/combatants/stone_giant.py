from simulator.abilities.on_hit_prone import OnHitProne
from simulator.utils.state_machine_template import StateMachineTemplate
from simulator.combatant import Combatant
from simulator.actions.movement import MovementGenerator, GetUpFactory
from simulator.feasibility import get_feasible_factories
from simulator.misc import DamageType, SavingThrow, Conditions, Size
from simulator.action_factory import *
from simulator.action_types import *
from simulator.actions.actoid import ActoidFlags
import numpy as np
import logging

logger = logging.getLogger("EncounTroll")




class StoneGiant(Combatant):

    def __init__(self, effect_tracker, name="Stone Giant"):
        super().__init__(effect_tracker, name, level=5, hp=126, ac=17, init_bonus=2, spell_to_hit=0, speed=40, resistances=set(), dc=17)
        self.size = Size.HUGE
        self.club = self.add_ability(Action.MELEE_ATTACK,  name="Greatclub", combatant=self, to_hit=9, dmg_dice="3d8", dmg_bonus=6, dmg_type=DamageType.Bludgeoning, attack_range=3, max_num=2)
        self.rock = self.add_ability(Action.RANGED_ATTACK, name="Rock", combatant=self, to_hit=9, dmg_dice="4d10", dmg_bonus=6,
                                            dmg_type=DamageType.Bludgeoning, attack_range=48, crit_range=1, ammo=2, on_hit=OnHitProne(SavingThrow.STR, 17))
        self.add_ability(Reaction.REACTION_ATTACK,  name="Greatclub", combatant=self, to_hit=9, dmg_dice="3d8", dmg_bonus=6, dmg_type=DamageType.Bludgeoning, attack_range=15)
        self.build_attack_fms()
        self.add_ability(Passive.MULTIATTACK, num_attacks=2)
        self.melee_reaction_range = 3
        self.movement_generator = None
        self.selected_target = None
        self.path = None
        self.saving_throws[SavingThrow.STR] = 6
        self.saving_throws[SavingThrow.DEX] = 5
        self.saving_throws[SavingThrow.CON] = 8
        self.saving_throws[SavingThrow.INT] = 0
        self.saving_throws[SavingThrow.WIS] = 4
        self.saving_throws[SavingThrow.CHA] = -1


    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_state('1')
        self.attack_fsm.add_transition(str(self.club[1]), '0', '1')
        self.attack_fsm.add_transition(str(self.club[1]), '1', 'nop')
        self.attack_fsm.add_transition(str(self.rock[1]), '0', 'nop')


    def plan_path(self, battle_map, target_combatant, target_position, attack_range):
        self.path = battle_map.get_path_to_combatant(self, target_combatant, rng=attack_range)
        logger.debug(f"Target position: {target_position}")
        if not self.path:
            raise RuntimeError
        self.movement_generator = MovementGenerator(self, self.path).get_generator()
        self.target_position_cache = target_position

    def get_action(self, battle_map):
        if self.is_affected_by(Conditions.PRONE) and self.movement >= self.speed / 2:
            return GetUpFactory().create()

        # TODO add the knock prone effect to the rock
        # TODO prevent it from throwing a rock once it's used a club
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
            if ActoidFlags.IS_ATTACK_LIKE in selected_action.actoid_flags:
                target_position = battle_map.get_combatant_position(selected_action.target_combatant)
                if not np.array_equal(self.target_position_cache, target_position):
                    # if the target moved or new turn recalculate path
                    try:
                        self.plan_path(battle_map, selected_action.target_combatant, target_position, selected_action.factory.range)
                    except RuntimeError:
                        # Could be blocked, try to find an enemy within reach
                        enemies = battle_map.get_enemies(self)
                        alternative_target_found = False
                        for e in enemies:
                            if battle_map.get_hop_distance(e, self) <= selected_action.factory.range:
                                selected_action.target_combatant = e
                                alternative_target_found
                                break
                        if not alternative_target_found and self.rock in feasible_action_factories:
                            # try if we can still throw a rock
                            return self.rock[1].create_best(self, battle_map)
                        else:
                            logger.info(f"{self.name} has nowhere to go and no one in reach to attack. Using dodge action", extra={"team": self.team_color})
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
                            self.rock[1].action_type = Action.RANGED_ATTACK
                        elif self.has_haste_action:
                            self.rock[1].action_type = HasteAction.HASTE_RANGED_ATTACK
                        else:
                            return None
                        return self.rock[1].create_best(self, battle_map)
            return selected_action

        else:
            return None


    def export_resources(self):
        return {
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'attack_fsm_state': self.attack_fsm.state,
            'rock_ammo': self.rock[1].ammo
        }

    def load_resources(self, resources):
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.attack_fsm.state = resources['attack_fsm_state']
        self.rock[1].ammo = resources['rock_ammo']

    def new_turn(self):
        super().new_turn()
        self.movement_generator = None

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self} taken an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
