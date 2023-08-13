from cachetools import cached
from cachetools.keys import hashkey

from simulator.actions.action_types import BonusAction
from simulator.battle_map import Map, map_position_toggled_cache
from simulator.effects.effect import EffectType
from simulator.effects.end_of_turn_combatant_effect import EndOfTurnEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.spells.spell import SpellStats
from simulator.misc import SavingThrow, Conditions, ROUND_HORIZON, ConditionWithoutDC, roll_saving_throw, Visibility
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import cache
from simulator.threat_utils import get_saving_throw_fail_prob, calculate_threat_in_delta
from simulator.threat_interfaces import ThreatModifierFactory, Threat
import logging
from simulator.utils.roll_types import RollType, ThreatModifierType

logger = logging.getLogger("Encounterra")

class HoldPersonFactory(ThreatModifierFactory):
    level = 2
    range = SpellStats.Range.FEET_60.value
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL

    def __init__(self, dc, action_type, caster):
        super().__init__()
        self.flags |= FactoryFlags.USES_CALCULATE_THREAT_IN_DELTA
        self.dc = dc
        self.action_type = action_type  # HOLD_PERSON, QUICKENED_HOLD_PERSON
        self.combatant = caster
        self.saving_throw = SavingThrow.WIS


    def __str__(self):
        """
        Important for FSM building
        """
        return "HoldPersonFactory"


    def get_twinned_kwargs(self):
        return {'dc': self.dc, 'caster': self.combatant}

    def get_quickened_kwargs(self):
        return {'dc': self.dc, 'caster': self.combatant}


    def create_all(self):
        targets = Map.get().get_enemies(self.combatant)
        return [HoldPerson(t, self) for t in targets]

    def create(self, target):
        return HoldPerson(target, self)


    def calculate_threat_to_target(self, target, **kwargs):
        if target.is_affected_by_any(Conditions.PARALYZED):
            return 0
        if Map.get().get_cartesian_distance_combatants(self.combatant, target) > HoldPersonFactory.range:
            return 0

        prevented_threat_out_acc = 0
        # Haste factories wouldn't change the result here, so we're omitting them
        # This is an approximation, we're only looking at the best action overall, not the action + bonus_action combo
        max_action_threat = 0
        for f in target.action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags:
                max_action_threat = max(max_action_threat, f[1].calculate_max_threat())
        for f in target.bonus_action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags:
                max_action_threat = max(max_action_threat, f[1].calculate_max_threat())
        prevented_threat_out_acc += max_action_threat

        mods = {ThreatModifierType.ROLL_TYPE: RollType.ADVANTAGE, ThreatModifierType.AUTO_CRIT: True}
        # Neglecting the auto-crit in melee range only
        threat_in_delta = min(target.curr_hp, calculate_threat_in_delta(target, 6, mods, FactoryFlags.IS_ATTACK_LIKE)[1])
        threat_round_total = prevented_threat_out_acc + threat_in_delta

        p_fail = get_saving_throw_fail_prob(self.dc, target.saving_throws[self.saving_throw])
        p_fail_acc = p_fail
        total_threat = 0
        for _ in range(ROUND_HORIZON):
            total_threat += threat_round_total * p_fail_acc
            p_fail_acc *= p_fail
        # logger.warning(f"MY DEBUG {self} calculate_threat_to_target ={total_threat}")
        return total_threat

    def get_eligible_targets(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            return []  # Must be able to see
        return [e for e in Map.get().get_enemies(self.combatant) if e.is_humanoid and not e.is_affected_by(Conditions.SWALLOWED)]

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        ret = max([self.calculate_threat_to_target(t) for t in targets])
        # logger.warning(f"MY DEBUG {self} calculate_max_threat = {ret}")
        return ret


class HoldPerson(Actoid, LimitedDurationEffect, EndOfTurnEffect, Threat):
    def __init__(self, target, factory, **kwargs):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, turns=10)
        EndOfTurnEffect.__init__(self, target, factory.saving_throw, factory.dc)
        self.target = target
        self.factory = factory


    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_HOLD_PERSON else "") + f"Hold Person on {self.target}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_HOLD_PERSON else "") + "Hold Person"


    def get_effect_type(self):
        return EffectType.HOLD_PERSON

    def activate(self):
        if not roll_saving_throw(self.target.saving_throws[SavingThrow.WIS], self.factory.dc, RollType.STRAIGHT):
            logger.info(f"{self.target} failed the save against Hold Person")
            Map.get().effect_tracker.add(self)
            self.factory.combatant.concentration_effect = self
            self.target.apply_condition(ConditionWithoutDC(Conditions.PARALYZED, self))
        else:
            logger.info(f"{self.target} saved against Hold Person")

    def deactivate(self):
        self.factory.combatant.break_concentration()
        self.target.remove_condition(Conditions.PARALYZED, self)

    def is_affecting(self, combatant):
        return combatant is self.target

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        ret = self.factory.calculate_threat_to_target(self.target)
        return ret

    def clear_cache(self):
        self.calculate_threat.cache_clear()

    @cached(cache={}, key=lambda self, distances, shortest_paths: hashkey())
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if self.factory.combatant.get_swallower():
            return None  # Not possible while blinded
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        if self.factory.combatant.movement > 0 and not self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            free_coords_in_range = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.target),
                                                                 distances,
                                                                 inflate_to_size=self.factory.combatant.size,
                                                                 rng=HoldPersonFactory.range, combatant=self.factory.combatant)
            return [coord for coord in free_coords_in_range if battle_map.visibility_dict_for_all_coords[coord][self.target] is not Visibility.NONE]
        elif battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.target) <= HoldPersonFactory.range and \
                battle_map.visibility_dict_for_all_coords[curr_coord][self.target] is not Visibility.NONE:
            return [curr_coord]
        return None
