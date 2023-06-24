from simulator.abilities.on_hit_effect import OnHit
from simulator.misc import Conditions, ConditionWithoutDC, DamageType, ROUND_HORIZON
import logging

from simulator.threat_utils import mean_dmg_auto_hit

logger = logging.getLogger("EncounTroll")


class OnHitSwallow(OnHit):

    def hit(self, attacker, attack, target, effect_tracker):
        logger.info(f"{target} is swallowed")
        target.remove_condition(Conditions.GRAPPLED)
        target.apply_condition(ConditionWithoutDC(Conditions.BLINDED | Conditions.RESTRAINED | Conditions.SWALLOWED, attacker))
        attacker.swallowed_target = target
        attacker.constricted_target = None

    def calculate_threat(self, attacker, target, battle_map, *args, **kwargs):
        # The swallow itself it hard to quantify but we just need to make sure it wins out over the regular bite
        return mean_dmg_auto_hit('3d6', target.is_resistant_to(DamageType.Acid)) * ROUND_HORIZON