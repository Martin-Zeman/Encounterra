import math

from cachetools import cached
from cachetools.keys import hashkey

from .action_types import Action, BonusAction
from .melee_attack import MeleeAttackFactory, MeleeAttack
from ..abilities.on_hit_saving_throw_effect import OnHitSavingThrowEffect
from ..actions.actoid import FactoryFlags
from ..battle_map import Map
from ..conditions import Conditions, apply_condition, Condition, remove_condition, get_source_of_frightened, \
    is_affected_by_any
import logging

from ..effects.effect import EffectType
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..misc import SavingThrow, get_superiority_dice
from ..resources import Uses, ResourceRefreshType
from ..threat_utils import calculate_threat_out_delta, get_saving_throw_fail_prob
from ..utils.roll_types import RollType, ThreatModifierType

logger = logging.getLogger("Encounterra")


class MenacingMeleeAttackFactory(MeleeAttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=Uses(math.inf, ResourceRefreshType.NEVER), on_hit=None, extra_dmg=None, uses_dex=False, two_handed=False, to_hit_bonus_die=None):
        dmg_dice = dmg_dice + (get_superiority_dice(combatant.level), )
        name = "Menacing " + name
        on_hit.append(OnHitSavingThrowEffect(SavingThrow.WIS, combatant.dc, "Frightened by Menacing Attack"))
        if isinstance(action_type, Action):
            action_type = Action.MENACING_MELEE_ATTACK
        else:
            action_type = BonusAction.BONUS_MENACING_MELEE_ATTACK
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg, uses_dex, two_handed, to_hit_bonus_die)

    def get_ability_name(self):
        return "Menacing Melee Attack"

    def create(self, target):
        return MenacingMeleeAttack(target, self)

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [MenacingMeleeAttack(t, self) for t in targets]

    def calculate_threat_to_target(self, target, **kwargs):
        total_threat = MeleeAttackFactory.calculate_threat_to_target(self, target)
        if is_affected_by_any(target, Conditions.FRIGHTENED):
            return total_threat - 1  # We want to discourage the Fighter from wasting resources
        total_threat += get_saving_throw_fail_prob(self.combatant.dc, target.saving_throws[SavingThrow.WIS]) * calculate_threat_out_delta(target, 12, {ThreatModifierType.ROLL_TYPE: RollType.DISADVANTAGE}, FactoryFlags.IS_ATTACK_LIKE)[1]
        return total_threat


class MenacingMeleeAttack(MeleeAttack, LimitedDurationEffect):

    def __init__(self, target, factory):
        MeleeAttack.__init__(self, target, factory)
        LimitedDurationEffect.__init__(self, factory.combatant, turns=1)

    def get_effect_type(self):
        return EffectType.MENACING_ATTACK_FRIGHTENED

    def activate(self, **kwargs):
        logger.info(f"{self.target} is frightened")
        Map.get().effect_tracker.add(self)
        apply_condition(self.target, Condition(Conditions.FRIGHTENED, self.factory.combatant))

    def deactivate(self):
        logger.info(f"{self.target} is no longer frightened")
        remove_condition(self.target, Conditions.FRIGHTENED, self.factory.combatant)

    def is_affecting(self, combatant):
        return self.target is combatant

    def deactivate_for_combatant(self, combatant):
        self.deactivate()
        return False
