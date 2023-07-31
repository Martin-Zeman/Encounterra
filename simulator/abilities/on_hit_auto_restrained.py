from simulator.abilities.on_hit_effect import OnHit
from simulator.misc import Conditions, ConditionWithDC, PhaseOfTurn, ConditionWithoutDC
import logging

logger = logging.getLogger("Encounterra")

class OnHitAutoRestrained(OnHit):
    def __init__(self, skill, dc, name="On Hit Restrained"):
        self.skill = skill
        self.dc = dc
        self.name = name

    def hit(self, attacker, attack, target):
        logger.info(f"{target} is grappled and restrained")
        cond = ConditionWithDC(Conditions.GRAPPLED | Conditions.RESTRAINED, self.skill, self.dc, attacker, PhaseOfTurn.ACTION)
        target.apply_dc_condition(cond)
        attacker.apply_condition(ConditionWithoutDC(Conditions.GRAPPLING, attacker))
        return None

    def calculate_threat(self, attacker, target, **kwargs):
        return 0  # TODO
