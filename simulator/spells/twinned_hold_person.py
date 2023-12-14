import copy
from functools import cache
from itertools import combinations

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import Passive
from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key
from ..effects.effect import EffectType
from ..effects.end_of_turn_combatant_effect import EndOfTurnEffect
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..spells.hold_person import HoldPersonFactory
from ..spells.spell import SpellStats
from ..misc import SavingThrow, Conditions, ConditionWithoutDC, ROUND_HORIZON, roll_saving_throw, Visibility, \
    reconcile_roll_types
from ..actions.actoid import Actoid, FactoryFlags, ActoidFlags
from ..threat_utils import get_saving_throw_success_prob, calculate_threat_in_delta
from ..threat_interfaces import Threat
from ..factory_interfaces import ThreatModifierFactory
import logging
from ..utils.roll_types import ThreatModifierType, RollType

logger = logging.getLogger("Encounterra")

class TwinnedHoldPersonFactory(ThreatModifierFactory):
    level = 2
    range = SpellStats.Range.FEET_60.value
    target = SpellStats.Target.TWO_CREATURES
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL

    def __init__(self, dc, action_type, caster, resource):
        super().__init__()
        self.flags |= FactoryFlags.USES_CALCULATE_THREAT_IN_DELTA
        self.dc = dc
        self.action_type = action_type  # HOLD_PERSON, QUICKENED_HOLD_PERSON
        self.combatant = caster
        self.resource = resource
        self.saving_throw = SavingThrow.WIS

    def __str__(self):
        """
        Important for FSM building
        """
        return "TwinnedHoldPersonFactory"


    def get_twinned_kwargs(self):
        return {'dc': self.dc, 'caster': self.combatant, 'resource': self.resource}

    def get_quickened_kwargs(self):
        return {'dc': self.dc, 'caster': self.combatant}

    def get_eligible_targets(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            return []  # Let's not waste a twinned version on this
        enemies = Map.get().get_enemies(self.combatant)
        if len(enemies) < 2:
            return []  # Let's not waste a twinned version on this
        return combinations([e for e in enemies if e.is_humanoid and not e.is_affected_by(Conditions.SWALLOWED)], 2)

    def create_all(self, previous_action_in_dag=None):
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
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, factory.combatant, turns=10)
        EndOfTurnEffect.__init__(self, factory.combatant, targets, factory.saving_throw, factory.dc)
        self.factory = factory


    def __str__(self):
        return f"Twinned Hold Person on {self.combatants[0]} and {self.combatants[1]}"

    def shorthand_str(self):
        return "Twinned Hold Person"

    def get_effect_type(self):
        return EffectType.HOLD_PERSON

    def activate(self,):
        st = self.factory.saving_throw
        dc = self.factory.dc
        roll_type_modifiers_1 = copy.copy(self.combatants[0].saving_throws_roll_type_mod[st])
        if self.combatants[0].has_passive(Passive.MAGIC_RESISTANCE):
            logger.info(f"{self.combatants[0]} gains advantage against Hold Person through Magic Resistance")
            roll_type_modifiers_1.add(RollType.ADVANTAGE)
        elif self.combatants[0].has_passive(Passive.HEART_OF_HRUGGEK):
            logger.info(f"{self.combatants[0]} gains advantage against Hold Person through Heart of Hruggek")
            roll_type_modifiers_1.add(RollType.ADVANTAGE)
        saved_1 = roll_saving_throw(self.combatants[0].saving_throws[st], dc, reconcile_roll_types(roll_type_modifiers_1))
        roll_type_modifiers_2 = copy.copy(self.combatants[1].saving_throws_roll_type_mod[st])
        if self.combatants[1].has_passive(Passive.MAGIC_RESISTANCE):
            logger.info(f"{self.combatants[1]} gains advantage against Hold Person through Magic Resistance")
            roll_type_modifiers_2.add(RollType.ADVANTAGE)
        elif self.combatants[1].has_passive(Passive.HEART_OF_HRUGGEK):
            logger.info(f"{self.combatants[1]} gains advantage against Hold Person through Heart of Hruggek")
            roll_type_modifiers_2.add(RollType.ADVANTAGE)
        saved_2 = roll_saving_throw(self.combatants[1].saving_throws[st], dc, reconcile_roll_types(roll_type_modifiers_2))

        if not saved_1:
            self.combatants[0].apply_condition(ConditionWithoutDC(Conditions.PARALYZED, self))
            logger.info(f"{self.combatants[0]} failed the save against Hold Person")
        else:
            logger.info(f"{self.combatants[0]} saved against Hold Person")
        if not saved_2:
            self.combatants[1].apply_condition(ConditionWithoutDC(Conditions.PARALYZED, self))
            logger.info(f"{self.combatants[1]} failed the save against Hold Person")
        else:
            logger.info(f"{self.combatants[1]} saved against Hold Person")
        if not saved_1 or not saved_2:
            Map.get().effect_tracker.add(self)
            self.factory.combatant.concentration_effect = self

    def deactivate(self):
        if self.factory.combatant.concentration_effect is self:
            self.factory.combatant.break_concentration()
        self.combatants[0].remove_condition(Conditions.PARALYZED, self)
        self.combatants[1].remove_condition(Conditions.PARALYZED, self)

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        return self.factory.calculate_threat_to_target(self.combatants[0]) + self.factory.calculate_threat_to_target(self.combatants[1])

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        #self.get_eligible_coords.cache_clear()

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        if self.factory.combatant.get_swallower():
            return None  # Not possible while blinded
        battle_map = Map.get()
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        if not self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            coords_for_first = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.combatants[0]),
                                                                 distances,
                                                                 inflate_to_dist=self.factory.combatant.size.value,
                                                                 rng=TwinnedHoldPersonFactory.range, combatant=self.factory.combatant)

            coords_for_second = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.combatants[1]),
                                                                  distances,
                                                                  inflate_to_dist=self.factory.combatant.size.value,
                                                                  rng=TwinnedHoldPersonFactory.range)
            free_coords_in_range = set(coords_for_first).intersection(set(coords_for_second))

            return [coord for coord in free_coords_in_range if
                    battle_map.visibility_dict_for_all_coords[coord][self.combatants[0]] is not Visibility.NONE
                    and battle_map.visibility_dict_for_all_coords[coord][self.combatants[1]] is not Visibility.NONE]
        elif battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.combatants[0]) <= HoldPersonFactory.range and \
            battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.combatants[1]) <= HoldPersonFactory.range and \
                battle_map.visibility_dict_for_all_coords[curr_coord][self.combatants[0]] is not Visibility.NONE and \
                battle_map.visibility_dict_for_all_coords[curr_coord][self.combatants[1]] is not Visibility.NONE:
            return [curr_coord]
        return None
