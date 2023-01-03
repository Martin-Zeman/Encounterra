from simulator.combatant import Combatant
from simulator.movement import MovementGenerator
from simulator.spellslots import Spellslots
from simulator.action_factory import *
from simulator.misc import Side
import logging
import random

logger = logging.getLogger(__name__)


class Faurung(Combatant):

    def __init__(self):
        # faurung_attacks = [Attack("Staff of Defence", self, 3, "1d8", -1, Action.ActionClasses.ACTION, DamageType.Bludgeoning, 1)]
        super().__init__("Faurung", level=5, hp=43, ac=16, init_bonus=2, speed=30, spell_to_hit=7, resistances=set(), dc=15)
        self.add_ability(Action.FIREBALL)
        self.add_ability(Action.FIREBOLT)
        self.add_ability(Action.HASTE)
        self.add_ability(BonusAction.MISTY_STEP)
        self.add_ability(Reaction.SHIELD)
        self.spellslots = Spellslots(Spellslots.Class.SORCERER, 5)
        self.movement_generator_cache = None
        self.nowhere_to_go = False

    def get_action(self, battle_map):
        while self.has_action or self.has_bonus_action or self.movement or self.has_haste_action:
            nearest_enemy, dist = battle_map.get_nearest(self, Side.ENEMY)
            if not nearest_enemy:
                # all enemies are dead
                return (None,)

            # First make sure to gain distance
            if battle_map.is_enemy_adjacent(self) and self.has_bonus_action and self.spellslots.has_spellslots(
                    2) and not self.already_cast_leveled_spell_this_turn and not self.nowhere_to_go:
                free_coords = battle_map.get_free_coords_away_from_enemies(self, 6)
                if not free_coords:
                    logger.debug(f"{self.name} has nowhere to Misty Step to")
                    self.nowhere_to_go = True
                    continue
                logger.debug(f"{self.name} casts Misty Step to location {free_coords[0]}", extra={"team": self.team_color})
                return (BonusAction.MISTY_STEP, free_coords[0])
            elif self.movement and not self.movement_generator_cache and not self.nowhere_to_go:
                free_coords = battle_map.get_free_coords_at_distance(nearest_enemy, int(self.movement + dist), self)
                if not free_coords:
                    logger.debug(f"{self.name} has nowhere to go to")
                    self.nowhere_to_go = True
                    continue
                path = battle_map.get_path_to(self, free_coords[0])
                self.movement_generator_cache = MovementGenerator(self, path, True).get_generator()
            elif self.movement and self.movement_generator_cache:
                try:
                    movement = next(self.movement_generator_cache)
                    logger.debug("Trying to get distance")
                    return (Movement.STANDARD, movement)
                except StopIteration:
                    self.movement_generator_cache = None

            # Then focus on offense
            if self.has_action and not self.already_cast_leveled_spell_this_turn:
                placement, score = battle_map.find_best_placement_harmful_circular(self, 30, 4)
                allies = battle_map.teams.get_allies(self)
                if self.spellslots.has_spellslots(3):
                    if score > 1:
                        logger.debug(f"{self.name} casts Fireball", extra={"team": self.team_color})
                        return (Action.FIREBALL, placement, self.dc)
                    elif allies and not self.is_concentrating:
                        target_ally = allies[random.randint(0, len(allies) - 1)]
                        logger.debug(f"{self.name} casts Haste on {target_ally}", extra={"team": self.team_color})
                        return (Action.HASTE, target_ally)
                    else:
                        logger.debug(f"{self} casts Firebolt on {nearest_enemy}", extra={"team": self.team_color})
                        return (Action.FIREBOLT, nearest_enemy)
                elif self.spellslots.has_spellslots(1):
                    logger.debug(f"{self} casts Chaosbolt on {nearest_enemy}", extra={"team": self.team_color})
                    return (Action.CHAOSBOLT, nearest_enemy)
                else:
                    logger.debug(f"{self} casts Firebolt on {nearest_enemy}", extra={"team": self.team_color})
                    return (Action.FIREBOLT, nearest_enemy)
            else:
                return (None,)
        return (None,)

    def new_turn(self):
        super().new_turn()
        self.nowhere_to_go = False
        self.movement_generator_cache = None

    def prompt_aoo(self, moving_combatant):
        return (None,)

    def prompt_after_hit_reaction(self, attacking_combatant):
        if self.spellslots.has_spellslots(1) and self.has_reaction:
            logger.debug(f"{self.name} casts Shield", extra={"team": self.team_color})
            return (Reaction.SHIELD,)
        elif self.has_reaction:
            logger.debug(f"{self.name} cannot cast Shield. Out of spellslots.", extra={"team": self.team_color})
        return (None,)
