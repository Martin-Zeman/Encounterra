from cachetools import cached
from cachetools.keys import hashkey

from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key
from ..effects.effect import EffectType
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..spells.spell import SpellStats
from ..actions.action_types import BonusAction
from ..actions.actoid import Actoid, ActoidFlags
from ..threat_utils import mean_dmg
from ..threat_interfaces import Threat
from ..factory_interfaces import ThreatModifierFactory
from functools import reduce, cache
from ..misc import ROUND_HORIZON, get_attack_factories, get_haste_eligible_attacks, Visibility
from ..conditions import Conditions, is_affected_by_any, is_affected_by, get_swallower
from ..utils.roll_types import ThreatModifierType
import logging


logger = logging.getLogger("Encounterra")


class HasteFactory(ThreatModifierFactory):
    level = 3
    range = SpellStats.Range.FEET_30.value
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.MINUTE
    concentration = True
    type = SpellStats.Type.BUFF
    dc = None
    dmg_type = None

    def __init__(self, action_type, caster, resource):
        super().__init__()
        self.action_type = action_type  # TWINNED_HASTE, QUICKENED_HASTE, HASTE
        self.combatant = caster
        self.resource = resource

    def __str__(self):
        """
        Important for FSM building
        """
        return "HasteFactory"

    def get_ability_name(self):
        return "Haste"

    def get_twinned_kwargs(self):
        return {'caster': self.combatant, 'resource': self.resource}

    def get_quickened_kwargs(self):
        return {'caster': self.combatant, 'resource': self.resource}

    def get_eligible_targets(self):
        swallower = get_swallower(self.combatant)
        if swallower:
            return [self.combatant]
        ret = Map.get().get_non_swallowed_allies_within_radius(self.combatant, HasteFactory.range)
        ret.append(self.combatant)
        ret = [a for a in ret if len(a.haste_action_factories) == 0]
        return ret

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [Haste(t, self) for t in targets]

    def create(self, target):
        return Haste(target, self)

    def calculate_threat_to_target(self, target, **kwargs):
        """
        For the given target ally it finds the attack with the highest mean dmg across all enemies withing range. It then adds
        estimated dmg prevention given by the AC bonus and by the saving throw advantage.
        """
        if target.haste_action_factories:  # No benefit if already hasted
            return 0
        battle_map = Map.get()
        enemies = battle_map.get_enemies(target)
            # This doesn't take different attack ranges into account
        max_attack_dmg = 0
        attacks = get_haste_eligible_attacks(target)
        for attack in attacks:
            potential_targets = battle_map.get_non_swallowed_enemies_within_hop_distance(target, target.speed + attack.range + 1)
            if not potential_targets:
                continue
            dmg_acc = reduce(lambda acc, pt: acc + mean_dmg(attack.to_hit, attack.dmg_dice, attack.dmg_bonus, pt.ac, attack.crit_range, pt.is_resistant_to(attack.dmg_type)), potential_targets, 0)
            dmg_acc /= len(potential_targets)
            max_attack_dmg = max(dmg_acc, max_attack_dmg)
        attack_dmg_decrement_acc = 0
        assert len(enemies) > 0
        for enemy in enemies:
            enemy_attacks = get_attack_factories(enemy)
            if not enemy_attacks:
                continue
            attack_dmg_decrement_acc = reduce(lambda acc, at: acc + at.calculate_threat_to_target_delta(target, {ThreatModifierType.TARGET_AC: 2}), enemy_attacks, 0)
            attack_dmg_decrement_acc /= len(enemy_attacks)
            # TODO include the ST-based abilities here
        max_attack_dmg -= attack_dmg_decrement_acc  # Take care to subtract this, because the decrement is non-positive
        return max_attack_dmg * ROUND_HORIZON

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        if not targets:
            return 0
        return max([self.calculate_threat_to_target(t) for t in targets])


class Haste(Actoid, LimitedDurationEffect, Threat):

    def __init__(self, target, factory):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, factory.combatant, turns=10)
        self.target = target
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_HASTE else "") + f"Haste on {self.target}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_HASTE else "") + "Haste"

    def get_effect_type(self):
        return EffectType.HASTE

    def activate(self, **kwargs):
        Map.get().effect_tracker.add(self)
        self.factory.combatant.concentration_effect = self
        self.target.ac += 2
        self.target.add_hasted_factories()
        self.target.has_haste_action = True  # TODO Remove this

    def deactivate(self):
        effect_tracker = Map.get().effect_tracker
        self.factory.combatant.break_concentration()
        self.target.ac -= 2
        self.target.haste_action_factories.clear()
        effect_tracker.create_post_haste_lethargy(self.factory.combatant, self.target)
        self.target.has_haste_action = False  # TODO Remove this

    def deactivate_for_combatant(self, combatant):
        assert False

    def is_affecting(self, combatant):
        return combatant is self.target

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        """
        It's the same as the single target version of the factory
        """
        return self.factory.calculate_threat_to_target(self.target)

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        #self.get_eligible_coords.cache_clear()

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        swallower = get_swallower(self.factory.combatant)
        if swallower:
            if self.target is self.factory.combatant:
                return [curr_coord]
            return None  # Not possible while blinded
        if self.target is self.factory.combatant:
            return battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)
        elif not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            free_coords_in_range = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.target),
                                                                 distances,
                                                                 inflate_to_dist=self.factory.combatant.size.value,
                                                                 rng=HasteFactory.range)
            return [coord for coord in free_coords_in_range if battle_map.visibility_dict_for_all_coords[coord][self.target] is not Visibility.NONE]
        elif battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.target) <= HasteFactory.range and \
                battle_map.visibility_dict_for_all_coords[curr_coord][self.target] is not Visibility.NONE:
            return [curr_coord]
        return None
