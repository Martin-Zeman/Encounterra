from ..abilities.on_hit_effect import OnHit
from ..actions.action_types import Passive
from ..battle_map import Map
from ..misc import avg_roll_multi, roll_dice_multi
import logging

logger = logging.getLogger("Encounterra")


class OnHitMartialAdvantage(OnHit):

    def __init__(self, dmg_type, name="Martial Advantage"):
        self.dmg_dice = ((2, 6),)
        self.dmg_type = dmg_type
        self.name = name

    def hit(self, attacker, attack, target, multiplier, dmg_so_far):
        battle_map = Map.get()
        if attacker.resources[Passive.MARTIAL_ADVANTAGE].has_resource() and battle_map.is_ally_adjacent_to_target(attacker, target):
            logger.info("Activating Martial Advantage")
            attacker.resources[Passive.MARTIAL_ADVANTAGE].use_resource()
            return [roll_dice_multi(self.dmg_dice) * multiplier, self.dmg_type]
        return None

    def calculate_threat(self, attacker, target, **kwargs):
        battle_map = Map.get()
        if attacker.resources[Passive.MARTIAL_ADVANTAGE].has_resource() and battle_map.is_ally_adjacent_to_target(attacker, target):
            avg_dmg_roll = avg_roll_multi(self.dmg_dice)
            return avg_dmg_roll + 0.05 * avg_dmg_roll  # TODO self.crit_range is simplified to 1
        return 0


