from itertools import combinations
from simulator.spells.spell import SpellStats
from simulator.effects.effect import Effect
from simulator.action_types import HasteAction
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.threat import mean_dmg, dmg_decrement_for_ac_flat
from simulator.threat_calculator import ThreatModifier, ThreatModifierFactory
from functools import reduce
from simulator.misc import ROUND_HORIZON, get_attacks, get_haste_eligile_attacks
from simulator.spells.haste import HasteFactory

class TwinnedHasteFactory(ThreatModifierFactory):
    def __init__(self, action_type, caster, effect_tracker):
        super().__init__()
        self.action_type = action_type # TWINNED_HASTE, QUICKENED_HASTE, HASTE
        self.caster = caster
        self.effect_tracker = effect_tracker

    def __str__(self):
        """
        Important for FSM building
        """
        return "TwinnedHasteFactory"

    def find_best_args(self, combatant, battle_map):
        # TODO Deprecated
        ret1 = None
        ret2 = None
        try:
            ret = HasteFactory.get_allies_sorted_by_threat(combatant, battle_map)
            ret1 = ret[0][0]
            ret2 = ret[1][0]
        except IndexError:
            pass
        return [ret1, ret2]

    def create_best(self, combatant, battle_map):
        return TwinnedHaste(self.find_best_args(combatant, battle_map), self)

    # def create_mock(self):
    #     return TwinnedHaste(None, self)

    def get_eligible_targets(self, battle_map):
        ret = battle_map.get_allies(self.caster)
        ret.append(self.caster)
        ret = combinations(ret, 2)
        return ret

    def create_all(self, battle_map):
        targets = self.get_eligible_targets(battle_map)
        return [TwinnedHaste(t, self) for t in targets]

    def create(self, targets):
        return TwinnedHaste(targets, self)

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

class TwinnedHaste(Actoid, Effect, ThreatModifier):

    level = 3
    spell_range = SpellStats.Range.FEET_30
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.MINUTE
    concentration = True
    type = SpellStats.Type.BUFF
    dc = None
    dmg_type = None

    def __init__(self, targets, factory):
        super().__init__(ActoidFlags.IS_SPELL)
        self.targets = targets
        self.factory = factory

    def __str__(self):
        return f"Twinned Haste on {self.targets[0]} and {self.targets[1]}"

    def activate(self):
        self.factory.caster.is_concentrating = True
        for target in self.targets:
            target.ac += 2
            target.haste_actions = [HasteAction.HASTE_MELEE_ATTACK, HasteAction.HASTE_RANGED_ATTACK, HasteAction.HASTE_DISENGAGE, HasteAction.HASTE_DASH, HasteAction.HASTE_HIDE]
            target.has_haste_action = True

    def deactivate(self):
        self.factory.caster.is_concentrating = False
        for target in self.targets:
            target.ac -= 2
            target.haste_actions.clear()
            self.factory.effect_tracker.create_post_haste_lethargy(target)
            target.has_haste_action = False

    def is_affecting(self, combatant, battle_map):
        return combatant is self.target


    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        """
        For the given target ally it finds the attack with the highest mean dmg across all enemies withing range. It then adds
        estimated dmg prevention given by the AC bonus and by the saving throw advantage.
        """
        assert not(self.targets[0] is None and self.targets[1] is None), "Both of the twinned haste targets are None. This should not happen, there should always be at least self as target"
        target1_threat = self.factory.calculate_threat_to_target(battle_map, self.targets[0]) if self.targets[0] is not None else 0
        target2_threat = self.factory.calculate_threat_to_target(battle_map, self.targets[1]) if self.targets[1] is not None else 0
        return target1_threat + target2_threat

    def get_eligible_coords(self, battle_map):
        target_combatant_coords = battle_map.get_combatant_coordinates[self.targets[0]]
        coords_for_fist = battle_map.get_free_coords_in_cartesian_range(target_combatant_coords, inflate_to_size=self.factory.caster.size, rng=self.spell_range.value)
        target_combatant_coords = battle_map.get_combatant_coordinates[self.targets[1]]
        coords_for_second = battle_map.get_free_coords_in_cartesian_range(target_combatant_coords, inflate_to_size=self.factory.caster.size, rng=self.spell_range.value)
        return coords_for_fist.intersection(coords_for_second)
