from ..actions.action_types import BonusAction
from ..battle_map import Map
from ..effects.combatant_effect import CombatantEffect
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..misc import get_attack_factories, ROUND_HORIZON
from ..conditions import Conditions, is_affected_by_any, get_swallower
from ..spells.spell import SpellStats
from ..effects.effect import EffectType
from ..actions.actoid import ActoidFlags
from ..threat_interfaces import AttackThreatModifier
from ..factory_interfaces import ThreatModifierFactory
from itertools import combinations
import numba_functions as nf
from ..utils.roll_types import ThreatModifierType

SAVING_THROW_BONUS_MULTIPLIER = 1.25


class BlessFactory(ThreatModifierFactory):
    level = 1
    range = SpellStats.Range.FEET_30.value
    target = SpellStats.Target.THREE_CREATURES
    duration = SpellStats.Duration.MINUTE
    concentration = True
    type = SpellStats.Type.BUFF
    dc = None
    dmg_type = None

    def __init__(self, action_type, caster, resource):
        super().__init__()
        self.action_type = action_type  # QUICKENED_BLESS, BLESS
        self.combatant = caster
        self.resource = resource

    def __str__(self):
        """
        Important for FSM building
        """
        return "BlessFactory"

    def get_ability_name(self):
        return "Bless"

    def get_quickened_kwargs(self):
        return {'caster': self.combatant, 'resource': self.resource}

    def get_eligible_targets(self):
        swallower = get_swallower(self.combatant)
        if swallower:
            return [self.combatant]
        allies = Map.get().get_non_swallowed_allies_within_radius(self.combatant, BlessFactory.range)
        allies.append(self.combatant)
        return combinations(allies, 3)

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [Bless(t, self) for t in targets]

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates the threat the factory is capable of dealing to a specific target.
        This is useful for calculating threat_in from the abilities of enemies
        """
        max_threat_increase = 0
        afs = get_attack_factories(target)
        for af in afs:
            eligible_targets = af.get_eligible_targets()
            for et in eligible_targets:
                threat_inc = af.calculate_threat_to_target_delta(et, {ThreatModifierType.TO_HIT_DIE: (1, 4)})
                max_threat_increase = max(threat_inc, max_threat_increase)
        return max_threat_increase * SAVING_THROW_BONUS_MULTIPLIER * ROUND_HORIZON

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        if not targets:
            return 0
        return max([self.calculate_threat_to_target(t) for t in targets])


class Bless(AttackThreatModifier, CombatantEffect, LimitedDurationEffect):
    def __init__(self, targets, factory):
        AttackThreatModifier.__init__(self, ActoidFlags.IS_SPELL)
        CombatantEffect.__init__(self, factory.combatant, targets)
        LimitedDurationEffect.__init__(self, factory.combatant, turns=10)
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_BLESS else "") + f"Bless on {self.combatants[0]}, {self.combatants[1]} and {self.combatants[2]}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_BLESS else "") + f"Bless"

    def get_effect_type(self):
        return EffectType.BLESS

    def activate(self, **kwargs):
        Map.get().effect_tracker.add(self)
        # todo should check if not already under the influence of another bless
        self.factory.combatant.concentration_effect = self
        for target in self.combatants:
            for mod in target.saving_throws_dice_mod.values():
                mod.append((1, 4))
            target.to_hit_dice_mod.append((1, 4))

    def deactivate(self):
        self.factory.combatant.break_concentration()
        for target in self.combatants:
            for mod in target.saving_throws_dice_mod.values():
                mod.remove((1, 4))
            target.to_hit_dice_mod.remove((1, 4))

    def deactivate_for_combatant(self, combatant):
        assert False

    def is_affecting(self, combatant):
        return combatant in self.combatants

    def calculate_threat(self, **kwargs):
        total_threat_increase = 0
        for ally in self.combatants:
            max_threat_increase = 0
            afs = get_attack_factories(ally)
            for af in afs:
                eligible_targets = af.get_eligible_targets()
                for et in eligible_targets:
                    threat_inc = af.calculate_threat_to_target_delta(et, {ThreatModifierType.TO_HIT_DIE: (1, 4)})
                    max_threat_increase = max(threat_inc, max_threat_increase)
            total_threat_increase += max_threat_increase
        return total_threat_increase * SAVING_THROW_BONUS_MULTIPLIER * ROUND_HORIZON

    def calculate_threat_for_attack(self, combatant, attack, *args, **kwargs):
        """
        Threat estimation generated by the instantiated ability.
        """
        try:
            return attack.calculate_threat_delta({ThreatModifierType.TO_HIT_DIE: (1, 4)})
        except AttributeError:
            return 0


    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            coords_for_first = set(nf.get_free_coords_in_cartesian_range(
                battle_map.grid,
                battle_map.get_combatant_position(self.combatants[0]).get(),
                distances,
                self.factory.combatant.size.value,
                BlessFactory.range,
                self.factory.combatant.id))
            coords_for_second = set(nf.get_free_coords_in_cartesian_range(
                battle_map.grid,
                battle_map.get_combatant_position(self.combatants[1]).get(),
                distances,
                self.factory.combatant.size.value,
                BlessFactory.range,
                self.factory.combatant.id))
            coords_for_third = set(nf.get_free_coords_in_cartesian_range(
                battle_map.grid,
                battle_map.get_combatant_position(self.combatants[2]).get(),
                distances,
                self.factory.combatant.size.value,
                BlessFactory.range,
                self.factory.combatant.id))
            return list(coords_for_third.intersection(coords_for_first.intersection(coords_for_second)))  # Strangely no visibility required
        elif battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.combatants[0]) <= BlessFactory.range \
            and battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.combatants[1]) <= BlessFactory.range \
            and battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.combatants[2]) <= BlessFactory.range:
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
        return None
