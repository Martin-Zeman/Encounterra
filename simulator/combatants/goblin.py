from simulator.actions.attack_fsms import OneMeleeOrOneRanged
from simulator.combatant import Combatant
from simulator.actions.movement import MovementGenerator, GetUpFactory
from simulator.misc import DamageType, SavingThrow, Conditions
from simulator.action_factory import *
from simulator.misc import Side
import logging

logger = logging.getLogger(__name__)


class Goblin(Combatant):

    def __init__(self, effect_tracker, name="Goblin"):
        super().__init__(effect_tracker, name, level=1, hp=7, ac=15, init_bonus=2, spell_to_hit=0, speed=30, resistances=set(), dc=0)
        self.scimitar_attack = self.add_ability(Action.ATTACK,  name="Scimitar", combatant=self, to_hit=4, dmg_dice="1d6", dmg_bonus=2, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1, attack_type=AttackFactory.Type.MELEE)
        self.shortbow_attack = self.add_ability(Action.ATTACK,  name="Shortbow", combatant=self, to_hit=4, dmg_dice="1d6", dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=64, crit_range=1, attack_type=AttackFactory.Type.RANGED)
        self.nimble_disengage = self.add_ability(BonusAction.CUNNING_DISENGAGE)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Scimitar", combatant=self, to_hit=4, dmg_dice="1d6", dmg_bonus=2, dmg_type=DamageType.Slashing, attack_range=1, crit_range=1, attack_type=AttackFactory.Type.MELEE)
        self.selected_target = None
        self.dist_to_nearest = None
        self.saving_throws[SavingThrow.STR] = -1
        self.saving_throws[SavingThrow.DEX] = 2
        self.saving_throws[SavingThrow.CON] = 0
        self.saving_throws[SavingThrow.INT] = 0
        self.saving_throws[SavingThrow.WIS] = -1
        self.saving_throws[SavingThrow.CHA] = -1

    def plan_path(self, battle_map):
        free_coords = battle_map.get_free_coords_at_distance_from_target(self.selected_target, self, 8, 16)
        for coord in free_coords:
            assert battle_map.is_empty(coord), "COORD IS NOT FREE"
            assert battle_map.are_valid_coords(coord), "COORD IS NOT VALID"
        if not free_coords:
            logger.info(f"There are no free coords for the {self} to disengage to. Using dodge action", extra={"team": self.team_color})
            raise RuntimeError
        path = battle_map.get_path_to(self, free_coords[0])
        if not path:
            logger.info(f"{self.name} has nowhere to go. Using dodge action", extra={"team": self.team_color})
            raise RuntimeError
        self.movement_generator = MovementGenerator(self, path).get_generator()

    def attack_routine(self):
        if self.has_action:
            return self.shortbow_attack[1].create(self.selected_target)
        else:
            for ha in self.haste_action_factories:
                if ha[1].name == "Shortbow":
                    return ha[1].create(self.selected_target)

    def get_action(self, battle_map):
        if self.is_affected_by(Conditions.PRONE) and self.movement >= self.speed / 2:
            return GetUpFactory().create()

        # TODO he doesn't shoot after moving into position
        if not self.selected_target:
            self.selected_target, self.dist_to_nearest, target_position = battle_map.get_nearest(self, Side.ENEMY)
        if not self.selected_target:
            return None
        while self.has_action or self.has_haste_action:
            dist = battle_map.get_hop_distance(self, self.selected_target)
            if 8 <= dist <= 16:
                # If I'm in position, just shoot
                return self.attack_routine()
            elif 1 < dist < 8 and self.movement and not self.movement_generator:
                # If I'm not in position but also not adjacent to anyone
                try:
                    self.plan_path(battle_map)
                except RuntimeError:
                    return self.dodge_factory[1].create_best(self, battle_map)
            elif dist == 1 and self.movement and self.has_bonus_action and not self.has_disengaged:
                # I'f I'm adjacent to an enemy I first need to disengage
                return self.nimble_disengage[1].create_best(self, battle_map)
            elif dist == 1 and self.movement and not self.movement_generator:
                # Once I've disengaged, plan escape path
                try:
                    self.plan_path(battle_map)
                except RuntimeError:
                    return self.dodge_factory[1].create_best(self, battle_map)
            elif self.movement_generator and self.movement > 0:
                # Move
                try:
                    movement = next(self.movement_generator)
                    logger.debug(f"Moving by {movement}")
                    return movement
                except StopIteration:
                    self.movement_generator = None
            else:
                return self.attack_routine()


    def new_turn(self):
        super().new_turn()
        self.movement_generator = None
        self.selected_target = None
        self.dist_to_nearest = None
        self.attack_fsm = OneMeleeOrOneRanged()  # Initialized here to avoid pickling error when multiprocessing
        self.attack_mapping = {self.scimitar_attack[1]: (1, OneMeleeOrOneRanged.melee), self.shortbow_attack[1]: (2, OneMeleeOrOneRanged.ranged)}

    def prompt_aoo(self, moving_combatant):
        # only use it if I go before my selected target in initiative so that I can move away and use sentinel+pam
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
