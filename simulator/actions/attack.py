from abc import abstractmethod

from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import reduce, cache
from simulator.misc import percent_of_curr_hp, avg_roll
from simulator.threat import mean_dmg
from simulator.threat_calculator import DirectThreat, DirectThreatFactory
from enum import Enum, auto
import math
import logging

from simulator.utils.roll_modifiers import RollModifier, ROLL_MODIFIER_CRIT, ROLL_MODIFIER

logger = logging.getLogger("EncounTroll")

class AttackFactory(DirectThreatFactory):

    class Type(Enum):
        MELEE = auto()
        RANGED = auto()

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, max_num=1, on_hit=None, ammo=math.inf):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.flags |= FactoryFlags.IS_HASTE_ELIGIBLE_ATTACK
        self.flags |= FactoryFlags.HAS_AMMO
        self.name = name
        self.combatant = combatant
        self.to_hit = to_hit
        self.dmg_dice = dmg_dice
        self.dmg_bonus = dmg_bonus
        self.dmg_type = dmg_type
        self.range = attack_range
        self.short_range = attack_range // 4
        self.action_type = action_type  # MELEE_ATTACK, RANGED_ATTACK, BONUS_MELEE_ATTACK, BONUS_RANGED_ATTACK REACTION_ATTACK, HASTE_MELEE...
        self.crit_range = crit_range
        self.max_num = max_num  # the maximum number of an attack of this type, may differ from total num attacks
        self.on_hit = on_hit

        # Here I'm keeping them as class instance variables to be able to call them in calculate_threat_approx
        self.mod_range = 0
        self.mod_to_hit_die = '0d0'
        self.mod_to_hit_flat = 0
        self.mod_dmg_flat = 0
        self.mod_dmg_die = '0d0'
        self.mod_crit_range = 0

    def __str__(self):
        return self.name + " AttackFactory"

    def find_best_args(self, combatant, battle_map):
        # TODO Deprecated
        pass
        # if self.attack_type is AttackFactory.Type.MELEE:
        #     potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.movement + self.range + 1)
        # else:
        #     potential_targets = battle_map.get_enemies_within_radius(combatant, combatant.movement + self.range)
        # hp_percentages = [percent_of_curr_hp(pt, mean_dmg(self.to_hit, self.dmg_dice, self.dmg_bonus, pt.ac, self.crit_range)) for pt
        #                   in potential_targets]
        # potential_targets = list(zip(potential_targets, hp_percentages))
        # potential_targets.sort(key=lambda e: e[1], reverse=True)
        # return potential_targets[0][0] if potential_targets else None

    def get_eligible_targets(self, battle_map):
        return battle_map.get_enemies(self.combatant)

    def create_best(self, combatant, battle_map):
        best_args = self.find_best_args(combatant, battle_map)
        if best_args is None:
            return None
        return Attack(best_args, self)

    def create(self, target_combatant):
        return Attack(target_combatant, self)

    # def create_mock(self):
    #     return Attack(None, self)

    def calculate_threat_approx(self, combatant, battle_map, roll_modifier=RollModifier.STRAIGHT):
        """
        Helper function which calculates the average potential threat over all potential targets including all possible mods
        """
        potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.speed + 1 + self.mod_range)
        if not potential_targets:
            return 0
        def mean_dmg_mod(acc, pt):
            to_hit_total = self.to_hit + self.mod_to_hit_flat + avg_roll(self.mod_to_hit_die)
            to_hit_total += ROLL_MODIFIER[roll_modifier][max(0, min(pt.ac - to_hit_total, 20))]
            total_crit = self.crit_range + self.mod_crit_range
            total_crit *= ROLL_MODIFIER_CRIT[roll_modifier]
            return acc + mean_dmg(to_hit_total, "+".join([self.dmg_dice, self.mod_dmg_die]) if self.mod_dmg_die else self.dmg_dice,
                                  self.dmg_bonus + self.mod_dmg_flat, pt.ac, total_crit, pt.is_resistant_to(self.dmg_type))

        dmg_acc = reduce(mean_dmg_mod, potential_targets)
        dmg_acc /= len(potential_targets)
        return dmg_acc


    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        try:
            consider_dist = kwargs["consider_dist"]
        except KeyError:
            consider_dist = False

        try:
            roll_modifier = kwargs['roll_modifier']
        except KeyError:
            roll_modifier = RollModifier.STRAIGHT

        to_hit_total = self.to_hit
        to_hit_total = to_hit_total + ROLL_MODIFIER[roll_modifier][max(0, min(target.ac - to_hit_total, 20))]

        # TODO: Should I include roll modifiers here? There may be a use-case in the future
        if not consider_dist or battle_map.get_hop_distance(self.combatant, target) <= self.range:
            return mean_dmg(to_hit_total, self.dmg_dice, self.dmg_bonus, target.ac, self.crit_range, target.is_resistant_to(self.dmg_type))
        return 0

    def calculate_threat_to_target_mod(self, battle_map, target, modified_stats, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        baseline = mean_dmg(self.to_hit, self.dmg_dice, self.dmg_bonus, target.ac, self.crit_range, target.is_resistant_to(self.dmg_type))
        try:
            mod_dmg_flat = modified_stats['dmg_bonus_flat']
        except KeyError:
            mod_dmg_flat = 0
        try:
            mod_dmg_die = modified_stats['dmg_bonus_die']
        except KeyError:
            mod_dmg_die = '0d0'
        try:
            mod_to_hit_flat = modified_stats['to_hit_flat']
        except KeyError:
            mod_to_hit_flat = 0
        try:
            mod_to_hit_die = modified_stats['to_hit_die']
        except KeyError:
            mod_to_hit_die = '0d0'
        try:
            mod_crit_range = modified_stats['crit_range']
        except KeyError:
            mod_crit_range = 0
        try:
            target_ac = modified_stats['target_ac']
        except KeyError:
            target_ac = 0
        try:
            roll_modifier = modified_stats['roll_modifier']
        except KeyError:
            roll_modifier = RollModifier.STRAIGHT

        total_target_ac = target.ac + target_ac
        to_hit_total = self.to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
        try:
            to_hit_total += ROLL_MODIFIER[roll_modifier][max(0, min(total_target_ac - to_hit_total, 20))]
        except KeyError:  # Can happen for extreme differences between the AC and the to_hit
            pass  # The effect is negligible in that case
        total_crit = self.crit_range + mod_crit_range
        total_crit *= ROLL_MODIFIER_CRIT[roll_modifier]
        try:
            modified = mean_dmg(to_hit_total, "+".join([self.dmg_dice, mod_dmg_die]) if mod_dmg_die else self.dmg_dice, self.dmg_bonus + mod_dmg_flat, total_target_ac, total_crit, target.is_resistant_to(self.dmg_type))
        except:
            logger.error("Error in mean_dmg of calculate_threat_to_target_mod of AttackFactory")
            modified = baseline
        return modified - baseline


class Attack(Actoid, DirectThreat):

    def __init__(self, target_combatant, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_ATTACK_LIKE | ActoidFlags.IS_DIRECT_THREAT)
        self.target_combatant = target_combatant
        self.factory = factory
        self.roll_modifier = RollModifier.STRAIGHT

    def __str__(self):
        return self.factory.name + f" on {self.target_combatant}"

    def get_dmg_type(self):
        return self.factory.dmg_type

    def clear_cache(self):
        self.calculate_threat.cache_clear()

    @cache
    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        return self.factory.calculate_threat_to_target(battle_map, self.target_combatant, kwargs)

