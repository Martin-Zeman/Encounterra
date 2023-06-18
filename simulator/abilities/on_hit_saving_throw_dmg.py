from simulator.abilities.on_hit_effect import OnHit
from simulator.action_resolver import resolve_on_hit_dmg_saving_throw
from simulator.misc import parse_dmg_dice, roll_dice
import logging

logger = logging.getLogger("EncounTroll")

class OnHitSavingThrowDmg(OnHit):
    def __init__(self, name, st, dc, dmg_dice, dmg_type, half_on_success=True):
        self.name = name
        self.st = st
        self.dc = dc
        self.dmg_dice = dmg_dice
        self.dmg_type = dmg_type
        self.half_on_success = half_on_success

    def hit(self, attacker, attack, target, effect_tracker):
        dice = parse_dmg_dice(self.dmg_dice)
        dmg = roll_dice(dice)
        resolve_on_hit_dmg_saving_throw(self, dmg, target, self.half_on_success)
