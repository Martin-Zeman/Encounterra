from enum import Enum, Flag, auto
import random
import re
from functools import reduce, cache

from simulator.actions.actoid import FactoryFlags
import logging
from simulator.utils.roll_types import RollType

logger = logging.getLogger("EncounTroll")

ROUND_HORIZON = 3

class SavingThrow(Enum):
    STR = 1
    DEX = 2
    CON = 3
    INT = 4
    WIS = 5
    CHA = 6

class SkillCheck(Enum):
    ATHLETICS = 1
    ACROBATICS = 2


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
    SWALLOWED = auto()  # Meta-Condition
    GRAPPLING = auto()  # Meta-Condition


class PhaseOfTurn(Enum):
    START_OF_TURN = auto()
    END_OF_TURN = auto()
    ACTION = auto()


class ConditionWithoutDC:
    def __init__(self, conditions, initiator):
        self.conditions = conditions  # Could multiples such as grapple + restrained go often together
        self.initiator = initiator


class ConditionWithDC:
    def __init__(self, conditions, st, dc, initiator, phase):
        self.conditions = conditions  # Could multiples such as grapple + restrained go often together
        self.st = st
        self.dc = dc
        self.initiator = initiator
        self.phase = phase


class Size(Enum):
    TINY = -2
    SMALL = -1
    MEDIUM = 0
    LARGE = 1
    HUGE = 2
    GARGANTUAN = 3


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

def reconcile_roll_types(types):
    """

    @param modifiers: set of modifiers
    @return: resulting modifier
    """
    try:
        types.remove(RollType.STRAIGHT)  # TODO Do I need this?
    except KeyError:
        pass
    if len(types) > 1:
        return RollType.STRAIGHT
    try:
        ret = types.pop()
    except KeyError:
        ret = RollType.STRAIGHT
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


def roll_dice(dice):
    """
    Basic function for rolling dice
    @param dice: list of tuples of (# of dice (1..inf), dice sizes (4, 6, 8, 10, 12))
    @return:
    """
    dice_sum = 0
    for d in dice:
        for _ in range(d[0]):
            dice_sum += random.randint(1, d[1])
    return dice_sum


def roll_saving_throw(bonus, dc, roll_type):
    d20 = parse_dmg_dice('1d20')
    if roll_type is RollType.STRAIGHT:
        roll = roll_dice(d20)
    elif roll_type is RollType.ADVANTAGE:
        roll = max(roll_dice(d20), roll_dice(d20))
    else:
        roll = min(roll_dice(d20), roll_dice(d20))

    if roll == 20:
        return True
    return roll + bonus >= dc



def roll_ability_check(bonus, dc, roll_type):
    d20 = parse_dmg_dice('1d20')
    if roll_type is RollType.STRAIGHT:
        return roll_dice(d20) + bonus >= dc
    elif roll_type is RollType.ADVANTAGE:
        return max(roll_dice(d20), roll_dice(d20)) + bonus >= dc
    else:
        return min(roll_dice(d20), roll_dice(d20)) + bonus >= dc


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


def percentage_hp_loss(start_of_turn_hp, combatant):
    return 100 * (start_of_turn_hp - max(0, combatant.curr_hp)) / combatant.max_hp

def percent_of_curr_hp(combatant, dmg):
    return dmg / (combatant.curr_hp * 0.01)

def get_factory_of_type(factories, type):
    for f in factories:
        if f[0] is type:
            return f[1]
    return None


def get_attacks(combatant):
    attacks = [af[1] for af in combatant.action_factories if FactoryFlags.IS_ATTACK_LIKE in af[1].flags]
    attacks.extend([baf[1] for baf in combatant.bonus_action_factories if FactoryFlags.IS_ATTACK_LIKE in baf[1].flags])
    return attacks

def get_haste_eligile_attacks(combatant):
    attacks = [af[1] for af in combatant.action_factories if FactoryFlags.IS_HASTE_ELIGIBLE_ATTACK in af[1].flags]
    return attacks


def reconstruct_path_through_dag(leaf_state, initial_state, max_threat_backwards_transition):
    """
    A small utility function that goes backwards from a leaf state in a DAG towards the initial state and reconstructs the path
    :param leaf_state:
    :param initial_state: path as a sequence of np.array coordinates
    :param max_threat_backwards_transition: backwards transition dict which state -> predecessor state
    :return: reconstructed path
    """
    curr_state = leaf_state
    reconstructed_path = []
    while curr_state != initial_state:
        try:
            reconstructed_path.insert(0, max_threat_backwards_transition[curr_state][0])
            curr_state = max_threat_backwards_transition[curr_state][1]
        except KeyError:
            print("FIXME")
    return reconstructed_path

