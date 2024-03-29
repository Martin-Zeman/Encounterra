import math

from .actoid import FactoryFlags
from .ranged_attack import RangedAttackFactory
from ..misc import get_superiority_dice
from ..resources import Uses, ResourceRefreshType


class PrecisionRangedAttackFactory(RangedAttackFactory):
    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=Uses(math.inf, ResourceRefreshType.NEVER), on_hit=[], extra_dmg=[], uses_dex=True, **kwargs):
        superiority_dice = get_superiority_dice(combatant.level)
        name = "Precision " + name
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg, uses_dex, superiority_dice)
        self.flags |= FactoryFlags.IS_PRECISION

    def get_ability_name(self):
        return "Precision Ranged Attack"
