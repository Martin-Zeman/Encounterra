import math

from cachetools import cached
from cachetools.keys import hashkey

from .action_types import Action
from .melee_attack import MeleeAttackFactory, MeleeAttack
from ..abilities.on_hit_saving_throw_paralysis import OnHitSavingThrowParalysis
from ..actions.actoid import FactoryFlags
from ..battle_map import Map
from ..conditions import Conditions, apply_condition, Condition, remove_condition, \
    get_source_of_paralyzed, is_affected_by_any
import logging

from ..effects.effect import EffectType
from ..effects.end_of_turn_combatant_effect import EndOfTurnEffect
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..misc import SavingThrow, roll_saving_throw, ROUND_HORIZON
from ..resources import Uses, ResourceRefreshType
from ..threat_utils import get_saving_throw_fail_prob, calculate_threat_in_delta
from ..utils.roll_types import RollType, ThreatModifierType

logger = logging.getLogger("Encounterra")


class ParalyzingAttackFactory(MeleeAttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=Uses(math.inf, ResourceRefreshType.NEVER), on_hit=None, extra_dmg=None, uses_dex=False, two_handed=False, to_hit_bonus_die=None):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg, uses_dex, two_handed, to_hit_bonus_die)
        self.saving_throw = SavingThrow.CON
        self.on_hit.append(OnHitSavingThrowParalysis(self.saving_throw, combatant.dc, "Paralyzed"))
        self.flags |= FactoryFlags.PREVENT_ENDLESS_RECURSION

    def get_ability_name(self):
        return self.name

    def create(self, target):
        return ParalyzingAttack(target, self)

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [ParalyzingAttack(t, self) for t in targets]

    def calculate_threat_to_target(self, target, **kwargs):
        total_threat = MeleeAttackFactory.calculate_threat_to_target(self, target)
        if is_affected_by_any(target, Conditions.PARALYZED):
            return total_threat

        prevented_threat_out_acc = 0
        # Haste factories wouldn't change the result here, so we're omitting them
        # This is an approximation, we're only looking at the best action overall, not the action + bonus_action combo
        max_action_threat = 0
        for f in target.action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags and FactoryFlags.PREVENT_ENDLESS_RECURSION not in f[1].flags:
                max_action_threat = max(max_action_threat, f[1].calculate_max_threat())
        for bf in target.bonus_action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in bf[1].flags and FactoryFlags.PREVENT_ENDLESS_RECURSION not in bf[1].flags:
                max_action_threat = max(max_action_threat, bf[1].calculate_max_threat())
        prevented_threat_out_acc += max_action_threat

        mods = {ThreatModifierType.ROLL_TYPE: RollType.ADVANTAGE, ThreatModifierType.AUTO_CRIT: True}
        # Neglecting the auto-crit in melee range only
        threat_in_delta = min(target.curr_hp, calculate_threat_in_delta(target, 6, mods, FactoryFlags.IS_ATTACK_LIKE)[1])
        threat_round_total = prevented_threat_out_acc + threat_in_delta

        p_fail = get_saving_throw_fail_prob(self.combatant.dc, target.saving_throws[self.saving_throw])
        p_fail_acc = p_fail
        for _ in range(ROUND_HORIZON):
            total_threat += threat_round_total * p_fail_acc
            p_fail_acc *= p_fail
        return total_threat

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        if not targets:
            return 0
        return max([self.calculate_threat_to_target(t) for t in targets])


class ParalyzingAttack(MeleeAttack, LimitedDurationEffect, EndOfTurnEffect):

    def __init__(self, target, factory):
        MeleeAttack.__init__(self, target, factory)
        LimitedDurationEffect.__init__(self, factory.combatant, turns=10)
        EndOfTurnEffect.__init__(self, factory.combatant, [target], factory.saving_throw, factory.combatant.dc)

    def get_effect_type(self):
        return EffectType.PARALYZING_ATTACK_PARALYZED

    def activate(self, **kwargs):
        Map.get().effect_tracker.add(self)
        logger.info(f"{self.target} is paralyzed")
        apply_condition(self.target, Condition(Conditions.PARALYZED, self.factory.combatant, self))

    def deactivate(self):
        logger.info(f"{self.target} is no longer paralyzed")
        remove_condition(self.target, Conditions.PARALYZED, self.factory.combatant)

    def combatant_saved_at_end_of_turn(self, combatant):
        saved = roll_saving_throw(combatant.saving_throws[self.factory.saving_throw], self.factory.combatant.dc, combatant.saving_throws_roll_type_mod[self.st])
        if saved:
            logger.info(f"{combatant} saved against {self}")
            return False
        logger.info(f"{combatant} failed the save against {self}")
        return True

    def is_affecting(self, combatant):
        return self.target is combatant

    def deactivate_for_combatant(self, combatant):
        self.deactivate()
        return False
