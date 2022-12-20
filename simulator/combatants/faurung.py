from simulator.combatant import Combatant
from simulator.attack import Attack
from simulator.dodge import Dodge
from simulator.movement import Movement, MovementGenerator
from simulator.action import Action
from simulator.spellslots import Spellslots
from simulator.misc import DamageType
from simulator.spells.fireball import Fireball
from simulator.spells.firebolt import Firebolt
import numpy as np
import logging

logger = logging.getLogger(__name__)


class Faurung(Combatant):

    def __init__(self):
        faurung_attacks = [Attack("Staff of Defence", self, 3, "1d8", -1, Action.ActionClasses.ACTION, DamageType.Bludgeoning, 1)]
        super().__init__("Faurung", actions=faurung_attacks, hp=43, ac=16, init_bonus=2, speed=30, resistances=[], dc=15, num_attacks=1)
        self.sorc_spellslots = Spellslots(Spellslots.Class.SORCERER, 5)
        self.movement_generator_cache = None

    def get_action(self, battle_map):
        while self.has_action or self.has_bonus_action or self.movement:
            nearest_enemy = battle_map.get_nearest_enemy(self)
            dist = battle_map.get_combatant_distance(self, nearest_enemy)
            if self.has_action and self.sorc_spellslots.has_spellslots(3):
                placement = battle_map.find_best_placement_harmful_circular(self, 30, 4)
                fireball = Fireball(placement, self.dc)
                self.sorc_spellslots.use_spellslot(3)
                self.has_action = False
                logger.debug(f"{self.name} casts Fireball", extra={"team": self.team_name})
                return fireball
            elif dist <= 1 and self.movement and not self.movement_generator_cache:
                free_coords = battle_map.get_free_positions_at_distance(nearest_enemy, int(self.movement), self)
                if free_coords:
                    path = battle_map.get_path_to_coord(self, free_coords[0])
                    self.movement_generator_cache = MovementGenerator(self, Movement.STANDARD, path, True).get_generator()
            elif dist <= 1 and self.movement and self.movement_generator_cache:
                try:
                    movement = next(self.movement_generator_cache)
                    logger.debug("Trying to get distance")
                    return movement
                except StopIteration:
                    self.movement_generator_cache = None
            elif self.has_action:
                # cast firebolt
                logger.debug(f"{self.name} casts Firebolt on {nearest_enemy.get_name()}", extra={"team": self.team_name})
                firebolt = Firebolt(7, 5, nearest_enemy)
                self.has_action = False
                return firebolt
            else:
                return None
        logger.debug(f"{self.name} uses the dodge action", extra={"team": self.team_name})
        return Dodge(self, Action.ActionClasses.ACTION)

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            pass
        return None
