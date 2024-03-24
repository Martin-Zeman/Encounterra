import math

from .action_types import Action, BonusAction
from .actoid import FactoryFlags
from .melee_attack import MeleeAttackFactory
from ..misc import get_superiority_dice


class PrecisionMeleeAttackFactory(MeleeAttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=math.inf, on_hit=[], extra_dmg=[], uses_dex=False, two_handed=False, **kwargs):
        superiority_dice = get_superiority_dice(combatant.level)
        name = "Precision " + name
        # if isinstance(action_type, Action):
        #     action_type = Action.PRECISION_MELEE_ATTACK
        # else:
        #     action_type = BonusAction.BONUS_PRECISION_MELEE_ATTACK
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg, uses_dex, two_handed, superiority_dice)
        self.flags |= FactoryFlags.IS_PRECISION

    def get_ability_name(self):
        return "Precision Melee Attack"
