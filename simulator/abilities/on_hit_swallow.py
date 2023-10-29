from ..abilities.on_hit_effect import OnHit
from ..battle_map import Map
from ..effects.digestion import Digestion
from ..misc import Conditions, ConditionWithoutDC, DamageType, ROUND_HORIZON
import logging

from ..threat_utils import mean_dmg_auto_hit

logger = logging.getLogger("Encounterra")


class OnHitSwallow(OnHit):

    def __init__(self, name="Swallow"):
        self.name = name

    def hit(self, attacker, attack, target):
        logger.info(f"{target} is swallowed")
        target.remove_all_conditions_of_type(Conditions.GRAPPLED)
        attacker.remove_condition(Conditions.GRAPPLING)
        target.apply_condition(ConditionWithoutDC(Conditions.BLINDED | Conditions.RESTRAINED | Conditions.SWALLOWED, attacker))
        attacker.swallowed_target = target
        attacker.constricted_target = None
        battle_map = Map.get()
        battle_map.effect_tracker.add(Digestion(attacker, target))
        battle_map.remove_combatant(target)
        return None

    def calculate_threat(self, attacker, target, **kwargs):
        # The swallow itself it hard to quantify but we just need to make sure it wins out over the regular bite
        return mean_dmg_auto_hit('3d6', target.is_resistant_to(DamageType.Acid)) * ROUND_HORIZON