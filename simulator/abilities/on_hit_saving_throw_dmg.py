from simulator.abilities.on_hit_effect import OnHit
from simulator.action_resolver import resolve_on_hit_dmg_saving_throw
from simulator.misc import parse_dmg_dice, roll_dice
import logging

from simulator.threat_utils import mean_dmg_dc_attack

logger = logging.getLogger("EncounTroll")

class OnHitSavingThrowDmg(OnHit):
    def __init__(self, name, st, dc, dmg_dice, dmg_type, half_on_success=True):
        self.name = name
        self.st = st
        self.dc = dc
        self.dmg_dice = dmg_dice
        self.dmg_type = dmg_type
        self.half_on_success = half_on_success

    def hit(self, attacker, attack, target):
        dice = parse_dmg_dice(self.dmg_dice)
        dmg = roll_dice(dice)
        resolve_on_hit_dmg_saving_throw(self, dmg, target, self.half_on_success)
        return None

    def calculate_threat(self, attacker, target, **kwargs):
        # The swallow itself it hard to quantify but we just need to make sure it wins out over the regular bite
        return mean_dmg_dc_attack(self.dc, self.dmg_dice, self.half_on_success, target.saving_throws[self.st])
