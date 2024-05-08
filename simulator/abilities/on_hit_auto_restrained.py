from ..abilities.on_hit_effect import OnHit
from ..conditions import Conditions, ConditionWithDC, Condition, apply_condition, apply_dc_condition, get_grappler
from ..misc import PhaseOfTurn
import logging

logger = logging.getLogger("Encounterra")


class OnHitAutoRestrained(OnHit):
    def __init__(self, skill, dc, name="On Hit Restrained"):
        self.skill = skill
        self.dc = dc
        self.name = name

    def hit(self, attacker, attack, target, multiplier, dmg_so_far):
        grappler = get_grappler(target)
        if grappler is None:
            logger.info(f"{target} is grappled and restrained")
            cond = ConditionWithDC(Conditions.GRAPPLED | Conditions.RESTRAINED, self.skill, self.dc, attacker, PhaseOfTurn.ACTION)
            apply_dc_condition(target, cond)
            apply_condition(attacker, Condition(Conditions.GRAPPLING, attacker, None, target))
        else:
            logger.info(f"{target} is already grappled by {grappler}")
        return None

    def calculate_threat(self, attacker, target, **kwargs):
        return 0  # TODO
