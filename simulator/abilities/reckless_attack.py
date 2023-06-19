import math

from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.effect import EffectType
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from simulator.misc import reconcile_roll_types
from functools import reduce
from simulator.misc import avg_roll
from simulator.threat_utils import mean_dmg, calculate_threat_in_mod
from simulator.threat_interfaces import DirectThreat, DirectThreatFactory
from enum import Enum, auto

from simulator.utils.roll_types import RollType, ROLL_TYPE, ROLL_TYPE_CRIT, ThreatModifierType


class RecklessAttackFactory(DirectThreatFactory):

    class Type(Enum):
        MELEE = auto()
        RANGED = auto()

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=math.inf, on_hit=None, extra_dmg=[]):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.flags |= FactoryFlags.IS_HASTE_ELIGIBLE_ATTACK
        self.flags |= FactoryFlags.HAS_AMMO
        self.flags |= FactoryFlags.IS_MELEE
        self.flags |= FactoryFlags.USES_CALCULATE_THREAT_IN_MOD
        self.name = name
        self.combatant = combatant
        self.to_hit = to_hit
        self.dmg_dice = dmg_dice
        self.dmg_bonus = dmg_bonus
        self.dmg_type = dmg_type
        self.extra_dmg = extra_dmg  # List of tuples of type (dmg_dice, dmg_type)
        self.range = attack_range
        self.action_type = action_type  # ATTACK, BONUS_ATTACK, REACTION_ATTACK, HASTE_ATTACK...
        self.ammo = math.inf
        self.crit_range = crit_range
        self.on_hit = on_hit

        # Here I'm keeping them as class instance variables to be able to call them in calculate_threat_approx
        self.mod_range = 0
        self.mod_to_hit_die = '0d0'
        self.mod_to_hit_flat = 0
        self.mod_dmg_flat = 0
        self.mod_dmg_die = '0d0'
        self.mod_crit_range = 0


    def __str__(self):
        """
        Important for FSM building
        """
        return "RecklessAttackFactory" + self.name


    def get_eligible_targets(self, battle_map):
        return battle_map.get_enemies(self.combatant)

    def create_all(self, battle_map):
        targets = self.get_eligible_targets(battle_map)
        return [RecklessAttack(t, self) for t in targets]

    def calculate_threat_out_approx(self, combatant, battle_map, roll_type=RollType.ADVANTAGE):
        """
        Helper function which calculates the average potential threat_out over all potential targets including all possible mods
        """
        potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.speed + 1 + self.mod_range)
        if not potential_targets:
            return 0
        def mean_dmg_mod(acc, pt):
            to_hit_total = self.to_hit + self.mod_to_hit_flat + avg_roll(self.mod_to_hit_die)
            to_hit_total += ROLL_TYPE[roll_type][max(0, min(pt.ac - to_hit_total, 20))]
            total_crit = self.crit_range + self.mod_crit_range
            total_crit *= ROLL_TYPE_CRIT[roll_type]
            return acc + mean_dmg(to_hit_total, "+".join([self.dmg_dice, self.mod_dmg_die]) if self.mod_dmg_die else self.dmg_dice,
                                  self.dmg_bonus + self.mod_dmg_flat, pt.ac, total_crit, pt.is_resistant_to(self.dmg_type))

        dmg_acc = reduce(mean_dmg_mod, potential_targets)
        dmg_acc /= len(potential_targets)
        return dmg_acc

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        try:
            consider_dist = kwargs["consider_dist"]
        except KeyError:
            consider_dist = True
        dmg = 0
        if battle_map.get_hop_distance(self.combatant, target) <= self.range or not consider_dist:
            dmg = mean_dmg(self.to_hit + ROLL_TYPE[RollType.ADVANTAGE][max(0, min(target.ac - self.to_hit, 20))], self.dmg_dice, self.dmg_bonus, target.ac, self.crit_range * ROLL_TYPE_CRIT[RollType.ADVANTAGE], target.is_resistant_to(self.dmg_type))
        # even the single target calculation the combatant is still more vulnerable to all potential attackers
        incoming_threat_mod_acc = calculate_threat_in_mod(self.combatant, 6, battle_map, RollType.ADVANTAGE, FactoryFlags.IS_ATTACK_LIKE) / 2  # Heuristic
        return dmg - incoming_threat_mod_acc

    def calculate_threat_to_target_delta(self, battle_map, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications.
        This is useful calculating the potential reduction of threat_in caused by abilities of enemies, e.g. advantage on saving throw
        against fireball or bane on attack rolls etc.
        """
        try:
            consider_dist = kwargs["consider_dist"]
        except KeyError:
            consider_dist = True

        baseline = 0
        if battle_map.are_in_hop_range(self.combatant, target, self.range) or not consider_dist:
            baseline = mean_dmg(self.to_hit + ROLL_TYPE[RollType.ADVANTAGE][max(0, min(target.ac - self.to_hit, 20))], self.dmg_dice, self.dmg_bonus,
                                    target.ac, self.crit_range * ROLL_TYPE_CRIT[RollType.ADVANTAGE], target.is_resistant_to(self.dmg_type))
        mod_range = modifiers.get(ThreatModifierType.RANGE, 0)
        mod_dmg_flat = modifiers.get(ThreatModifierType.DMG_BONUS_FLAT, 0)
        # mod_dmg_die = modifiers.get(ThreatModifierType.DMG_BONUS_DIE, '0d0')
        mod_to_hit_flat = modifiers.get(ThreatModifierType.TO_HIT_FLAT, 0)
        mod_to_hit_die = modifiers.get(ThreatModifierType.TO_HIT_DIE, '0d0')
        mod_crit_range = modifiers.get(ThreatModifierType.CRIT_RANGE, 0)
        roll_type = reconcile_roll_types({RollType.ADVANTAGE, modifiers.get(ThreatModifierType.ROLL_TYPE, RollType.ADVANTAGE)})

        modified = baseline
        with battle_map.as_if_dist_mod_from_combatant(self.combatant, target, -mod_range):
            if battle_map.are_in_hop_range(self.combatant, target, self.range) or not consider_dist:
                to_hit_total = self.to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
                to_hit_total += ROLL_TYPE[roll_type][max(0, min(target.ac - to_hit_total, 20))]
                total_crit = self.crit_range + mod_crit_range
                total_crit *= ROLL_TYPE_CRIT[roll_type]
                modified = mean_dmg(to_hit_total, "+".join([self.dmg_dice, self.mod_dmg_die]), self.dmg_bonus + mod_dmg_flat, target.ac, total_crit, target.is_resistant_to(self.dmg_type))

        incoming_threat_mod_acc = calculate_threat_in_mod(self.combatant, 6, battle_map, RollType.ADVANTAGE, FactoryFlags.IS_ATTACK_LIKE) / 2  # Heuristic
        return modified - baseline - incoming_threat_mod_acc


class RecklessAttack(Actoid, DirectThreat, CombatantEffect, LimitedDurationEffect):

    def __init__(self, target_combatant, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_ATTACK_LIKE | ActoidFlags.IS_DIRECT_THREAT | ActoidFlags.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[factory.combatant])
        LimitedDurationEffect.__init__(self, turns=1)
        self.target_combatant = target_combatant
        self.factory = factory
        self.roll_type = RollType.ADVANTAGE

    def __str__(self):
        return f"Reckless Attack at {self.target_combatant}"

    def get_effect_type(self):
        return EffectType.RECKLESS_ATTACK

    def shorthand_str(self):
        return "Reckless Attack"

    def activate(self, battle_map):
        self.combatants[0].reckless_attack_active = True

    def deactivate(self, battle_map):
        self.combatants[0].reckless_attack_active = False

    def get_dmg_type(self):
        return self.factory.dmg_type

    # def clear_cache(self):
    #     self.calculate_threat.cache_clear()

    # @cache
    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        return self.factory.calculate_threat_to_target(battle_map, self.target_combatant, **kwargs)

    def calculate_threat_delta(self, battle_map, modifiers, *args, **kwargs):
        """
        The delta in threat when modifiers are applied on this ability.
        """
        return self.factory.calculate_threat_to_target_delta(battle_map, self.target_combatant, modifiers, *args, **kwargs)

    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        return battle_map.get_free_coords_in_hop_range(battle_map.get_combatant_position(self.target_combatant),
                                                       distances,
                                                       inflate_to_size=self.factory.combatant.size,
                                                       rng=self.factory.range,
                                                       combatant=self.factory.combatant)

    def is_current_coord_eligible(self, battle_map):
        return battle_map.are_in_hop_range(self.factory.combatant, self.target_combatant, self.factory.range)