from simulator.battle_map import Map, map_position_toggled_cache
from simulator.effects.effect import EffectType
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.spells.spell import SpellStats
from simulator.actions.action_types import BonusAction
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.threat_utils import mean_dmg
from simulator.threat_interfaces import ThreatModifierFactory, Threat
from functools import reduce, cache
from simulator.misc import ROUND_HORIZON, get_attacks, get_haste_eligile_attacks, Conditions, Visibility
import logging

from simulator.utils.roll_types import ThreatModifierType

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

    def __init__(self, action_type, caster):
        super().__init__()
        self.action_type = action_type  # TWINNED_HASTE, QUICKENED_HASTE, HASTE
        self.combatant = caster

    def __str__(self):
        """
        Important for FSM building
        """
        return "HasteFactory"

    def get_twinned_kwargs(self):
        return {'caster': self.combatant}

    def get_quickened_kwargs(self):
        return {'caster': self.combatant}


    def get_eligible_targets(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            return [self.combatant]
        ret = [a for a in Map.get().get_allies_within_radius(self.combatant, HasteFactory.range) if not a.is_affected_by(Conditions.SWALLOWED)]  # TODO do I want to keep this?
        ret.append(self.combatant)
        ret = [a for a in ret if len(a.haste_action_factories) == 0]
        return ret

    def create_all(self):
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
        attacks = get_haste_eligile_attacks(target)
        for attack in attacks:
            potential_targets = battle_map.get_enemies_within_hop_distance(target, target.speed + attack.range + 1)
            if not potential_targets:
                continue
            dmg_acc = reduce(lambda acc, pt: acc + mean_dmg(attack.to_hit, attack.dmg_dice, attack.dmg_bonus, pt.ac, attack.crit_range, pt.is_resistant_to(attack.dmg_type)), potential_targets, 0)
            dmg_acc /= len(potential_targets)
            max_attack_dmg = max(dmg_acc, max_attack_dmg)
        # logger.warning(f"MY DEBUG {self} calculate_threat_to_target max_attack_dmg = {max_attack_dmg}")
        attack_dmg_decrement_acc = 0
        assert len(enemies) > 0
        for enemy in enemies:
            enemy_attacks = get_attacks(enemy)
            if not enemy_attacks:
                continue
            # attack_dmg_decrement_acc = reduce(lambda acc, at: acc + dmg_decrement_for_ac_flat(at.to_hit, at.dmg_dice, at.dmg_bonus, target.ac, 2, at.crit_range, target.is_resistant_to(at.dmg_type)), enemy_attacks, 0)
            attack_dmg_decrement_acc = reduce(lambda acc, at: acc + at.calculate_threat_to_target_delta(target, {ThreatModifierType.TARGET_AC: 2}), enemy_attacks, 0)
            attack_dmg_decrement_acc /= len(enemy_attacks)
            # TODO include the ST-based abilities here
        max_attack_dmg -= attack_dmg_decrement_acc  # Take care to subtract this, because the decrement is non-positive
        # logger.warning(f"MY DEBUG {self} calculate_threat_to_target attack_dmg_decrement_acc = {attack_dmg_decrement_acc}")
        # logger.warning(f"MY DEBUG {self} calculate_threat_to_target total = {max_attack_dmg * ROUND_HORIZON}")
        return max_attack_dmg * ROUND_HORIZON

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        return max([self.calculate_threat_to_target(t) for t in targets])

class Haste(Actoid, LimitedDurationEffect, Threat):

    def __init__(self, target, factory):
        super().__init__(ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, turns=10)
        self.target = target
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_HASTE else "") + f"Haste on {self.target}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_HASTE else "") + "Haste"

    def get_effect_type(self):
        return EffectType.HASTE

    def activate(self):
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
        effect_tracker.create_post_haste_lethargy(self.target)
        self.target.has_haste_action = False  # TODO Remove this

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

    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        swallower = self.factory.combatant.get_swallower()
        if swallower:
            if self.target is self.factory.combatant:
                set(curr_coord)
            return None  # Not possible while blinded
        if self.target is self.factory.combatant:
            return battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)
        elif self.factory.combatant.movement > 0 and not self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            free_coords_in_range = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.target),
                                                                 distances,
                                                                 inflate_to_size=self.factory.combatant.size,
                                                                 rng=HasteFactory.range)
            return {coord for coord in free_coords_in_range if battle_map.visibility_dict_for_all_coords[coord][self.target] is not Visibility.NONE}
        elif battle_map.get_cartesian_distance(self.factory.combatant, self.target) <= HasteFactory.range and \
                battle_map.visibility_dict_for_all_coords[curr_coord][self.target] is not Visibility.NONE:
            return set([curr_coord])
        return None
