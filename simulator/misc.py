from enum import Enum, Flag, auto
import random
import re
import math
import functools


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


def parse_dmg_dice(dice_string):
    p = re.compile('(\d+)d(\d+)')
    m = p.match(dice_string)
    num_dice = int(m.group(1))
    dice_size = int(m.group(2))
    return num_dice, dice_size


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


def percentage_hp_loss(start_of_turn_hp, combatant):
    return 100 * (start_of_turn_hp - max(0, combatant.curr_hp)) / combatant.max_hp


# def init_coroutine(func):
#     @functools.wraps(func)
#     def init(*args, **kwargs):
#         gen = func(*args, **kwargs)
#         next(gen)
#         return gen
#     return init
