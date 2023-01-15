from enum import Enum, Flag, auto
import random
import re
import math
import numpy as np
from scipy.stats import randint
from functools import reduce, partial, cache


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


@cache
def parse_dmg_dice(dice_string):
    p = re.compile('(\d+)d(\d+)')
    m = p.match(dice_string)
    num_dice = int(m.group(1))
    dice_size = int(m.group(2))
    return num_dice, dice_size


@cache
def mean_dmg(to_hit, dmg_dice, dmg_bonus, ac, crit_range=1):
    """
    Calculates mean dmg of an attack-like ability
    @param to_hit: to hit bonus
    @param dmg_dice: damage dice in a string form
    @param dmg_bonus: bonus to damage
    @param ac: target's AC
    @param crit_range: 1 - default for nat 20, 2 for [19, 20], 3 for [18..20], etc.
    @return: mean damage not accounting for critical failures
    """
    rv = randint(1, 21, to_hit)
    p_hit = 1.0 - rv.cdf(ac - 1)
    num_dice, dice_size = parse_dmg_dice(dmg_dice)
    avg_dmg_die_roll = num_dice * ((1.0 + dice_size) / 2.0)
    return (avg_dmg_die_roll + dmg_bonus) * p_hit + 0.05 * crit_range * avg_dmg_die_roll


@cache
def dmg_increment_for_to_hit_flat(to_hit, dmg_dice, dmg_bonus, ac, to_hit_increment):
    """
    Calculates the increase in mean dmg for an attack-like ability using a flat to-hit bonus
    @param to_hit: to hit bonus
    @param dmg_dice: damage dice in a string form
    @param dmg_bonus: bonus to damage
    @param ac: target's AC
    @param to_hit_increment:
    @return: mean damage increment not accounting for critical failures
    """
    return mean_dmg(to_hit + to_hit_increment, dmg_dice, dmg_bonus, ac) - mean_dmg(to_hit, dmg_dice, dmg_bonus, ac)


@cache
def dmg_decrement_for_ac_flat(to_hit, dmg_dice, dmg_bonus, ac, ac_bonus):
    """
    Calculates the decrease in mean dmg received for an attack-like ability using a flat AC bonus
    @param to_hit: to hit bonus
    @param dmg_dice: damage dice in a string form
    @param dmg_bonus: bonus to damage
    @param ac: target's AC
    @param ac_bonus: bonus to target's AC
    @return: mean damage increment not accounting for critical failures
    """
    return mean_dmg(to_hit, dmg_dice, dmg_bonus, ac) - mean_dmg(to_hit, dmg_dice, dmg_bonus, ac + ac_bonus)


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
def mean_dmg_dc_attack(dc, dmg_dice, half_on_success, st_bonus):
    """
    Calculates mean damage of a DC-based ability
    @param dc: DC
    @param dmg_dice: dmg dice in string form
    @param half_on_success: True if half damage is received on a successful saving throw, False if zero
    @param st_bonus: respective saving throw bonus
    @return:
    """
    num_dice, dice_size = parse_dmg_dice(dmg_dice)
    avg_dmg_die_roll = num_dice * ((1.0 + dice_size) / 2.0)
    rv = randint(1, 21, st_bonus)
    p_fail = rv.cdf(dc - 1)
    fail_dmg = avg_dmg_die_roll * p_fail
    final_avg_dmg = fail_dmg + avg_dmg_die_roll / 2.0 * (1.0 - p_fail) if half_on_success else fail_dmg
    return final_avg_dmg


def calc_dc_attack(dc, dmg_dice, half_on_success):
    return partial(mean_dmg_dc_attack, dc, dmg_dice, half_on_success)


def roll_dice(num_dice, dice_size):
    dice_sum = 0
    for i in range(num_dice):
        dice_sum += random.randint(1, dice_size)
    return dice_sum


def roll_dice_chaos_bolt(num_dice, dice_size):
    dice_sum = 0
    numbers_rolled = []
    for i in range(num_dice):
        rolled = random.randint(1, dice_size)
        dice_sum += rolled
        numbers_rolled.append(rolled)
    return dice_sum, numbers_rolled


def roll_spell_dmg(dmg_dice):
    num_dice, dice_size = parse_dmg_dice(dmg_dice)
    return roll_dice(num_dice, dice_size)


def roll_chaos_bolt_dmg(dmg_dice, additional_dmg_dice):
    num_dice, dice_size = parse_dmg_dice(dmg_dice)
    primary_dmg, numbers = roll_dice_chaos_bolt(num_dice, dice_size)
    num_dice, dice_size = parse_dmg_dice(additional_dmg_dice)
    secondary_dmg = roll_dice(num_dice, dice_size)
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

# def init_coroutine(func):
#     @functools.wraps(func)
#     def init(*args, **kwargs):
#         gen = func(*args, **kwargs)
#         next(gen)
#         return gen
#     return init
