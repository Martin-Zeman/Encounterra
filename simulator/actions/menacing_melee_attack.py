import math

from cachetools import cached
from cachetools.keys import hashkey

from .action_types import HasteAction
from .melee_attack import MeleeAttackFactory, MeleeAttack
from ..actions.actoid import FactoryFlags
from ..actions.attack import AttackFactory, Attack
from ..battle_map import Map
from ..conditions import Conditions, is_affected_by_any, get_swallower
import logging

from ..misc import SavingThrow
from ..threat_utils import calculate_threat_out_delta, get_saving_throw_fail_prob
from ..utils.roll_types import RollType, ThreatModifierType

logger = logging.getLogger("Encounterra")


class MenacingMeleeAttackFactory(MeleeAttackFactory):

    def get_ability_name(self):
        return "Menacing Melee Attack"

    def create(self, target):
        return MenacingMeleeAttack(target, self)

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [MenacingMeleeAttack(t, self) for t in targets]

    def calculate_threat_to_target(self, target, **kwargs):
        return (MeleeAttackFactory.calculate_threat_to_target(self, target) +
                get_saving_throw_fail_prob(self.combatant.dc, target.saving_throws[SavingThrow.WIS]) * calculate_threat_out_delta(target, 12, {ThreatModifierType.ROLL_TYPE: RollType.DISADVANTAGE}, FactoryFlags.IS_ATTACK_LIKE)[1])


class MenacingMeleeAttack(MeleeAttack):
    def __str__(self):
        form_prefix = str(self.factory.combatant.get_current_form()).split()[-1] + " " if self.factory.combatant.get_original_form() is not self.factory.combatant else ""
        return form_prefix + ("Hasted Menacing " if isinstance(self.factory.action_type, HasteAction) else "Menacing ") + self.factory.name + f" on {self.target}"

    def shorthand_str(self):
        return ("Hasted Menacing " if isinstance(self.factory.action_type, HasteAction) else "Menacing ") + self.factory.name
