from simulator.combatant import Combatant
from simulator.attack import Attack
from simulator.dodge import Dodge
from simulator.movement import Movement, MovementGenerator
from simulator.action import Action
from simulator.spellslots import Spellslots
from simulator.misc import DamageType
from simulator.spells.fireball import Fireball
from simulator.spells.firebolt import Firebolt
from simulator.spells.misty_step import MistyStep
import numpy as np
import logging

logger = logging.getLogger(__name__)


class Faurung(Combatant):

    def __init__(self):
        faurung_attacks = [Attack("Staff of Defence", self, 3, "1d8", -1, Action.ActionClasses.ACTION, DamageType.Bludgeoning, 1)]
        super().__init__("Faurung", actions=faurung_attacks, hp=43, ac=16, init_bonus=2, speed=30, resistances=[], dc=15, num_attacks=1)
        self.spellslots.append(Spellslots(Spellslots.Class.SORCERER, 5))
        self.movement_generator_cache = None
        self.nowhere_to_go = False

    def get_action(self, battle_map):
        while self.has_action or self.has_bonus_action or self.movement:
            nearest_enemy = battle_map.get_nearest_enemy(self)
            dist = battle_map.get_distance(self, nearest_enemy)
            if not dist:
                # all enemies are dead
                return None
            if battle_map.is_enemy_adjacent(self) and self.has_bonus_action and self.spellslots[0].has_spellslots(2) and not self.already_cast_leveled_spell_this_turn and not self.nowhere_to_go:
                free_coords = battle_map.get_free_coords_away_from_enemies(self, 6)
                if not free_coords:
                    logger.debug(f"{self.name} has nowhere to Misty Step to")
                    self.nowhere_to_go = True
                    continue
                misty_step = MistyStep(free_coords[0])
                self.spellslots[0].use_spellslot(2)
                self.already_cast_leveled_spell_this_turn = True
                self.has_bonus_action = False
                logger.debug(f"{self.name} casts Misty Step to location {free_coords[0]}", extra={"team": self.team_color})
                return misty_step
            elif self.movement and not self.movement_generator_cache and not self.nowhere_to_go:
                free_coords = battle_map.get_free_coords_at_distance(nearest_enemy, int(self.movement + dist), self)
                if not free_coords:
                    logger.debug(f"{self.name} has nowhere to go to")
                    self.nowhere_to_go = True
                    continue
                path = battle_map.get_path_to(self, free_coords[0])
                self.movement_generator_cache = MovementGenerator(self, Movement.STANDARD, path, True).get_generator()
            elif self.movement and self.movement_generator_cache:
                try:
                    movement = next(self.movement_generator_cache)
                    logger.debug("Trying to get distance")
                    return movement
                except StopIteration:
                    self.movement_generator_cache = None
            if self.has_action and self.spellslots[0].has_spellslots(3) and not self.already_cast_leveled_spell_this_turn:
                placement = battle_map.find_best_placement_harmful_circular(self, 30, 4)
                fireball = Fireball(placement, self.dc)
                self.spellslots[0].use_spellslot(3)
                self.has_action = False
                self.already_cast_leveled_spell_this_turn = True
                logger.debug(f"{self.name} casts Fireball", extra={"team": self.team_color})
                return fireball
            elif self.has_action:
                # cast firebolt
                logger.debug(f"{self.name} casts Firebolt on {nearest_enemy.get_name()}", extra={"team": self.team_color})
                firebolt = Firebolt(7, 5, nearest_enemy)
                self.has_action = False
                return firebolt
            else:
                return None
        return None

    def new_turn(self):
        super().new_turn()
        self.nowhere_to_go = False
        self.movement_generator_cache = None

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            pass
        return None
