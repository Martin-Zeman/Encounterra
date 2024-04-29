from .on_hit_saving_throw_effect import OnHitSavingThrowEffect
from ..abilities.on_hit_effect import OnHit
from ..misc import roll_saving_throw, reconcile_roll_types, Class
import logging

logger = logging.getLogger("Encounterra")


class OnHitSavingThrowParalysis(OnHitSavingThrowEffect):
    def __init__(self, st, dc, name="On Hit Saving Throw Paralysis"):
        self.st = st
        self.dc = dc
        self.name = name

    def hit(self, attacker, attack, target, multiplier, dmg_so_far):
        if type(attacker).cls is Class.MONSTER.UNDEAD:
            return None
        saved = roll_saving_throw(target.saving_throws[self.st], self.dc, reconcile_roll_types(target.saving_throws_roll_type_mod[self.st]))
        if not saved:
            attack.activate()
        return None

    def calculate_threat(self, attacker, target, **kwargs):
        return 0  # Calculated in the attack itself, it's too specific
