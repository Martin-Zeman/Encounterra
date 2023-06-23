from simulator.abilities.on_hit_effect import OnHit
from simulator.misc import roll_saving_throw, reconcile_roll_types, Conditions, ConditionWithoutDC
import logging

logger = logging.getLogger("EncounTroll")

class OnHitProne(OnHit):
    def __init__(self, st, dc):
        self.st = st
        self.dc = dc

    def hit(self, attacker, attack, target, effect_tracker):
        saved = roll_saving_throw(target.saving_throws[self.st], self.dc, reconcile_roll_types(target.saving_throws_roll_type_mod[self.st]))
        if not saved:
            logger.info(f"{target} is knocked prone")
            target.apply_condition(ConditionWithoutDC(Conditions.PRONE, attacker))