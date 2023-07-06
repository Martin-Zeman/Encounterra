from simulator.abilities.on_hit_effect import OnHit
from simulator.misc import Conditions, ConditionWithDC, PhaseOfTurn, ConditionWithoutDC
import logging

logger = logging.getLogger("EncounTroll")

class OnHitAutoRestrained(OnHit):
    def __init__(self, skill, dc):
        self.skill = skill
        self.dc = dc

    def hit(self, attacker, attack, target):
        logger.info(f"{target} is grappled and restrained")
        cond = ConditionWithDC(Conditions.GRAPPLED | Conditions.RESTRAINED, self.skill, self.dc, attacker, PhaseOfTurn.ACTION)
        target.apply_dc_condition(cond)
        attacker.apply_condition(ConditionWithoutDC(Conditions.GRAPPLING, attacker))

    def calculate_threat(self, attacker, target, *args, **kwargs):
        return 0  # TODO
