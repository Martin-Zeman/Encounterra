from simulator.actions.attack_fsms import OneAttack
from simulator.combatant import Combatant
from simulator.actions.movement import MovementGenerator, GetUpFactory
from simulator.spellslots import Spellslots
from simulator.misc import CombatantArchetype, DamageType, get_factory_of_type, SavingThrow, Conditions
from simulator.action_factory import *
from simulator.spells.spell import SpellStats
from simulator.feasibility import get_feasible_actions
import logging

logger = logging.getLogger(__name__)


class Faurung(Combatant):

    def __init__(self, effect_tracker, name="Faurung"):
        super().__init__(effect_tracker, name, level=5, hp=43, ac=16, init_bonus=2, speed=30, spell_to_hit=7, resistances=set(), dc=15)
        self.staff = self.add_ability(Action.ATTACK, name="Staff of Defence", combatant=self, to_hit=2, dmg_dice="1d8", dmg_bonus=-1,
                         dmg_type=DamageType.Bludgeoning, attack_range=1, attack_type=AttackFactory.Type.MELEE)
        self.add_ability(Reaction.REACTION_ATTACK, name="Staff of Defence", combatant=self, to_hit=2, dmg_dice="1d8", dmg_bonus=-1,
                         dmg_type=DamageType.Bludgeoning, attack_range=1, attack_type=AttackFactory.Type.MELEE)
        # self.attack_fsm = OneMelee()
        # self.attack_mapping = {staff[1]: (1, OneMelee.melee)}
        self.add_ability(Action.FIREBALL)
        self.add_ability(Action.FIREBOLT)
        self.add_ability(Action.HASTE)
        self.add_ability(BonusAction.MISTY_STEP)
        self.add_ability(Reaction.SHIELD)
        self.add_ability(Passive.METAMAGIC, sorcery_points=5)
        self.add_ability(MetaAction.QUICKENED_SPELL)
        self.add_ability(MetaAction.TWINNED_SPELL)
        self.spellslots = Spellslots(Spellslots.Class.SORCERER, 5)
        self.archetype = CombatantArchetype.RANGED
        self.movement_generator_cache = None
        self.nowhere_to_go = False
        self.saving_throws[SavingThrow.STR] = -1
        self.saving_throws[SavingThrow.DEX] = 2
        self.saving_throws[SavingThrow.CON] = 6
        self.saving_throws[SavingThrow.INT] = 1
        self.saving_throws[SavingThrow.WIS] = 1
        self.saving_throws[SavingThrow.CHA] = 7

    def get_action(self, battle_map):
        if self.is_affected_by(Conditions.PRONE) and self.movement >= self.speed / 2:
            return GetUpFactory().create()

        enemies, _ = battle_map.get_enemies_within_radius_sorted_by_distance(self, SpellStats.Range.FEET_120.value)
        while enemies and self.movement and not self.movement_generator_cache and not self.nowhere_to_go:
            curr_hop_dist = battle_map.get_hop_distance(self, enemies[0])
            free_coords = battle_map.get_free_coords_at_distance_from_target(enemies[0], self, curr_hop_dist, curr_hop_dist + self.movement)
            if not free_coords:
                logger.info(f"{self.name} has nowhere to go to")
                self.nowhere_to_go = True
                break
            path = battle_map.get_path_to(self, free_coords[0])
            self.movement_generator_cache = MovementGenerator(self, path).get_generator()

        if self.movement and self.movement_generator_cache:
            try:
                movement = next(self.movement_generator_cache)
                logger.info("Trying to get distance")
                return movement
            except StopIteration:
                self.movement_generator_cache = None

        feasible_action_factories = get_feasible_actions(self.action_factories, self, battle_map)
        feasible_bonus_action_factories = get_feasible_actions(self.bonus_action_factories, self, battle_map)
        feasible_haste_action_factories = get_feasible_actions(self.haste_action_factories, self, battle_map)
        # feasible_free_actions = get_feasible_actions(self.free_actions, self, battle_map)
        if len(feasible_action_factories) > 0 or len(feasible_bonus_action_factories) > 0 or len(feasible_haste_action_factories) > 0:# or len(feasible_free_actions > 0):
            feasible_actions = list(filter(lambda item: item is not None, [fa[1].create_best(self, battle_map) for fa in feasible_action_factories]))
            feasible_bonus_actions = list(filter(lambda item: item is not None, [fa[1].create_best(self, battle_map) for fa in feasible_bonus_action_factories]))
            feasible_haste_actions = list(filter(lambda item: item is not None, [fa[1].create_best(self, battle_map) for fa in feasible_haste_action_factories]))
            # feasible_free_actions = [fa[1].create_best(self, battle_map) for fa in feasible_free_actions]

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
            ret = None
            try:
                if len(all_actions) > 1 and isinstance(all_actions[1][1], MistyStep):
                    # In case misty step ranks second, give preference to it
                    ret = all_actions[1][1]
                else:
                    ret = all_actions[0][1]
                logger.info(f"{self} uses {ret}")
            except IndexError:
                pass
            return ret
        else:
            return None


    def new_turn(self):
        super().new_turn()
        self.nowhere_to_go = False
        self.movement_generator_cache = None
        self.attack_fsm = OneAttack()  # Initialized here to avoid pickling error when multiprocessing
        self.attack_mapping = {self.staff[1]: (1, OneAttack.attack)}

    def prompt_aoo(self, moving_combatant):
        return None

    def prompt_after_hit_reaction(self, attacking_combatant, attack_roll):
        if self.spellslots.get_spellslots(1) and self.has_reaction and attack_roll <= self.dc + 5:
            shield_factory = get_factory_of_type(self.reaction_factories, Reaction.SHIELD)
            logger.info(f"{self.name} casts Shield", extra={"team": self.team_color})
            return shield_factory.create() if shield_factory else None
        elif attack_roll > self.dc + 5:
            logger.info("Shield would not suffice")
        elif self.has_reaction:
            logger.info(f"{self.name} cannot cast Shield. Out of spellslots.", extra={"team": self.team_color})
        return None
