from simulator.abilities.on_hit_effect import OnHit
from simulator.misc import roll_saving_throw, reconcile_roll_modifiers, Conditions
import logging

logger = logging.getLogger("EncounTroll")

class OnHitAutoRestrained(OnHit):
    def __init__(self, st, dc):
        self.st = st
        self.dc = dc

    def hit(self, attacker, attack, target, effect_tracker):
        # saved = roll_saving_throw(target.saving_throws[self.st], self.dc, reconcile_roll_modifiers(target.saving_throws_roll_mod[self.st]))
        # if not saved:
        # TODO Add the possibility of breaking free
        logger.info(f"{target} is grappled and restrained")
        target.apply_condition(Conditions.GRAPPLED)
        target.apply_condition(Conditions.RESTRAINED)