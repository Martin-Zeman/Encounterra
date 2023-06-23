from simulator.abilities.on_hit_effect import OnHit
from simulator.misc import Conditions, ConditionWithoutDC
import logging

logger = logging.getLogger("EncounTroll")


class OnHitSwallow(OnHit):

    def hit(self, attacker, attack, target, effect_tracker):
        logger.info(f"{target} is swallowed")
        target.remove_condition(Conditions.GRAPPLED)
        target.apply_condition(ConditionWithoutDC(Conditions.BLINDED | Conditions.RESTRAINED | Conditions.SWALLOWED, attacker))
        attack.swallowed_target = target
        attack.constricted_target = None
