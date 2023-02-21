import sys
from enum import Enum, Flag, auto
import random
import re
import math
import numpy as np
from scipy.stats import randint
from functools import reduce, partial, cache
from functools import reduce

from simulator.actions.actoid import FactoryFlags

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

class CombatantArchetype(Enum):
    MELEE = 0
    RANGED = 1
    HYBRID = 2


SIGN = {"+": 1, "-": -1}

# Calculated by find_disadvantage_eq_penalty and find_advantage_eq_bonus. Gives the statistic approximation of advantage/disadvantage in
# terms of a flat bonus/penalty. This is dependent on the AC/DC threshold.
ROLL_MODIFIER = {
    RollModifier.STRAIGHT: {
        1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0, 17: 0, 18: 0, 19: 0, 20: 0
    },
    # The Advantage equivalent bonus for a needed roll of at least equal to the key
    RollModifier.ADVANTAGE: {
        1: 0, 2: 3, 3: 4, 4: 5, 5: 5, 6: 5, 7: 5, 8: 5, 9: 5, 10: 4, 11: 4, 12: 4, 13: 3, 14: 3, 15: 3, 16: 2, 17: 2, 18: 1, 19: 1, 20: 0
    },
    # The Disadvantage equivalent penalty for a needed roll of at least equal to the key
    RollModifier.DISADVANTAGE: {
        1: 0, 2: 0, 3: -1, 4: -1, 5: -2, 6: -2, 7: -3, 8: -3, 9: -3, 10: -4, 11: -4, 12: -4, 13: -5, 14: -5, 15: -5, 16: -5, 17: -5, 18: -5,
        19: -4, 20: -3
    }
}

# TODO This may be oversimplified, calculate a bit more thoroughly
ROLL_MODIFIER_CRIT = {
    RollModifier.STRAIGHT: 1.0,
    RollModifier.ADVANTAGE: 2.0,
    RollModifier.DISADVANTAGE: 0.5
}

def reconcile_roll_modifiers(modifiers):
    """

    @param modifiers: set of modifiers
    @return: resulting modifier
    """
    try:
        modifiers.remove(RollModifier.STRAIGHT)  # TODO Do I need this?
    except KeyError:
        pass
    if len(modifiers) > 1:
        return RollModifier.STRAIGHT
    try:
        ret = modifiers.pop()
    except:  # TODO Find the exact one
        ret = RollModifier.STRAIGHT
    return ret

@cache
def parse_dmg_dice(dice_string):
    """

    @param dice_string:
    @return: list of tuples representing (#num dice, dice size)
    """
    segments = re.split(r'([+-])', dice_string)
    res = []
    p = re.compile('(\d+)d(\d+)')
    sign = 1
    for seg in segments:
        try:
            m = p.match(seg)
            res.append((sign * int(m.group(1)), int(m.group(2))))
        except AttributeError:
            sign = SIGN[seg]
    return res

def avg_roll(dice_string):
    dice = parse_dmg_dice(dice_string)
    return reduce(lambda acc, d: acc + d[0] * ((1.0 + d[1]) / 2.0), dice, 0)


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
    avg_dmg_die_roll = reduce(lambda acc, d: acc + d[0] * ((1.0 + d[1]) / 2.0), dice, 0)
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


def calculate_threat_in_mod(combatant, threat_radius, battle_map, roll_modifier, factory_flags):
    """
    Estimates the change in mean dmg from enemies within radius given a roll modifier assuming they'd all attack the combatant
    @param combatant: the potential receiver of the dmg
    @param threat_radius: radius within which enemies are to be considered
    @param battle_map:
    @param roll_modifier: the roll modifier to be considered (advantage or disadvantage)
    @param factory_flags: the kind of factory which is relevant for this calculation(e.g. attacks only or any direct threat...)
    @return: estimated change in dmg, negative for advantage, positive for disadvantage
    """
    potential_attackers = battle_map.get_enemies_within_hop_distance(combatant, threat_radius)
    incoming_threat_mod_acc = 0
    min_or_max = max if roll_modifier is RollModifier.ADVANTAGE else min
    for pa in potential_attackers:
        max_incoming_threat = 0
        for f in pa.action_factories:
            if factory_flags & f[1].flags:  # Checks for any overlap in flags
                max_incoming_threat = min_or_max(max_incoming_threat, f[1].calculate_threat_to_target_mod(battle_map, combatant, {
                    "roll_modifier": roll_modifier}))
        incoming_threat_mod_acc += max_incoming_threat

        max_incoming_threat = 0
        for f in pa.bonus_action_factories:
            if factory_flags & f[1].flags:  # Checks for any overlap in flags
                max_incoming_threat = min_or_max(max_incoming_threat, f[1].calculate_threat_to_target_mod(battle_map, combatant, {
                    "roll_modifier": roll_modifier}))
        incoming_threat_mod_acc += max_incoming_threat

        max_incoming_threat = 0
        for f in pa.haste_action_factories:
            if factory_flags & f[1].flags:  # Checks for any overlap in flags
                max_incoming_threat = min_or_max(max_incoming_threat, f[1].calculate_threat_to_target_mod(battle_map, combatant, {
                    "roll_modifier": roll_modifier}))
        incoming_threat_mod_acc += max_incoming_threat
    if roll_modifier is RollModifier.ADVANTAGE:
        assert incoming_threat_mod_acc >= 0
    else:
        assert incoming_threat_mod_acc <= 0
    return incoming_threat_mod_acc

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
    avg_dmg_die_roll = reduce(lambda acc, d: acc + d[0] * ((1.0 + d[1]) / 2.0), dice, 0)
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

def roll_saving_throw(bonus, dc, roll_modifier):
    if roll_modifier is RollModifier.STRAIGHT:
        return roll_dice('1d20') + bonus >= dc
    elif roll_modifier is RollModifier.ADVANTAGE:
        return max(roll_dice('1d20'), roll_dice('1d20')) + bonus >= dc
    else:
        return min(roll_dice('1d20'), roll_dice('1d20')) + bonus >= dc


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

def get_factory_of_type(factories, type):
    for f in factories:
        if f[0] is type:
            return f[1]
    return None


# def init_coroutine(func):
#     @functools.wraps(func)
#     def init(*args, **kwargs):
#         gen = func(*args, **kwargs)
#         next(gen)
#         return gen
#     return init
