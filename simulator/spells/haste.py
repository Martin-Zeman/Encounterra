from simulator.spells.spell import SpellStats
from simulator.effects.effect import Effect
from simulator.action_types import HasteAction
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.threat_calculator import ThreatModifier, ThreatModifierFactory
from functools import reduce
from simulator.misc import mean_dmg, ROUND_HORIZON, dmg_decrement_for_ac_flat

class HasteFactory(ThreatModifierFactory):
    def __init__(self, action_type, caster, effect_tracker):
        self.action_type = action_type # TWINNED_HASTE, QUICKENED_HASTE, HASTE
        self.caster = caster
        self.effect_tracker = effect_tracker


    @staticmethod
    def get_allies_sorted_by_threat(combatant, battle_map):
        allies = battle_map.get_allies_within_radius(combatant, Haste.spell_range.value)
        enemies = battle_map.get_enemies(combatant)
        threat_per_ally = 0
        ret = []
        for ally in allies:
            # This doesn't take different attack ranges into account
            max_attack_dmg = 0
            for attack in ally.attacks:
                potential_targets = battle_map.get_enemies_within_hop_distance(ally, ally.speed + attack.range + 1)
                dmg_acc = reduce(lambda acc, pt: acc + mean_dmg(attack.to_hit, attack.dmg_dice, attack.dmg_bonus, pt.ac, attack.crit_range, pt.is_resistant_to(attack.dmg_type)), potential_targets)
                dmg_acc /= len(potential_targets)
                max_attack_dmg = max(dmg_acc, max_attack_dmg)
            threat_per_ally += max_attack_dmg
            attack_dmg_decrement_acc = 0
            for enemy in enemies:
                attack_dmg_decrement_acc = reduce(lambda acc, at: acc + dmg_decrement_for_ac_flat(at.to_hit, at.dmg_dice, at.dmg_bonus, ally.ac, 2, at.crit_range,
                                          ally.is_resistant_to(at.dmg_type)), enemy.attacks)

                attack_dmg_decrement_acc /= len(enemy.attacks)
                # TODO include the ST-based abilities here
            threat_per_ally += attack_dmg_decrement_acc
            ret.append([ally, threat_per_ally])
        ret.sort(key=lambda e: e[1], reverse=True)
        return ret

    def find_best_args(self, combatant, battle_map):
        return HasteFactory.get_allies_sorted_by_threat(combatant, battle_map)[0]

    def create_best(self, combatant, battle_map):
        return Haste(self.find_best_args(combatant, battle_map), self)

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
        for attack in target.attacks:
            potential_targets = battle_map.get_enemies_within_hop_distance(target, target.speed + attack.range + 1)
            dmg_acc = reduce(lambda acc, pt:acc + mean_dmg(attack.to_hit, attack.dmg_dice, attack.dmg_bonus, pt.ac, attack.crit_range, pt.is_resistant_to(attack.dmg_type)), potential_targets)
            dmg_acc /= len(potential_targets)
            max_attack_dmg = max(dmg_acc, max_attack_dmg)
        attack_dmg_decrement_acc = 0
        for enemy in enemies:
            attack_dmg_decrement_acc = reduce(lambda acc, at:acc + dmg_decrement_for_ac_flat(at.to_hit, at.dmg_dice, at.dmg_bonus, target.ac, 2, at.crit_range, target.is_resistant_to(at.dmg_type)), enemy.attacks)
            attack_dmg_decrement_acc /= len(enemy.attacks)
            # TODO include the ST-based abilities here
        max_attack_dmg += attack_dmg_decrement_acc
        return max_attack_dmg * ROUND_HORIZON


class Haste(Actoid, Effect, ThreatModifier):

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
        self.target = target
        self.factory = factory

    def __str__(self):
        return "Haste"

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

    def is_affecting(self, combatant):
        return combatant is self.target


    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        """
        It's the same as the single target version of the factory
        """
        return self.factory.calculate_threat_to_target(self, battle_map, self.target)
