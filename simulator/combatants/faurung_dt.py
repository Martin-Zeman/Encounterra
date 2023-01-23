from simulator.combatant import Combatant
from simulator.actions.movement import MovementGenerator
from simulator.spellslots import Spellslots
from simulator.action_factory import *
from simulator.misc import Side
from simulator.spells.spell import SpellStats
import logging
import pickle

logger = logging.getLogger(__name__)


class FaurungDt(Combatant):
    INV_MAPPING = {0: Action.FIREBOLT, 1: Action.CHAOSBOLT, 2: Action.HASTE, 3: BonusAction.QUICKENED_FIREBALL,
                   4: Action.TWINNED_FIREBOLT, 5: Action.TWINNED_HASTE, 6: Action.FIREBALL}

    def __init__(self):
        super().__init__("FaurungDt", level=5, hp=43, ac=16, init_bonus=2, speed=30, spell_to_hit=7, resistances=set(), dc=15)
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
        with open('simulator/decision_tree/faurung_model.pickle', 'rb') as handle:
            self.model = pickle.load(handle)

    def get_action(self, battle_map):
        while self.has_action or self.has_bonus_action or self.movement or self.has_haste_action:
            nearest_enemy, dist = battle_map.get_nearest(self, Side.ENEMY)
            if not nearest_enemy:
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
            # Model 'enemies', 'cast_leveled', 'ss1', 'ss2', 'ss3', 'enemy_adjacent', 'allies', 'is_concentrating', 'sorcery_points'
            if self.has_action:
                placement, _, _ = battle_map.find_best_placement_harmful_circular(self, 30, 4)
                allies = battle_map.teams.get_allies(self)
                enemies, _ = battle_map.get_enemies_within_radius_sorted_by_distance(self, SpellStats.Range.FEET_120.value)

                decision = self.INV_MAPPING[self.model.predict([[len(enemies), self.already_cast_leveled_spell_this_turn,
                                                                 self.spellslots.get_spellslots(1), self.spellslots.get_spellslots(2),
                                                                 self.spellslots.get_spellslots(3), False, len(allies),
                                                                 self.is_concentrating, self.curr_sorcery_points]])[0]]
                try:
                    match decision:
                        case Action.FIREBOLT | Action.CHAOSBOLT:
                            logger.debug(f"{self} casts {decision.name} on {nearest_enemy}", extra={"team": self.team_color})
                            return (decision, [enemies[0]])
                        case Action.HASTE:
                            logger.debug(f"{self.name} casts Haste on {allies[0]}", extra={"team": self.team_color})
                            return (decision, [allies[0]])
                        case Action.TWINNED_HASTE:
                            logger.debug(f"{self.name} casts Twinned Haste on {allies[0]} and {allies[1]}", extra={"team": self.team_color})
                            return (decision, allies[0:2])
                        case Action.FIREBALL | BonusAction.QUICKENED_FIREBALL:
                            logger.debug(f"{self.name} casts {decision.name}", extra={"team": self.team_color})
                            return (decision, placement)
                        case Action.TWINNED_FIREBOLT:
                            logger.debug(f"{self} casts {decision.name} on {enemies[0]} and {enemies[1]}", extra={"team": self.team_color})
                            return (decision, enemies[0:2])
                except:
                    logger.error("Faurung decision tree failure. Doding...")
                    return (Action.DODGE,)
                return
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
