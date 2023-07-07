from itertools import combinations

from simulator.battle_map import Map
from simulator.effects.effect import EffectType
from simulator.effects.end_of_turn_combatant_effect import EndOfTurnEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.spells.hold_person import HoldPersonFactory
from simulator.spells.spell import SpellStats
from simulator.misc import SavingThrow, Conditions, ConditionWithoutDC, ROUND_HORIZON
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags

from simulator.threat_utils import get_saving_throw_success_prob, calculate_threat_in_delta
from simulator.threat_interfaces import ThreatModifierFactory, ThreatModifier
import logging

from simulator.utils.roll_types import ThreatModifierType, RollType

logger = logging.getLogger("EncounTroll")

class TwinnedHoldPersonFactory(ThreatModifierFactory):
    level = 2
    range = SpellStats.Range.FEET_60.value
    target = SpellStats.Target.TWO_CREATURES
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
        return "TwinnedHoldPersonFactory"


    def get_twinned_kwargs(self):
        return {'dc': self.dc, 'caster': self.combatant}

    def get_quickened_kwargs(self):
        return {'dc': self.dc, 'caster': self.combatant}

    def get_eligible_targets(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            return []  # Let's not waste a twinned version on this
        return combinations([e for e in Map.get().get_enemies(self.combatant) if not e.is_affected_by(Conditions.SWALLOWED)], 2)

    def create_all(self):
        targets = Map.get().get_enemies(self.combatant)
        return [TwinnedHoldPerson(t, self) for t in targets]

    def create(self, target_combatant):
        return TwinnedHoldPerson(target_combatant, self)


    def calculate_threat_to_target(self, target, *args, **kwargs):
        if target.is_affected_by_any(Conditions.PARALYZED):
            return 0
        if Map.get().get_cartesian_distance(self.combatant, target) > HoldPersonFactory.range:
            return 0

        threat_acc = 0
        # Haste factories wouldn't change the result here, so we're omitting them
        # This is an approximation, we're only looking at the best action overall, not the action + bonus_action combo
        max_action_threat = 0
        for f in target.action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags:
                max_action_threat = max(max_action_threat, f[1].calculate_max_threat())
        for f in target.bonus_action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags:
                max_action_threat = max(max_action_threat, f[1].calculate_max_threat())
        threat_acc += max_action_threat

        mods = {ThreatModifierType.ROLL_TYPE: RollType.ADVANTAGE, ThreatModifierType.AUTO_CRIT: True}
        # Neglecting the auto-crit in melee range only
        threat_acc += calculate_threat_in_delta(self.combatant, 6, mods, FactoryFlags.IS_ATTACK_LIKE)[1]

        p_success = get_saving_throw_success_prob(self.dc, target.saving_throws[self.saving_throw])
        total_threat = 0
        for _ in range(ROUND_HORIZON):
            total_threat += threat_acc * p_success
            p_success *= p_success
        return total_threat


    def calculate_max_threat(self):
        if self.combatant.get_swallower():
            return 0
        targets = [e for e in Map.get().get_enemies(self.combatant) if not e.is_affected_by(Conditions.SWALLOWED)]
        threats = sorted([self.calculate_threat_to_target(t) for t in targets], reverse=True)
        return (threats[0] if threats else 0) + (threats[1] if len(threats) > 1 else 0)


class TwinnedHoldPerson(Actoid, LimitedDurationEffect, EndOfTurnEffect, ThreatModifier):
    def __init__(self, targets, factory, **kwargs):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, turns=10)
        EndOfTurnEffect.__init__(self, factory.combatant, factory.saving_throw, factory.dc)
        self.targets = targets
        self.factory = factory


    def __str__(self):
        return f"Twinned Hold Person on {self.targets[0]} and {self.targets[1]}"

    def shorthand_str(self):
        return "Twinned Hold Person"

    def get_effect_type(self):
        return EffectType.HOLD_PERSON

    def activate(self,):
        Map.get().effect_tracker.add(self)
        self.factory.combatant.concentration_effect = self
        self.targets[0].apply_condition(ConditionWithoutDC(Conditions.PARALYZED, self))
        self.targets[1].apply_condition(ConditionWithoutDC(Conditions.PARALYZED, self))

    def deactivate(self):
        self.factory.combatant.break_concentration()
        self.targets[0].remove_condition(Conditions.PARALYZED, self)
        self.targets[1].remove_condition(Conditions.PARALYZED, self)

    def is_affecting(self, combatant):
        return combatant in self.targets


    def calculate_threat(self, **kwargs):
        return self.factory.calculate_threat_to_target(self.targets[0]) + self.factory.calculate_threat_to_target(self.targets[1])


    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        coords_for_first = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[0]),
                                                             distances,
                                                             inflate_to_size=self.factory.combatant.size,
                                                             rng=TwinnedHoldPersonFactory.range, combatant=self.factory.combatant)

        coords_for_second = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[1]),
                                                              distances,
                                                              inflate_to_size=self.factory.combatant.size,
                                                              rng=TwinnedHoldPersonFactory.range)
        return coords_for_first.intersection(coords_for_second)

    def is_current_coord_eligible(self):
        if self.factory.combatant.get_swallower():
            return False  # Impossible when blinded
        battle_map = Map.get()
        return battle_map.get_cartesian_distance(self.factory.combatant, self.targets[0]) <= HoldPersonFactory.range and \
            battle_map.get_cartesian_distance(self.factory.combatant, self.targets[1]) <= HoldPersonFactory.range
