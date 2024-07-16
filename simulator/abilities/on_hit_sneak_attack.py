from ..abilities.on_hit_effect import OnHit
from ..battle_map import Map
import numba_functions as nf
import logging

from ..utils.roll_types import RollType

logger = logging.getLogger("Encounterra")


class OnHitSneakAttack(OnHit):

    @staticmethod
    def get_dmg_dice(level):
        match level:
            case lvl if 1 <= lvl <= 2:
                return (1, 6)
            case lvl if 3 <= lvl <= 4:
                return (2, 6)
            case lvl if 5 <= lvl <= 6:
                return (3, 6)
            case lvl if 7 <= lvl <= 8:
                return (4, 6)
            case lvl if 9 <= lvl <= 10:
                return (5, 6)
            case lvl if 11 <= lvl <= 12:
                return (6, 6)
            case lvl if 13 <= lvl <= 14:
                return (7, 6)
            case lvl if 15 <= lvl <= 16:
                return (8, 6)
            case lvl if 17 <= lvl <= 18:
                return (9, 6)
            case lvl if 19 <= lvl <= 20:
                return (10, 6)
            case _:
                logger.error("Incorrect caster level of Sneak Attack")
                return (1, 6)

    def __init__(self, dmg_dice, dmg_type, crit_range, name="Sneak Attack"):
        self.dmg_dice = dmg_dice
        self.dmg_type = dmg_type
        self.crit_range = crit_range
        self.name = name

    def hit(self, attacker, attack, target, multiplier, dmg_so_far):
        if attack.roll_type is RollType.DISADVANTAGE:
            return None
        battle_map = Map.get()
        if not getattr(attacker, "already_used_sneak_attack_this_turn", True) and (attack.roll_type is RollType.ADVANTAGE or battle_map.is_ally_adjacent_to_target(attacker, target)):
            logger.info("Activating Sneak Attack")
            attacker.already_used_sneak_attack_this_turn = True
            return [nf.roll_dice_multi(self.dmg_dice) * multiplier, self.dmg_type]
        return None

    def calculate_threat(self, attacker, target, **kwargs):
        roll_type = kwargs.get("roll_type", RollType.STRAIGHT)
        if roll_type is RollType.DISADVANTAGE:
            return 0
        battle_map = Map.get()
        if not getattr(attacker, "already_used_sneak_attack_this_turn", True) and (roll_type is RollType.ADVANTAGE or battle_map.is_ally_adjacent_to_target(attacker, target)):
            avg_dmg_roll = nf.avg_roll_multi(self.dmg_dice)
            return avg_dmg_roll + 0.05 * self.crit_range * avg_dmg_roll
        return 0


