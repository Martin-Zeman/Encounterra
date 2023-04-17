from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.spells.spell import SpellStats
from simulator.effects.effect import Effect
from simulator.action_types import HasteAction, BonusActionOrdering, BonusAction
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.threat import mean_dmg, dmg_decrement_for_ac_flat
from simulator.threat_calculator import ThreatModifier, ThreatModifierFactory
from functools import reduce
from simulator.misc import ROUND_HORIZON, get_attacks, get_haste_eligile_attacks
import logging

logger = logging.getLogger(__name__)

class HasteFactory(ThreatModifierFactory):
    def __init__(self, action_type, caster, effect_tracker):
        super().__init__()
        self.bonus_action_ordering = BonusActionOrdering.GOES_BEFORE_ACTION  # In case this became a bonus action
        self.action_type = action_type  # TWINNED_HASTE, QUICKENED_HASTE, HASTE
        self.caster = caster
        self.effect_tracker = effect_tracker

    def __str__(self):
        """
        Important for FSM building
        """
        return "HasteFactory"

    def get_twinned_kwargs(self):
        return {'effect_tracker': self.effect_tracker, 'caster': self.caster}

    def get_quickened_kwargs(self):
        return {'effect_tracker': self.effect_tracker, 'caster': self.caster}


    @staticmethod
    def get_allies_sorted_by_threat(combatant, battle_map):
        allies = battle_map.get_allies_within_radius(combatant, Haste.spell_range.value)
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
            threat_per_ally += attack_dmg_decrement_acc
            ret.append([ally, threat_per_ally])
        ret.sort(key=lambda e: e[1], reverse=True)
        return ret

    def find_best_args(self, combatant, battle_map):
        # TODO Deprecated
        try:
            return HasteFactory.get_allies_sorted_by_threat(combatant, battle_map)[0][0]
        except IndexError:
            return None

    def create_best(self, combatant, battle_map):
        ally = self.find_best_args(combatant, battle_map)
        if ally is None:
            return None
        return Haste(ally, self)

    # def create_mock(self):
    #     return Haste(None, self)

    def get_eligible_targets(self, battle_map):
        ret = battle_map.get_allies(self.caster)
        ret.append(self.caster)
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
            attack_dmg_decrement_acc = reduce(lambda acc, at: acc + dmg_decrement_for_ac_flat(at.to_hit, at.dmg_dice, at.dmg_bonus, target.ac, 2, at.crit_range, target.is_resistant_to(at.dmg_type)), enemy_attacks, 0)
            attack_dmg_decrement_acc /= len(enemy_attacks)
            # TODO include the ST-based abilities here
        max_attack_dmg += attack_dmg_decrement_acc
        return max_attack_dmg * ROUND_HORIZON

    def calculate_threat_to_target_using_attack(self, battle_map, target, attack_factory, *args, **kwargs):
        enemies = battle_map.get_enemies(target)
            # This doesn't take different attack ranges into account
        max_attack_dmg = 0
        potential_targets = battle_map.get_enemies_within_hop_distance(target, target.speed + attack_factory.range + 1)
        if potential_targets:
            dmg_acc = reduce(lambda acc, pt: acc + mean_dmg(attack_factory.to_hit, attack_factory.dmg_dice, attack_factory.dmg_bonus, pt.ac, attack_factory.crit_range, pt.is_resistant_to(attack_factory.dmg_type)), potential_targets, 0)
            dmg_acc /= len(potential_targets)
            max_attack_dmg = max(dmg_acc, max_attack_dmg)
        attack_dmg_decrement_acc = 0
        assert len(enemies) > 0
        for enemy in enemies:
            enemy_attacks = get_attacks(enemy)
            if not enemy_attacks:
                continue
            attack_dmg_decrement_acc = reduce(lambda acc, at: acc + dmg_decrement_for_ac_flat(at.to_hit, at.dmg_dice, at.dmg_bonus, target.ac, 2, at.crit_range, target.is_resistant_to(at.dmg_type)), enemy_attacks, 0)
            attack_dmg_decrement_acc /= len(enemy_attacks)
            # TODO include the ST-based abilities here
        max_attack_dmg += attack_dmg_decrement_acc
        return max_attack_dmg * ROUND_HORIZON

class Haste(Actoid, LimitedDurationEffect, ThreatModifier):

    level = 3
    spell_range = SpellStats.Range.FEET_30
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.MINUTE
    concentration = True
    type = SpellStats.Type.BUFF
    dc = None
    dmg_type = None

    def __init__(self, target, factory):
        super().__init__(ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, turns=10)
        self.target = target
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_HASTE else "") + f"Haste on {self.target}"

    def activate(self):
        self.factory.caster.is_concentrating = True
        self.target.ac += 2
        # TODO rework this in the new way
        self.target.haste_actions = [HasteAction.HASTE_ATTACK, HasteAction.HASTE_DISENGAGE, HasteAction.HASTE_DASH, HasteAction.HASTE_HIDE]
        self.target.has_haste_action = True

    def deactivate(self):
        self.factory.caster.is_concentrating = False
        self.target.ac -= 2
        self.target.haste_actions.clear()
        self.factory.effect_tracker.create_post_haste_lethargy(self.target)
        self.target.has_haste_action = False

    def is_affecting(self, combatant, battle_map):
        return combatant is self.target


    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        """
        It's the same as the single target version of the factory
        """
        return self.factory.calculate_threat_to_target(battle_map, self.target)

    def get_eligible_coords(self, battle_map, shortest_paths):
        if self.target is self.factory.caster:
            return battle_map.get_all_accessible_coords(shortest_paths)
        else:
            return battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.target),
                                                                 inflate_to_size=self.factory.caster.size,
                                                                 rng=self.spell_range.value, combatant=self.target)
