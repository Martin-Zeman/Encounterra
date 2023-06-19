from simulator.combatant_coords import CombatantCoords
from simulator.effects.effect import EffectType
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.spells.spell import SpellStats
from simulator.actions.action_types import BonusAction
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.threat_utils import mean_dmg, dmg_decrement_for_ac_flat
from simulator.threat_interfaces import ThreatModifier, ThreatModifierFactory
from functools import reduce, cache
from simulator.misc import ROUND_HORIZON, get_attacks, get_haste_eligile_attacks
import logging

from simulator.utils.roll_types import ThreatModifierType

logger = logging.getLogger("EncounTroll")

class HasteFactory(ThreatModifierFactory):
    level = 3
    range = SpellStats.Range.FEET_30.value
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.MINUTE
    concentration = True
    type = SpellStats.Type.BUFF
    dc = None
    dmg_type = None

    def __init__(self, action_type, caster, effect_tracker):
        super().__init__()
        self.action_type = action_type  # TWINNED_HASTE, QUICKENED_HASTE, HASTE
        self.combatant = caster
        self.effect_tracker = effect_tracker

    def __str__(self):
        """
        Important for FSM building
        """
        return "HasteFactory"

    def get_twinned_kwargs(self):
        return {'effect_tracker': self.effect_tracker, 'caster': self.combatant}

    def get_quickened_kwargs(self):
        return {'effect_tracker': self.effect_tracker, 'caster': self.combatant}


    @staticmethod
    def get_allies_sorted_by_threat(combatant, battle_map):
        allies = battle_map.get_allies_within_radius(combatant, HasteFactory.range)
        allies.append(combatant)
        enemies = battle_map.get_enemies(combatant)
        threat_per_ally = 0
        ret = []
        for ally in allies:
            # This doesn't take different attack ranges into account
            max_attack_dmg = 0
            attacks = get_haste_eligile_attacks(ally)
            for attack in attacks:
                potential_targets = battle_map.get_enemies_within_hop_distance(ally, ally.speed + attack.range + 1)
                if not potential_targets:
                    continue
                dmg_acc = reduce(lambda acc, pt: acc + mean_dmg(attack.to_hit, attack.dmg_dice, attack.dmg_bonus, pt.ac, attack.crit_range, pt.is_resistant_to(attack.dmg_type)), potential_targets, 0)
                dmg_acc /= len(potential_targets)
                max_attack_dmg = max(dmg_acc, max_attack_dmg)
            threat_per_ally += max_attack_dmg
            attack_dmg_decrement_acc = 0
            for enemy in enemies:
                enemy_attacks = get_attacks(enemy)
                if not enemy_attacks:
                    continue
                attack_dmg_decrement_acc = reduce(lambda acc, at: acc + dmg_decrement_for_ac_flat(at.to_hit, at.dmg_dice, at.dmg_bonus, ally.ac, 2, at.crit_range,
                                          ally.is_resistant_to(at.dmg_type)), enemy_attacks, 0)

                attack_dmg_decrement_acc /= len(enemy_attacks)
                # TODO include the ST-based abilities here
            threat_per_ally -= attack_dmg_decrement_acc  # Take care to subtract this, because the decrement is non-positive
            ret.append([ally, threat_per_ally])
        ret.sort(key=lambda e: e[1], reverse=True)
        return ret

    def get_eligible_targets(self, battle_map):
        ret = battle_map.get_allies_within_radius(self.combatant, HasteFactory.range)
        ret.append(self.combatant)
        ret = [a for a in ret if len(a.haste_action_factories) == 0]
        return ret

    def create_all(self, battle_map):
        targets = self.get_eligible_targets(battle_map)
        return [Haste(t, self) for t in targets]

    def create(self, target_combatant):
        return Haste(target_combatant, self)

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        For the given target ally it finds the attack with the highest mean dmg across all enemies withing range. It then adds
        estimated dmg prevention given by the AC bonus and by the saving throw advantage.
        """
        if target.haste_action_factories:  # No benefit if already hasted
            return 0
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
        attack_dmg_decrement_acc = 0
        assert len(enemies) > 0
        for enemy in enemies:
            enemy_attacks = get_attacks(enemy)
            if not enemy_attacks:
                continue
            # attack_dmg_decrement_acc = reduce(lambda acc, at: acc + dmg_decrement_for_ac_flat(at.to_hit, at.dmg_dice, at.dmg_bonus, target.ac, 2, at.crit_range, target.is_resistant_to(at.dmg_type)), enemy_attacks, 0)
            attack_dmg_decrement_acc = reduce(lambda acc, at: acc + at.calculate_threat_to_target_delta(battle_map, target, {ThreatModifierType.TARGET_AC: 2}), enemy_attacks, 0)
            attack_dmg_decrement_acc /= len(enemy_attacks)
            # TODO include the ST-based abilities here
        max_attack_dmg -= attack_dmg_decrement_acc  # Take care to subtract this, because the decrement is non-positive
        return max_attack_dmg * ROUND_HORIZON

class Haste(Actoid, LimitedDurationEffect, ThreatModifier):

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

    def activate(self, battle_map):
        self.factory.combatant.is_concentrating = True
        self.target.ac += 2
        self.target.add_hasted_factories()
        self.target.has_haste_action = True  # TODO Remove this

    def deactivate(self, battle_map):
        self.factory.combatant.is_concentrating = False
        self.target.ac -= 2
        self.target.haste_action_factories.clear()
        self.factory.effect_tracker.create_post_haste_lethargy(self.target)
        self.target.has_haste_action = False  # TODO Remove this

    def is_affecting(self, combatant, battle_map):
        return combatant is self.target


    def clear_cache(self):
        self.calculate_threat.cache_clear()

    @cache
    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        """
        It's the same as the single target version of the factory
        """
        return self.factory.calculate_threat_to_target(battle_map, self.target)

    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        if self.target is self.factory.combatant:
            return battle_map.get_all_accessible_coords(shortest_paths)
        else:
            return battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.target),
                                                                 distances,
                                                                 inflate_to_size=self.factory.combatant.size,
                                                                 rng=HasteFactory.range)

    def is_current_coord_eligible(self, battle_map):
        return battle_map.get_cartesian_distance(self.factory.combatant, self.target) <= HasteFactory.range
