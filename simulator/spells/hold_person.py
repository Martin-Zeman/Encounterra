import copy

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import BonusAction, Passive
from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key
from ..effects.effect import EffectType
from ..effects.end_of_turn_combatant_effect import EndOfTurnEffect
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..spells.spell import SpellStats
from ..misc import SavingThrow, ROUND_HORIZON, roll_saving_throw, Visibility, reconcile_roll_types
from ..conditions import Conditions, Condition, is_affected_by_any, is_affected_by, get_swallower, \
    apply_condition, remove_condition
from ..actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import cache
from ..threat_utils import get_saving_throw_fail_prob, calculate_threat_in_delta
from ..threat_interfaces import Threat
from ..factory_interfaces import ThreatModifierFactory
import logging
from ..utils.roll_types import RollType, ThreatModifierType

logger = logging.getLogger("Encounterra")


class HoldPersonFactory(ThreatModifierFactory):
    level = 2
    range = SpellStats.Range.FEET_60.value
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL

    def __init__(self, dc, action_type, caster, resource):
        super().__init__()
        self.flags |= FactoryFlags.PREVENT_ENDLESS_RECURSION
        self.dc = dc
        self.action_type = action_type  # HOLD_PERSON, QUICKENED_HOLD_PERSON
        self.combatant = caster
        self.saving_throw = SavingThrow.WIS
        self.resource = resource

    def __str__(self):
        """
        Important for FSM building
        """
        return "HoldPersonFactory"

    def get_ability_name(self):
        return "Hold Person"

    def get_twinned_kwargs(self):
        return {'dc': self.dc, 'caster': self.combatant, 'resource': self.resource}

    def get_quickened_kwargs(self):
        return {'dc': self.dc, 'caster': self.combatant, 'resource': self.resource}

    def get_eligible_targets(self):
        swallower = get_swallower(self.combatant)
        if swallower:
            return []  # Must be able to see
        return [e for e in Map.get().get_non_swallowed_enemies(self.combatant) if e.is_humanoid]

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [HoldPerson(t, self) for t in targets]

    def create(self, target):
        return HoldPerson(target, self)

    def calculate_threat_to_target(self, target, **kwargs):
        if is_affected_by_any(target, Conditions.PARALYZED):
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
        return total_threat

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        if not targets:
            return 0
        return max([self.calculate_threat_to_target(t) for t in targets])


class HoldPerson(Actoid, LimitedDurationEffect, EndOfTurnEffect, Threat):
    def __init__(self, target, factory, **kwargs):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, factory.combatant, turns=10)
        EndOfTurnEffect.__init__(self, factory.combatant, [target], factory.saving_throw, factory.dc)
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_HOLD_PERSON else "") + f"Hold Person on {self.combatants[0]}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_HOLD_PERSON else "") + "Hold Person"

    def get_effect_type(self):
        return EffectType.HOLD_PERSON

    def activate(self, **kwargs):
        roll_type_modifiers = copy.copy(self.combatants[0].saving_throws_roll_type_mod[self.st])  # Make a copy because it's related to this ability and not to all WIS saves
        if self.combatants[0].has_passive(Passive.MAGIC_RESISTANCE):
            logger.info(f"{self.combatants[0]} gains advantage against Hold Person through Magic Resistance")
            roll_type_modifiers.add(RollType.ADVANTAGE)
        elif self.combatants[0].has_passive(Passive.HEART_OF_HRUGGEK):
            logger.info(f"{self.combatants[0]} gains advantage against Hold Person through Heart of Hruggek")
            roll_type_modifiers.add(RollType.ADVANTAGE)
        saved = roll_saving_throw(self.combatants[0].saving_throws[self.st], self.dc, reconcile_roll_types(roll_type_modifiers))
        if not saved:
            logger.info(f"{self.combatants[0]} failed the save against Hold Person")
            Map.get().effect_tracker.add(self)
            self.factory.combatant.concentration_effect = self
            apply_condition(self.combatants[0], Condition(Conditions.PARALYZED, self.factory.combatant, self))
        else:
            logger.info(f"{self.combatants[0]} saved against Hold Person")

    def combatant_saved_at_end_of_turn(self, combatant):
        roll_type_modifiers = copy.copy(combatant.saving_throws_roll_type_mod[self.st])  # Make a copy because it's related to this ability and not to all WIS saves
        if combatant.has_passive(Passive.MAGIC_RESISTANCE):
            logger.info(f"{combatant} gains advantage against Hold Person through Magic Resistance")
            roll_type_modifiers.add(RollType.ADVANTAGE)
        elif combatant.has_passive(Passive.HEART_OF_HRUGGEK):
            logger.info(f"{combatant} gains advantage against Hold Person through Heart of Hruggek")
            roll_type_modifiers.add(RollType.ADVANTAGE)
        saved = roll_saving_throw(combatant.saving_throws[self.st], self.dc, reconcile_roll_types(roll_type_modifiers))
        if saved:
            logger.info(f"{combatant} saved against {self}")
            return False
        logger.info(f"{combatant} failed the save against {self}")
        return True

    def deactivate(self):
        self.factory.combatant.break_concentration()
        remove_condition(self.combatants[0], Conditions.PARALYZED, self.factory.combatant)

    def deactivate_for_combatant(self, combatant):
        if combatant is self.combatants[0]:
            self.factory.combatant.break_concentration()
            remove_condition(self.combatants[0], Conditions.PARALYZED, self.factory.combatant)

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        ret = self.factory.calculate_threat_to_target(self.combatants[0])
        return ret

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        #self.get_eligible_coords.cache_clear()

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if get_swallower(self.factory.combatant):
            return None  # Not possible while blinded
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            free_coords_in_range = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.combatants[0]),
                                                                 distances,
                                                                 inflate_to_dist=self.factory.combatant.size.value,
                                                                 rng=HoldPersonFactory.range, combatant=self.factory.combatant)
            return [coord for coord in free_coords_in_range if battle_map.visibility_dict_for_all_coords[coord][self.combatants[0]] is not Visibility.NONE]
        elif battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.combatants[0]) <= HoldPersonFactory.range and \
                battle_map.visibility_dict_for_all_coords[curr_coord][self.combatants[0]] is not Visibility.NONE:
            return [curr_coord]
        return None
