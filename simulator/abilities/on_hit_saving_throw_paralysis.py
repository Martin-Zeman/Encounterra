from .on_hit_saving_throw_effect import OnHitSavingThrowEffect
from ..misc import reconcile_roll_types, Class
import logging

from ..utils.utils import roll_saving_throw

logger = logging.getLogger("Encounterra")


class OnHitSavingThrowParalysis(OnHitSavingThrowEffect):

    def hit(self, attacker, attack, target, multiplier, dmg_so_far):
        if type(target).cls is Class.MONSTER.UNDEAD:
            return None
        saved = roll_saving_throw(target.saving_throws[self.st], self.dc, reconcile_roll_types(target.saving_throws_roll_type_mod[self.st]))
        if not saved:
            attack.activate()
        return None
