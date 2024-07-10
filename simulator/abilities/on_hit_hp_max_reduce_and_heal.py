from ..abilities.on_hit_effect import OnHit
from ..misc import avg_roll_multi, roll_dice_multi
import logging

from ..threat_utils import MAX_HP_MODIFIER_MULTIPLIER

logger = logging.getLogger("Encounterra")


class OnHitHpMaxReduceAndHeal(OnHit):
    def __init__(self, dmg_dice, dmg_type, crit_range, name="On Hit HP Max Reduce"):
        self.dmg_dice = dmg_dice
        self.dmg_type = dmg_type
        self.crit_range = crit_range
        self.name = name

    def hit(self, attacker, attack, target, multiplier, dmg_so_far):
        dmg = roll_dice_multi(self.dmg_dice)
        dmg *= multiplier
        target.max_hp_modifier -= dmg
        attacker.heal(dmg)
        logger.info(f"{attacker} heals for {dmg} damage")
        return [dmg, self.dmg_type]

    def calculate_threat(self, attacker, target, **kwargs):
        avg_dmg_roll = avg_roll_multi(self.dmg_dice)
        return (avg_dmg_roll + 0.05 * self.crit_range * avg_dmg_roll) * 2 * MAX_HP_MODIFIER_MULTIPLIER
