from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from simulator.misc import mean_dmg
from functools import reduce
from simulator.misc import percent_of_curr_hp, avg_roll, RollModifier, ROLL_MODIFIER, ROLL_MODIFIER_CRIT
from simulator.threat_calculator import DirectThreat, DirectThreatFactory
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)

class AttackFactory(DirectThreatFactory):

    class Type(Enum):
        MELEE = auto()
        RANGED = auto()

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, attack_type, crit_range=[20], max_num=1):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.name = name
        self.combatant = combatant
        self.to_hit = to_hit
        self.dmg_dice = dmg_dice
        self.dmg_bonus = dmg_bonus
        self.dmg_type = dmg_type
        self.range = attack_range
        self.short_range = attack_range // 4
        self.action_type = action_type  # ATTACK, BONUS_ATTACK, REACTION_ATTACK, HASTE_ATTACK...
        self.attack_type = attack_type  # MELEE or RANGED
        self.crit_range = crit_range
        self.max_num = max_num  # the maximum number of an attack of this type, may differ from total num attacks

        # Here I'm keeping them as class instance variables to be able to call them in calculate_threat_approx
        self.mod_range = 0
        self.mod_to_hit_die = ''
        self.mod_to_hit_flat = 0
        self.mod_dmg_flat = 0
        self.mod_dmg_die = ''
        self.mod_crit_range = 0

    def __str__(self):
        return self.name + " AttackFactory"

    def find_best_args(self, combatant, battle_map):
        # TODO consider prioritizing the ones you have a change to finish off
        if self.attack_type is AttackFactory.Type.MELEE:
            potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.movement + self.range + 1)
        else:
            potential_targets = battle_map.get_enemies_within_radius(combatant, combatant.movement + self.range)
        hp_percentages = [percent_of_curr_hp(pt, mean_dmg(self.to_hit, self.dmg_dice, self.dmg_bonus, pt.ac, len(self.crit_range))) for pt
                          in potential_targets]
        potential_targets = list(zip(potential_targets, hp_percentages))
        potential_targets.sort(key=lambda e: e[1], reverse=True)
        return potential_targets[0][0] if potential_targets else None

    def create_best(self, combatant, battle_map):
        best_args = self.find_best_args(combatant, battle_map)
        if best_args is None:
            return None
        return Attack(best_args, self)

    def create(self, target_combatant):
        return Attack(target_combatant, self)

    def calculate_threat_approx(self, combatant, battle_map, roll_modifier=RollModifier.STRAIGHT):
        """
        Helper function which calculates the average potential threat over all potential targets including all possible mods
        """
        potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.speed + 1 + self.mod_range)
        num = min(self.max_num, self.combatant.curr_num_attacks)
        def mean_dmg_mod(acc, pt):
            to_hit_total = self.to_hit + self.mod_to_hit_flat + avg_roll(self.mod_to_hit_die)
            to_hit_total += ROLL_MODIFIER[roll_modifier][pt.ac - to_hit_total]
            total_crit = len(self.crit_range) + self.mod_crit_range
            total_crit *= ROLL_MODIFIER_CRIT[roll_modifier]
            return acc + num * mean_dmg(to_hit_total, "+".join([self.dmg_dice, self.mod_dmg_die]) if self.mod_dmg_die else self.dmg_dice,
                                  self.dmg_bonus + self.mod_dmg_flat, pt.ac, total_crit, pt.is_resistant_to(self.dmg_type))
        dmg_acc = reduce(mean_dmg_mod)
        dmg_acc /= len(potential_targets)
        return dmg_acc

    def calculate_threat_approx_mod(self, battle_map, modified_stats, *args, **kwargs):
        """
        Goes over all the modified stats and accumulates the threat delta for all of them
        """
        baseline = self.calculate_threat_approx(self.combatant, battle_map)
        try:
            self.mod_range = modified_stats['range']
        except KeyError:
            self.mod_range = 0
        try:
            self.mod_dmg_flat = modified_stats['dmg_bonus_flat']
        except KeyError:
            self.mod_dmg_flat = 0
        try:
            self.mod_dmg_die = modified_stats['dmg_bonus_die']
        except KeyError:
            self.mod_dmg_die = ''
        try:
            self.mod_to_hit_flat = modified_stats['to_hit_flat']
        except KeyError:
            self.mod_to_hit_flat = 0
        try:
            self.mod_to_hit_die = modified_stats['to_hit_die']
        except KeyError:
            self.mod_to_hit_die = ''
        try:
            self.mod_crit_range = modified_stats['crit_range']
        except KeyError:
            self.mod_crit_range = 0
        try:
            roll_modifier = modified_stats['roll_modifier']
        except KeyError:
            roll_modifier = RollModifier.STRAIGHT

        modified = baseline
        try:
            modified = self.calculate_threat_approx(self.combatant, battle_map, roll_modifier)
        except:
            pass # just make sure the original stats are restored

        self.mod_range = 0
        self.mod_to_hit_die = ''
        self.mod_to_hit_flat = 0
        self.mod_dmg_flat = 0
        self.mod_dmg_die = ''
        self.mod_crit_range = 0
        return modified - baseline

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        num = min(self.max_num, self.combatant.curr_num_attacks)
        # TODO: Should I include roll modifiers here? There may be a use-case in the future
        return num * mean_dmg(self.to_hit, self.dmg_dice, self.dmg_bonus, target.ac, len(self.crit_range), target.is_resistant_to(self.dmg_type))

    def calculate_threat_to_target_mod(self, battle_map, target, modified_stats, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        num = min(self.max_num, self.combatant.curr_num_attacks)
        baseline = num * mean_dmg(self.to_hit, self.dmg_dice, self.dmg_bonus, target.ac, len(self.crit_range), target.is_resistant_to(self.dmg_type))
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
            roll_modifier = modified_stats['roll_modifier']
        except KeyError:
            roll_modifier = RollModifier.STRAIGHT

        to_hit_total = self.to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
        to_hit_total += ROLL_MODIFIER[roll_modifier][target.ac - to_hit_total]
        total_crit = len(self.crit_range) + mod_crit_range
        total_crit *= ROLL_MODIFIER_CRIT[roll_modifier]
        try:
            modified = num * mean_dmg(to_hit_total, "+".join([self.dmg_dice, mod_dmg_die]) if mod_dmg_die else self.dmg_dice, self.dmg_bonus + mod_dmg_flat, target.ac, total_crit, target.is_resistant_to(self.dmg_type))
        except:
            logger.error("Error in mean_dmg of calculate_threat_to_target_mod of AttackFactory")
            modified = baseline
        return modified - baseline


class Attack(Actoid, DirectThreat):

    def __init__(self, target_combatant, factory):
        Actoid.__init__(self, actoid_type=ActoidFlags.IS_ATTACK_LIKE | ActoidFlags.IS_DIRECT_THREAT)
        self.target_combatant = target_combatant
        self.factory = factory
        self.roll_modifier = RollModifier.STRAIGHT

    def __str__(self):
        return self.factory.name

    def get_dmg_type(self):
        return self.factory.dmg_type

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        return self.factory.calculate_threat_to_target(battle_map, self.target_combatant)
