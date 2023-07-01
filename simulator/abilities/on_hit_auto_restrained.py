from simulator.abilities.on_hit_effect import OnHit
from simulator.misc import Conditions, ConditionWithDC, PhaseOfTurn
import logging

logger = logging.getLogger("EncounTroll")

class OnHitAutoRestrained(OnHit):
    def __init__(self, st, dc):
        self.st = st
        self.dc = dc

    def hit(self, attacker, attack, target):
        logger.info(f"{target} is grappled and restrained")
        cond = ConditionWithDC(Conditions.GRAPPLED | Conditions.RESTRAINED, self.st, self.dc, attacker, PhaseOfTurn.ACTION)
        target.apply_dc_condition(cond)

    def calculate_threat(self, attacker, target, *args, **kwargs):
        return 0  # TODO
