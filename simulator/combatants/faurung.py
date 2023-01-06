from simulator.combatant import Combatant
from simulator.movement import MovementGenerator
from simulator.spellslots import Spellslots
from simulator.action_factory import *
from simulator.misc import Side
from simulator.spells.spell import Spell
import logging
import random

logger = logging.getLogger(__name__)


class Faurung(Combatant):

    def __init__(self):
        super().__init__("Faurung", level=5, hp=43, ac=16, init_bonus=2, speed=30, spell_to_hit=7, resistances=set(), dc=15)
        self.add_ability(Action.FIREBALL)
        self.add_ability(Action.FIREBOLT)
        self.add_ability(Action.HASTE)
        self.add_ability(BonusAction.MISTY_STEP)
        self.add_ability(Reaction.SHIELD)
        self.add_ability(Passive.METAMAGIC, sorcery_points=5)
        self.add_ability(MetaAction.QUICKENED_SPELL)
        self.add_ability(MetaAction.TWINNED_SPELL)
        self.spellslots = Spellslots(Spellslots.Class.SORCERER, 5)
        self.movement_generator_cache = None
        self.nowhere_to_go = False

    def get_action(self, battle_map):
        while self.has_action or self.has_bonus_action or self.movement or self.has_haste_action:
            enemies, dist = battle_map.get_enemies_within_radius(self, Spell.Range.FEET_120.value)
            if not enemies:
                # all enemies are dead
                return (MetaAction.DONE,)

            # First make sure to gain distance
            if battle_map.is_enemy_adjacent(self) and self.has_bonus_action and self.spellslots.get_spellslots(
                    2) and not self.already_cast_leveled_spell_this_turn and not self.nowhere_to_go:
                free_coords = battle_map.get_free_coords_away_from_enemies(self, 6)
                if not free_coords:
                    logger.debug(f"{self.name} has nowhere to Misty Step to")
                    self.nowhere_to_go = True
                    continue
                logger.debug(f"{self.name} casts Misty Step to location {free_coords[0]}", extra={"team": self.team_color})
                return (BonusAction.MISTY_STEP, free_coords[0])
            elif self.movement and not self.movement_generator_cache and not self.nowhere_to_go:
                free_coords = battle_map.get_free_coords_at_distance(enemies[0], int(self.movement + dist[0]), self)
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
            should_twin = False
            if len(enemies) > 1 and random.randint(1, 10) > 3 and self.curr_sorcery_points > 0:
                should_twin = True
            if self.has_action and not self.already_cast_leveled_spell_this_turn:
                placement, score = battle_map.find_best_placement_harmful_circular(self, 30, 4)
                allies = battle_map.teams.get_allies(self)
                if self.spellslots.get_spellslots(3) and score > 1 and self.curr_sorcery_points > 0:
                    if score > 1:
                        logger.debug(f"{self.name} casts Fireball", extra={"team": self.team_color})
                        return (BonusAction.QUICKENED_FIREBALL if self.has_bonus_action and self.curr_sorcery_points > 1 else Action.FIREBALL, placement)
                        # return (Action.FIREBALL, placement)
                elif self.spellslots.get_spellslots(3) and allies and not self.is_concentrating:
                    target_ally = allies[random.randint(0, len(allies) - 1)]
                    logger.debug(f"{self.name} casts Haste on {target_ally}", extra={"team": self.team_color})
                    return (BonusAction.QUICKENED_HASTE if self.has_bonus_action and self.curr_sorcery_points > 1 else Action.HASTE, [target_ally])
                    # return (Action.HASTE, target_ally)
                elif self.spellslots.get_spellslots(1):
                    logger.debug(f"{self} casts Chaosbolt on {enemies[0]}", extra={"team": self.team_color})
                    return (Action.TWINNED_CHAOSBOLT, enemies[0:2]) if should_twin else (BonusAction.QUICKENED_CHAOSBOLT if self.has_bonus_action and self.curr_sorcery_points > 1 else Action.CHAOSBOLT, [enemies[0]])
                    # return (Action.CHAOSBOLT, nearest_enemy)
                else:
                    logger.debug(f"{self} casts Firebolt on {enemies[0]}", extra={"team": self.team_color})
                    return (Action.TWINNED_FIREBOLT, enemies[0:2]) if should_twin else (Action.FIREBOLT, [enemies[0]])
            elif self.has_action:
                logger.debug(f"{self} casts Firebolt on {enemies[0]}", extra={"team": self.team_color})
                return (Action.TWINNED_FIREBOLT, enemies[0:2]) if should_twin else (Action.FIREBOLT, [enemies[0]])
            else:
                return (MetaAction.DONE,)
        return (MetaAction.DONE,)

    def new_turn(self):
        super().new_turn()
        self.nowhere_to_go = False
        self.movement_generator_cache = None

    def prompt_aoo(self, moving_combatant):
        return (MetaAction.DONE,)

    def prompt_after_hit_reaction(self, attacking_combatant):
        if self.spellslots.get_spellslots(1) and self.has_reaction:
            logger.debug(f"{self.name} casts Shield", extra={"team": self.team_color})
            return (Reaction.SHIELD,)
        elif self.has_reaction:
            logger.debug(f"{self.name} cannot cast Shield. Out of spellslots.", extra={"team": self.team_color})
        return (MetaAction.DONE,)
