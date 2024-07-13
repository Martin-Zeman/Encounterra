from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import BonusAction
from ..battle_map import Map, map_toggled_cache_with_key, map_position_toggled_cache, \
    _get_free_coords_in_cartesian_range
from ..effects.combatant_effect import CombatantEffect
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..conditions import Conditions, is_affected_by_any, is_affected_by, get_swallower
from ..spells.spell import SpellStats
from ..effects.effect import  EffectType
from ..actions.actoid import Actoid, ActoidFlags, FactoryFlags
from ..factory_interfaces import ThreatModifierFactory

from ..threat_utils import calculate_threat_in_delta
from ..utils.roll_types import ThreatModifierType


class ShieldOfFaithFactory(ThreatModifierFactory):
    level = 1
    range = SpellStats.Range.FEET_60.value
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.TEN_MINUTES
    concentration = True
    type = SpellStats.Type.BUFF
    dc = None
    dmg_type = None

    def __init__(self, caster, resource):
        super().__init__()
        self.action_type = BonusAction.SHIELD_OF_FAITH
        self.combatant = caster
        self.resource = resource

    def __str__(self):
        """
        Important for FSM building
        """
        return "ShieldOfFaithFactory"

    def get_ability_name(self):
        return "Shield of Faith"

    def get_quickened_kwargs(self):
        return {'caster': self.combatant, 'resource': self.resource}

    def get_eligible_targets(self):
        if get_swallower(self.combatant):  # Even though RAW it's not necessary it may cause bugs
            return [self.combatant]
        ret = Map.get().get_non_swallowed_allies_within_radius(self.combatant, ShieldOfFaithFactory.range)
        ret.append(self.combatant)
        return ret

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [ShieldOfFaith(t, self) for t in targets]

    def calculate_threat_to_target(self, target, **kwargs):
        incoming_threat_delta = calculate_threat_in_delta(target, 6, {ThreatModifierType.TARGET_AC: 2}, FactoryFlags.IS_ATTACK_LIKE)[1]
        return incoming_threat_delta

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        if not targets:
            return 0
        return max([calculate_threat_in_delta(t, 6, {ThreatModifierType.TARGET_AC: 2}, FactoryFlags.IS_ATTACK_LIKE)[1] for t in targets])


class ShieldOfFaith(Actoid, CombatantEffect, LimitedDurationEffect):
    def __init__(self, target, factory):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        CombatantEffect.__init__(self, factory.combatant, [target])
        LimitedDurationEffect.__init__(self, factory.combatant, turns=100)
        self.factory = factory

    def __str__(self):
        return f"Shield of Faith on {self.combatants[0]}"

    def shorthand_str(self):
        return "Shield of Faith"

    def get_effect_type(self):
        return EffectType.SHIELD_OF_FAITH

    def activate(self, **kwargs):
        Map.get().effect_tracker.add(self)
        self.factory.combatant.concentration_effect = self
        self.combatants[0].ac += 2

    def deactivate(self):
        self.factory.combatant.break_concentration()
        self.combatants[0].ac -= 2

    def deactivate_for_combatant(self, combatant):
        assert False

    def is_affecting(self, combatant):
        return combatant in self.combatants

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        incoming_threat_delta = -1 * calculate_threat_in_delta(self.combatants[0], 6, {ThreatModifierType.TARGET_AC: 2}, FactoryFlags.IS_ATTACK_LIKE)[0]
        return incoming_threat_delta

    def clear_cache(self):
        self.calculate_threat.cache_clear()


    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        if get_swallower(self.factory.combatant):
            return None
        battle_map = Map.get()
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            free_coords_in_range = _get_free_coords_in_cartesian_range(
                battle_map.grid,
                battle_map.get_combatant_position(self.combatants[0]).get(),
                distances,
                inflate_to_dist=self.factory.combatant.size.value,
                rng=ShieldOfFaithFactory.range, combatant_id=self.factory.combatant.id)
            return free_coords_in_range
        elif battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.combatants[0]) <= ShieldOfFaithFactory.range:
            return [curr_coord]
        return None
