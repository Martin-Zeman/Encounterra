import math

from cachetools import cached
from cachetools.keys import hashkey

from .melee_attack import MeleeAttackFactory, MeleeAttack
from ..actions.actoid import FactoryFlags
from ..actions.attack import AttackFactory, Attack
from ..battle_map import Map
from ..conditions import Conditions, is_affected_by_any, get_swallower
import logging


logger = logging.getLogger("Encounterra")


class PrecisionMeleeAttackFactory(MeleeAttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=math.inf, on_hit=[], extra_dmg=[], uses_dex=False, two_handed=False):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg, uses_dex, two_handed)
        self.flags |= FactoryFlags.IS_MELEE

    def get_ability_name(self):
        return "Precision Melee Attack"

    def create(self, target):
        return PrecisionMeleeAttack(target, self)

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [PrecisionMeleeAttack(t, self) for t in targets]


class PrecisionMeleeAttack(MeleeAttack):
    pass
