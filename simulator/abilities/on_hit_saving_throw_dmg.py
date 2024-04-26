from ..abilities.on_hit_effect import OnHit
from ..action_resolver import resolve_on_hit_dmg_saving_throw
from ..misc import parse_dmg_dice, roll_dice
import logging

from ..threat_utils import mean_dmg_dc_attack

logger = logging.getLogger("Encounterra")


class OnHitSavingThrowDmg(OnHit):
    def __init__(self, st, dc, dmg_dice, dmg_type, half_on_success=True, name="On Hit Saving Throw Damage"):
        self.st = st
        self.dc = dc
        self.dmg_dice = dmg_dice
        self.dmg_type = dmg_type
        self.half_on_success = half_on_success
        self.name = name

    def hit(self, attacker, attack, target, multiplier, dmg_so_far):
        dice = parse_dmg_dice(self.dmg_dice)
        dmg = roll_dice(dice)
        resolve_on_hit_dmg_saving_throw(self, dmg, target, self.half_on_success)
        return None

    def calculate_threat(self, attacker, target, **kwargs):
        # The swallow itself it hard to quantify but we just need to make sure it wins out over the regular bite
        return min(target.curr_hp, mean_dmg_dc_attack(self.dc, self.dmg_dice, self.half_on_success, self.st, target, self.dmg_type))
