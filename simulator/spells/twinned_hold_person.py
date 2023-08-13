from functools import cache
from itertools import combinations

from cachetools import cached
from cachetools.keys import hashkey

from simulator.battle_map import Map, map_position_toggled_cache
from simulator.effects.effect import EffectType
from simulator.effects.end_of_turn_combatant_effect import EndOfTurnEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.spells.hold_person import HoldPersonFactory
from simulator.spells.spell import SpellStats
from simulator.misc import SavingThrow, Conditions, ConditionWithoutDC, ROUND_HORIZON, roll_saving_throw, Visibility
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from simulator.threat_utils import get_saving_throw_success_prob, calculate_threat_in_delta
from simulator.threat_interfaces import ThreatModifierFactory, Threat
import logging
from simulator.utils.roll_types import ThreatModifierType, RollType

logger = logging.getLogger("Encounterra")

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
        return combinations([e for e in Map.get().get_enemies(self.combatant) if e.is_humanoid and not e.is_affected_by(Conditions.SWALLOWED)], 2)

    def create_all(self):
        targets = Map.get().get_enemies(self.combatant)
        return [TwinnedHoldPerson(t, self) for t in targets]

    def create(self, target):
        return TwinnedHoldPerson(target, self)


    def calculate_threat_to_target(self, target, **kwargs):
        if target.is_affected_by_any(Conditions.PARALYZED):
            return 0
        if Map.get().get_cartesian_distance_combatants(self.combatant, target) > HoldPersonFactory.range:
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


class TwinnedHoldPerson(Actoid, LimitedDurationEffect, EndOfTurnEffect, Threat):
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
        saved1 = roll_saving_throw(self.targets[0].saving_throws[SavingThrow.WIS], self.factory.dc, RollType.STRAIGHT)
        saved2 = roll_saving_throw(self.targets[1].saving_throws[SavingThrow.WIS], self.factory.dc, RollType.STRAIGHT)
        if not saved1:
            self.targets[0].apply_condition(ConditionWithoutDC(Conditions.PARALYZED, self))
            logger.info(f"{self.targets[0]} failed the save against Hold Person")
        else:
            logger.info(f"{self.targets[0]} saved against Hold Person")
        if not saved2:
            self.targets[1].apply_condition(ConditionWithoutDC(Conditions.PARALYZED, self))
            logger.info(f"{self.targets[1]} failed the save against Hold Person")
        else:
            logger.info(f"{self.targets[1]} saved against Hold Person")
        if not saved1 or not saved2:
            Map.get().effect_tracker.add(self)
            self.factory.combatant.concentration_effect = self

    def deactivate(self):
        if self.factory.combatant.concentration_effect is self:
            self.factory.combatant.break_concentration()
        self.targets[0].remove_condition(Conditions.PARALYZED, self)
        self.targets[1].remove_condition(Conditions.PARALYZED, self)

    def is_affecting(self, combatant):
        return combatant in self.targets

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        return self.factory.calculate_threat_to_target(self.targets[0]) + self.factory.calculate_threat_to_target(self.targets[1])

    def clear_cache(self):
        self.calculate_threat.cache_clear()

    @cached(cache={}, key=lambda self, distances, shortest_paths: hashkey())
    def get_eligible_coords(self, distances, shortest_paths):
        if self.factory.combatant.get_swallower():
            return None  # Not possible while blinded
        battle_map = Map.get()
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        if self.factory.combatant.movement > 0 and not self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            coords_for_first = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[0]),
                                                                 distances,
                                                                 inflate_to_size=self.factory.combatant.size,
                                                                 rng=TwinnedHoldPersonFactory.range, combatant=self.factory.combatant)

            coords_for_second = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[1]),
                                                                  distances,
                                                                  inflate_to_size=self.factory.combatant.size,
                                                                  rng=TwinnedHoldPersonFactory.range)
            free_coords_in_range = set(coords_for_first).intersection(set(coords_for_second))

            return [coord for coord in free_coords_in_range if
                    battle_map.visibility_dict_for_all_coords[coord][self.targets[0]] is not Visibility.NONE
                    and battle_map.visibility_dict_for_all_coords[coord][self.targets[1]] is not Visibility.NONE]
        elif battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.targets[0]) <= HoldPersonFactory.range and \
            battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.targets[1]) <= HoldPersonFactory.range and \
                battle_map.visibility_dict_for_all_coords[curr_coord][self.targets[0]] is not Visibility.NONE and \
                battle_map.visibility_dict_for_all_coords[curr_coord][self.targets[1]] is not Visibility.NONE:
            return [curr_coord]
        return None
