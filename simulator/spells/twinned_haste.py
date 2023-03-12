from simulator.spells.spell import SpellStats
from simulator.effects.effect import Effect
from simulator.action_types import HasteAction
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.threat import mean_dmg, dmg_decrement_for_ac_flat
from simulator.threat_calculator import ThreatModifier, DirectThreatFactory
from functools import reduce
from simulator.misc import  ROUND_HORIZON, get_attacks
from simulator.spells.haste import HasteFactory

class TwinnedHasteFactory(DirectThreatFactory):
    def __init__(self, action_type, caster, effect_tracker):
        super().__init__(ActoidFlags.IS_SPELL)
        self.action_type = action_type # TWINNED_HASTE, QUICKENED_HASTE, HASTE
        self.caster = caster
        self.effect_tracker = effect_tracker

    def find_best_args(self, combatant, battle_map):
        return HasteFactory.get_allies_sorted_by_threat(combatant, battle_map)[0:1]

    def create_best(self, combatant, battle_map):
        return TwinnedHaste(self.find_best_args(combatant, battle_map), self)

    def create(self, targets):
        return TwinnedHaste(targets, self)

    def calculate_threat_mod_approx(self, battle_map, modified_stats, *args, **kwargs):
        return 0  # No need

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        For the given target ally it finds the attack with the highest mean dmg across all enemies withing range. It then adds
        estimated dmg prevention given by the AC bonus and by the saving throw advantage.
        """
        enemies = battle_map.get_enemies(target)
            # This doesn't take different attack ranges into account
        max_attack_dmg = 0
        attacks = get_attacks(target)
        for attack in attacks:
            potential_targets = battle_map.get_enemies_within_hop_distance(target, target.speed + attack.range + 1)
            if not potential_targets:
                continue
            dmg_acc = reduce(lambda acc, pt:acc + mean_dmg(attack.to_hit, attack.dmg_dice, attack.dmg_bonus, pt.ac, attack.crit_range, pt.is_resistant_to(attack.dmg_type)), potential_targets)
            dmg_acc /= len(potential_targets)
            max_attack_dmg = max(dmg_acc, max_attack_dmg)
        attack_dmg_decrement_acc = 0
        for enemy in enemies:
            enemy_attacks = get_attacks(enemy)
            if not enemy_attacks:
                continue
            attack_dmg_decrement_acc = reduce(lambda acc, at:acc + dmg_decrement_for_ac_flat(at.to_hit, at.dmg_dice, at.dmg_bonus, target.ac, 2, at.crit_range, target.is_resistant_to(at.dmg_type)), enemy_attacks)
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
            target.haste_actions = [HasteAction.HASTE_ATTACK, HasteAction.HASTE_DISENGAGE, HasteAction.HASTE_DASH, HasteAction.HASTE_HIDE]
            target.has_haste_action = True

    def deactivate(self):
        self.factory.caster.is_concentrating = False
        for target in self.targets:
            target.ac -= 2
            target.haste_actions.clear()
            self.factory.effect_tracker.create_post_haste_lethargy(target)
            target.has_haste_action = False

    def is_affecting(self, combatant):
        return combatant is self.target


    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        """
        For the given target ally it finds the attack with the highest mean dmg across all enemies withing range. It then adds
        estimated dmg prevention given by the AC bonus and by the saving throw advantage.
        """
        assert self.targets[0] is not None and self.targets[1] is not None, "One of the twinned haste targets is None"
        return self.factory.calculate_threat_to_target(battle_map, self.targets[0]) + self.factory.calculate_threat_to_target(battle_map, self.targets[1])

