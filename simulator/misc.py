import sys
from enum import Enum, Flag, auto
import random
import re
import math
import numpy as np
from scipy.stats import randint
from functools import reduce, partial, cache
from functools import reduce


ROUND_HORIZON = 3

class SavingThrow(Enum):
    STR = 1
    DEX = 2
    CON = 3
    INT = 4
    WIS = 5
    CHA = 6


class DamageType(Enum):
    Bludgeoning = 0
    Slashing = 1
    Piercing = 2
    Fire = 3
    Cold = 4
    Poison = 5
    Acid = 6
    Lightning = 7
    Radiant = 8
    Necrotic = 9
    Force = 10
    Psychic = 11
    Thunder = 12

    def __str__(self):
        return self.name


class Conditions(Flag):
    NONE = auto()
    BLINDED = auto()
    CHARMED = auto()
    DEAFENED = auto()
    FRIGHTENED = auto()
    GRAPPLED = auto()
    INCAPACITATED = auto()
    INVISIBLE = auto()
    PARALYZED = auto()
    PETRIFIED = auto()
    POISONED = auto()
    PRONE = auto()
    RESTRAINED = auto()
    STUNNED = auto()
    UNCONSCIOUS = auto()


class RollModifier(Flag):
    STRAIGHT = auto()
    ADVANTAGE = auto()
    DISADVANTAGE = auto()


class Size(Enum):
    TINY = 0
    SMALL = 1
    MEDIUM = 2
    LARGE = 3
    HUGE = 4
    GARGANTUAN = 5


class Side(Enum):
    ENEMY = auto()
    ALLY = auto()


class DistanceMetric(Enum):
    HOP = auto()
    CARTESIAN = auto()


class PlacementScenario(Enum):
    TWO_HALVES = 1
    TOTALLY_RANDOM = 2
    # SURROUNDED = 3


SIGN = {"+": 1, "-": -1}
# ADVANTAGE = {
#     20: 0.098,
#     19: 0.191,
#     18: 0.278,
#     17: 0.359,
#     16: 0.437,
#     15: 0.510,
#     14: 0.576,
#     13: 0.639,
#     12: 0.698,
#     11: 0.751,
#     10: 0.798,
#     9: 0.840,
#     8: 0.877,
#     7: 0.910,
#     6: 0.938,
#     5: 0.960,
#     4: 0.978,
#     3: 0.990,
#     2: 0.998,
#     1: 1.000
# }
#
# DISADVANTAGE = {
#     20: 0.002,
#     19: 0.010,
#     18: 0.022,
#     17: 0.039,
#     16: 0.062,
#     15: 0.089,
#     14: 0.123,
#     13: 0.160,
#     12: 0.202,
#     11: 0.249,
#     10: 0.303,
#     9: 0.361,
#     8: 0.424,
#     7: 0.492,
#     6: 0.564,
#     5: 0.640,
#     4: 0.723,
#     3: 0.811,
#     2: 0.903,
#     1: 1.000,
# }
#
# STRAIGHT = {
#     20: 0.050,
#     19: 0.100,
#     18: 0.150,
#     17: 0.200,
#     16: 0.250,
#     15: 0.300,
#     14: 0.350,
#     13: 0.400,
#     12: 0.450,
#     11: 0.500,
#     10: 0.550,
#     9: 0.600,
#     8: 0.650,
#     7: 0.700,
#     6: 0.750,
#     5: 0.800,
#     4: 0.850,
#     3: 0.900,
#     2: 0.950,
#     1: 1.000
# }

# @cache
# def find_advantage_eq_bonus(min_needed_roll):
#     """
#     Finds the equivalent bonus for a roll with advantage
#     """
#     assert min_needed_roll < 21, "An impossible needed roll"
#     straight = STRAIGHT[min_needed_roll]
#     min_diff = abs(ADVANTAGE[min_needed_roll] - straight)
#     min_i = min_needed_roll
#     for i in range(min_needed_roll + 1, 21):
#         diff = abs(ADVANTAGE[i] - straight)
#         if diff < min_diff:
#             min_diff = diff
#             min_i = i
#         else:
#             break
#     return min_i - min_needed_roll

# The Advantage equivalent bonus for a needed roll of at least equal to the key
ADVANTAGE_BONUS = {
    1: 0, 2: 3, 3: 4, 4: 5, 5: 5, 6: 5, 7: 5, 8: 5, 9: 5, 10: 4, 11: 4, 12: 4, 13: 3, 14: 3, 15: 3, 16: 2, 17: 2, 18: 1, 19: 1, 20: 0
}

# The Disadvantage equivalent penalty for a needed roll of at least equal to the key
DISADVANTAGE_PENALTY = {
    {1: 0, 2: 0, 3: -1, 4: -1, 5: -2, 6: -2, 7: -3, 8: -3, 9: -3, 10: -4, 11: -4, 12: -4, 13: -5, 14: -5, 15: -5, 16: -5, 17: -5, 18: -5,
     19: -4, 20: -3}
}

# @cache
# def find_advantage_eq_bonus(min_needed_roll):
#     """
#     Finds the equivalent bonus for a roll with advantage
#     """
#     assert min_needed_roll < 21, "An impossible needed roll"
#     straight = STRAIGHT[min_needed_roll]
#     min_diff = abs(ADVANTAGE[min_needed_roll] - straight)
#     min_i = min_needed_roll
#     for i in range(min_needed_roll + 1, 21):
#         diff = abs(ADVANTAGE[i] - straight)
#         if diff < min_diff:
#             min_diff = diff
#             min_i = i
#         else:
#             break
#     return min_i - min_needed_roll
#
#
# @cache
# def find_disadvantage_eq_penalty(min_needed_roll):
#     """
#     Finds the equivalent penalty for a roll with disadvantage
#     """
#     assert min_needed_roll < 21, "An impossible needed roll"
#     straight = STRAIGHT[min_needed_roll]
#     min_diff = abs(straight - DISADVANTAGE[min_needed_roll])
#     min_i = min_needed_roll
#     for i in range(min_needed_roll - 1, 1, -1):
#         diff = abs(straight - DISADVANTAGE[i])
#         if diff < min_diff:
#             min_diff = diff
#             min_i = i
#         else:
#             break
#     return min_i - min_needed_roll


@cache
def parse_dmg_dice(dice_string):
    """

    @param dice_string:
    @return: list of tuples representing (#num dice, dice size)
    """
    segments = re.split(r'([+-])', dice_string)
    num_dice = []
    dice_size = []
    p = re.compile('(\d+)d(\d+)')
    sign = 1
    for seg in segments:
        try:
            m = p.match(seg)
            num_dice.append(sign * int(m.group(1)))
            dice_size.append(int(m.group(2)))
        except AttributeError:
            sign = SIGN[seg]
    return zip(num_dice, dice_size)

def avg_roll(dice_string):
    dice = parse_dmg_dice(dice_string)
    return reduce(lambda acc, d: acc + d[0] * ((1.0 + d[1]) / 2.0), dice)


@cache
def mean_dmg(to_hit, dmg_dice, dmg_bonus, ac, crit_range=1, is_resistant=False):
    """
    Calculates mean dmg of an attack-like ability
    @param to_hit: to hit bonus
    @param dmg_dice: damage dice in a string form
    @param dmg_bonus: bonus to damage
    @param ac: target's AC
    @param crit_range: 1 - default for nat 20, 2 for [19, 20], 3 for [18..20], etc.
    @param is_resistant: True if the target is resistant to the dmg type
    @return: mean damage not accounting for critical failures
    """
    rv = randint(1, 21, to_hit)
    p_hit = 1.0 - rv.cdf(ac - 1)
    dice = parse_dmg_dice(dmg_dice)
    avg_dmg_die_roll = reduce(lambda acc, d: acc + d[0] * ((1.0 + d[1]) / 2.0), dice)
    res = (avg_dmg_die_roll + dmg_bonus) * p_hit + 0.05 * crit_range * avg_dmg_die_roll
    return res if not is_resistant else (res / 2)


@cache
def dmg_increment_for_to_hit_flat(to_hit, dmg_dice, dmg_bonus, ac, to_hit_increment, crit_range=1,  is_resistant=False):
    """
    Calculates the increase in mean dmg for an attack-like ability using a flat to-hit bonus
    @param to_hit: to hit bonus
    @param dmg_dice: damage dice in a string form
    @param dmg_bonus: bonus to damage
    @param ac: target's AC
    @param to_hit_increment:
    @return: mean damage increment not accounting for critical failures
    """
    return mean_dmg(to_hit + to_hit_increment, dmg_dice, dmg_bonus, ac, crit_range, is_resistant) - mean_dmg(to_hit, dmg_dice, dmg_bonus, ac, crit_range, is_resistant)

@cache
def dmg_increment_for_dmg_flat(to_hit, dmg_dice, dmg_bonus, ac, dmg_increment):
    """
    Calculates the increase in mean dmg for an attack-like ability using a flat damage bonus
    @param to_hit: to hit bonus
    @param dmg_dice: damage dice in a string form
    @param dmg_bonus: bonus to damage
    @param ac: target's AC
    @param dmg_increment:
    @return: mean damage increment not accounting for critical failures
    """
    return mean_dmg(to_hit, dmg_dice, dmg_bonus + dmg_increment, ac) - mean_dmg(to_hit, dmg_dice, dmg_bonus, ac)


@cache
def dmg_decrement_for_ac_flat(to_hit, dmg_dice, dmg_bonus, ac, ac_bonus, crit_range=1,  is_resistant=False):
    """
    Calculates the decrease in mean dmg received for an attack-like ability using a flat AC bonus
    @param to_hit: to hit bonus
    @param dmg_dice: damage dice in a string form
    @param dmg_bonus: bonus to damage
    @param ac: target's AC
    @param ac_bonus: bonus to target's AC
    @return: mean damage decrement not accounting for critical failures (positive value)
    """
    return mean_dmg(to_hit, dmg_dice, dmg_bonus, ac, crit_range, is_resistant) - mean_dmg(to_hit, dmg_dice, dmg_bonus, ac + ac_bonus, crit_range, is_resistant)


@cache
def mean_dmg_bonus_increment_for_to_hit_bonus_dice(to_hit, dmg_dice, dmg_bonus, ac, bonus_dice_size):
    """
    Calculates the increase in mean dmg for an attack-like ability using a to-hit bonus die
    @param to_hit: to hit bonus
    @param dmg_dice: damage dice in a string form
    @param dmg_bonus: bonus to damage
    @param ac: target's AC
    @param bonus_dice_size:
    @return: mean damage increment not accounting for critical failures
    """
    return mean_dmg(to_hit + (1.0 + bonus_dice_size) / 2.0, dmg_dice, dmg_bonus, ac) - mean_dmg(to_hit, dmg_dice, dmg_bonus, ac)


def print_ac_dc_range(min, max, attacks, monster_name="Monster"):
    print(monster_name + ":")
    for i in range(min, max + 1):
        dmg_sum = reduce((lambda a, b: a + b), [a(i) for a in attacks])
        print("{:.2f}".format(dmg_sum))
    print()


def calc_attack(to_hit, dmg_dice, dmg_bonus):
    return partial(mean_dmg, to_hit, dmg_dice, dmg_bonus)


@cache
def mean_dmg_dc_attack(dc, dmg_dice, half_on_success, st_bonus, is_resistant=False):
    """
    Calculates mean damage of a DC-based ability
    @param dc: DC
    @param dmg_dice: dmg dice in string form
    @param half_on_success: True if half damage is received on a successful saving throw, False if zero
    @param st_bonus: respective saving throw bonus
    @return:
    """
    dice = parse_dmg_dice(dmg_dice)
    avg_dmg_die_roll = reduce(lambda acc, d: acc + d[0] * ((1.0 + d[1]) / 2.0), dice)
    rv = randint(1, 21, st_bonus)
    p_fail = rv.cdf(dc - 1)
    fail_dmg = avg_dmg_die_roll * p_fail
    final_avg_dmg = fail_dmg + avg_dmg_die_roll / 2.0 * (1.0 - p_fail) if half_on_success else fail_dmg
    return final_avg_dmg if not is_resistant else final_avg_dmg / 2


def calc_dc_attack(dc, dmg_dice, half_on_success):
    return partial(mean_dmg_dc_attack, dc, dmg_dice, half_on_success)


def roll_dice(dice):
    """

    @param dice: list of tuples of (# of dice (1..inf), dice sizes (4, 6, 8, 10, 12))
    @return:
    """
    dice_sum = 0
    for d in dice:
        for _ in range(d[0]):
            dice_sum += random.randint(1, d[1])
    return dice_sum


def roll_dice_chaos_bolt(dice):
    dice_sum = 0
    numbers_rolled = []
    for i in range(dice[0]):
        rolled = random.randint(1, dice[1])
        dice_sum += rolled
        numbers_rolled.append(rolled)
    return dice_sum, numbers_rolled


def roll_spell_dmg(dmg_dice):
    dice = parse_dmg_dice(dmg_dice)
    return roll_dice(dice)


def roll_chaos_bolt_dmg(dmg_dice, additional_dmg_dice):
    dice = parse_dmg_dice(dmg_dice)
    primary_dmg, numbers = roll_dice_chaos_bolt(dice[0])
    dice = parse_dmg_dice(additional_dmg_dice)
    secondary_dmg = roll_dice(dice)
    return primary_dmg + secondary_dmg, numbers


def linex_loss(x):
    return (math.e ** (x - 10)) + 2 * (x - 10) + 10


def normal_dist(x, mean, sd):
    prob_density = (np.pi * sd) * np.exp(-0.5 * ((x - mean) / sd) ** 2)
    return prob_density


def caster_distance_reward_func(dist):
    return normal_dist(dist, 15, 8) - 13


def percentage_hp_loss(start_of_turn_hp, combatant):
    return 100 * (start_of_turn_hp - max(0, combatant.curr_hp)) / combatant.max_hp

def percent_of_curr_hp(combatant, dmg):
    return dmg / (combatant.curr_hp * 0.01)


# def init_coroutine(func):
#     @functools.wraps(func)
#     def init(*args, **kwargs):
#         gen = func(*args, **kwargs)
#         next(gen)
#         return gen
#     return init
