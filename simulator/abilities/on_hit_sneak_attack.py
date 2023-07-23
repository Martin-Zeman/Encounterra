from simulator.abilities.on_hit_effect import OnHit
from simulator.battle_map import Map
from simulator.effects.effect import EffectType
from simulator.misc import roll_saving_throw, reconcile_roll_types, Conditions, ConditionWithoutDC, parse_dmg_dice, roll_dice, avg_roll
import logging

from simulator.utils.roll_types import RollType

logger = logging.getLogger("EncounTroll")

class OnHitSneakAttack(OnHit):

    @staticmethod
    def get_dmg_dice(level):
        match level:
            case lvl if 1 <= lvl <= 2:
                return "1d6"
            case lvl if 3 <= lvl <= 4:
                return "2d6"
            case lvl if 5 <= lvl <= 6:
                return "3d6"
            case lvl if 7 <= lvl <= 8:
                return "4d6"
            case lvl if 9 <= lvl <= 10:
                return "5d6"
            case lvl if 11 <= lvl <= 12:
                return "6d6"
            case lvl if 13 <= lvl <= 14:
                return "7d6"
            case lvl if 15 <= lvl <= 16:
                return "8d6"
            case lvl if 17 <= lvl <= 18:
                return "9d6"
            case lvl if 19 <= lvl <= 20:
                return "10d6"
            case _:
                logger.error("Incorrect caster level of Sneak Attack")
                return "1d6"
    def __init__(self, dmg_dize, dmg_type, crit_range, name="Sneak Attack"):
        self.dmg_dice = dmg_dize
        self.dmg_type = dmg_type
        self.crit_range = crit_range
        self.name = name

    def hit(self, attacker, attack, target):
        battle_map = Map.get()
        if not getattr(attacker, "already_used_sneak_attack_this_turn", True) and (attack.roll_type is RollType.ADVANTAGE or battle_map.is_ally_adjacent_to_target(attacker, target)):
            logger.info("Activating Sneak Attack")
            dice = parse_dmg_dice(self.dmg_dice)
            attacker.already_used_sneak_attack_this_turn = True
            return [roll_dice(dice), self.dmg_type]

    def calculate_threat(self, attacker, target, **kwargs):
        battle_map = Map.get()
        roll_type = kwargs.get("roll_type", RollType.STRAIGHT)
        if not getattr(attacker, "already_used_sneak_attack_this_turn", True) and (roll_type is RollType.ADVANTAGE or battle_map.is_ally_adjacent_to_target(attacker, target)):
            avg_dmg_roll = avg_roll(self.dmg_dice)
            return avg_dmg_roll + 0.05 * self.crit_range * avg_dmg_roll
        return 0


