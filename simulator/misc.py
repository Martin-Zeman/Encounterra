from enum import Enum, Flag, auto
import random
import re

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
    TINY = auto()
    SMALL = auto()
    MEDIUM = auto()
    LARGE = auto()
    HUGE = auto()
    GARGANTUAN = auto()



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


def roll_spell_dmg(spell):
    num_dice, dice_size = parse_dmg_dice(spell.dmg_dice)
    return roll_dice(num_dice, dice_size)
