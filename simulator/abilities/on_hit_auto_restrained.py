from ..abilities.on_hit_effect import OnHit
from ..conditions import Conditions, ConditionWithDC, ConditionWithoutDC, apply_condition, apply_dc_condition
from ..misc import PhaseOfTurn
import logging

logger = logging.getLogger("Encounterra")

class OnHitAutoRestrained(OnHit):
    def __init__(self, skill, dc, name="On Hit Restrained"):
        self.skill = skill
        self.dc = dc
        self.name = name

    def hit(self, attacker, attack, target, multiplier):
        logger.info(f"{target} is grappled and restrained")
        cond = ConditionWithDC(Conditions.GRAPPLED | Conditions.RESTRAINED, self.skill, self.dc, attacker, PhaseOfTurn.ACTION)
        apply_dc_condition(target, cond)
        apply_condition(attacker, ConditionWithoutDC(Conditions.GRAPPLING, attacker, target))
        return None

    def calculate_threat(self, attacker, target, **kwargs):
        return 0  # TODO
