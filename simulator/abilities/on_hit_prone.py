from simulator.abilities.on_hit_effect import OnHit
from simulator.misc import roll_saving_throw, reconcile_roll_modifiers, Conditions
import logging

logger = logging.getLogger(__name__)

class OnHitProne(OnHit):
    def __init__(self, st, dc):
        self.st = st
        self.dc = dc

    def hit(self, attacker, attack, target, effect_tracker):
        saved = roll_saving_throw(target.saving_throws[self.st], self.dc, reconcile_roll_modifiers(target.saving_throws_roll_mod[self.st]))
        if not saved:
            logger.info(f"{target} is knocked prone")
            target.apply_condition(Conditions.PRONE)