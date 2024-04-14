from ..abilities.on_hit_effect import OnHit
from ..misc import roll_saving_throw, reconcile_roll_types
from ..conditions import Conditions, Condition, apply_condition
import logging

logger = logging.getLogger("Encounterra")


class OnHitProne(OnHit):
    def __init__(self, st, dc, name="On Hit Prone"):
        self.st = st
        self.dc = dc
        self.name = name

    def hit(self, attacker, attack, target, multiplier, dmg_so_far):
        saved = roll_saving_throw(target.saving_throws[self.st], self.dc, reconcile_roll_types(target.saving_throws_roll_type_mod[self.st]))
        if not saved:
            logger.info(f"{target} is knocked prone")
            apply_condition(target, Condition(Conditions.PRONE, attacker))
        return None

    def calculate_threat(self, attacker, target, **kwargs):
        return 0  # TODO
