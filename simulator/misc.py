from enum import Enum, auto
import random
import re
from functools import reduce, cache
from itertools import product

import numpy as np
import numba_functions as nf
from numba import njit

from .actions.actoid import FactoryFlags
import logging
from .utils.roll_types import RollType

logger = logging.getLogger("Encounterra")

ROUND_HORIZON = 3
SHORTER_ROUND_HORIZON = 2


class Artificer(Enum):
    ALCHEMIST = "Alchemist"
    ARMORER = "Armorer"
    ARTILLERIST = "Artillerist"
    BATTLE_SMITH = "Battlesmith"


class Barbarian(Enum):
    PATH_OF_THE_ANCESTRAL_GUARDIAN = "Path of the Ancestral Guardian"
    PATH_OF_THE_BEAST = "Path of the Beast"
    PATH_OF_THE_BERSERKER = "Path of the Berserker"
    PATH_OF_THE_STORM_HERALD = "Path of the Storm Herald"
    PATH_OF_THE_TOTEM_WARRIOR = "Path of the Totem Warrior"
    PATH_OF_THE_ZEALOT = "Path of the Zealot"
    PATH_OF_WILD_MAGIC = "Path of the Wild Magic"
    BEFORE_SUBCLASS = ""


class Bard(Enum):
    COLLEGE_OF_CREATION = "College of Creation"
    COLLEGE_OF_ELOQUENCE = "College of Eloquence"
    COLLEGE_OF_GLAMOUR = "College of Glamour"
    COLLEGE_OF_LORE = "College of Lore"
    COLLEGE_OF_SPIRITS = "College of Spirits"
    COLLEGE_OF_SWORDS = "College of Swords"
    COLLEGE_OF_VALOR = "College of Valor"
    COLLEGE_OF_WHISPERS = "College of Whispers"
    BEFORE_SUBCLASS = ""


class Cleric(Enum):
    ARCANA_DOMAIN = "Arcana Domain"
    DEATH_DOMAIN = "Death Domain"
    FORGE_DOMAIN = "Forge Domain"
    GRAVE_DOMAIN = "Grave Domain"
    KNOWLEDGE_DOMAIN = "Knowledge Domain"
    LIFE_DOMAIN = "Life Domain"
    LIGHT_DOMAIN = "Light Domain"
    NATURE_DOMAIN = "Nature Domain"
    ORDER_DOMAIN = "Order Domain"
    PEACE_DOMAIN = "Peace Domain"
    TEMPEST_DOMAIN = "Tempest Domain"
    TRICKERY_DOMAIN = "Trickery Domain"
    TWILIGHT_DOMAIN = "Twilight Domain"
    WAR_DOMAIN = "War Domain"


class Druid(Enum):
    CIRCLE_OF_DREAMS = "Circle of Dreams"
    CIRCLE_OF_SPORES = "Circle of Spores"
    CIRCLE_OF_STARS = "Circle of Stars"
    CIRCLE_OF_WILDFIRE = "Circle of Wildfire"
    CIRCLE_OF_LAND = "Circle of Land"
    CIRCLE_OF_MOON = "Circle of Moon"
    CIRCLE_OF_SHEPHERD = "Circle of Shepherd"
    BEFORE_SUBCLASS = ""


class Fighter(Enum):
    ARCANE_ARCHER = "Arcane Archer"
    BATTLE_MASTER = "Battlemaster"
    CAVALIER = "Cavalier"
    ECHO_KNIGHT = "Echo Knight"
    ELDRITCH_KNIGHT = "Eldritch Knight"
    PSI_WARRIOR = "Psi Warrior"
    RUNE_KNIGHT = "Rune Knight"
    SAMURAI = "Samurai"
    PURPLE_DRAGON_KNIGHT = "Purple Dragon Knight"
    BEFORE_SUBCLASS = ""


class Paladin(Enum):
    OATH_OF_CONQUEST = "Oath of Conquest"
    OATH_OF_DEVOTION = "Oath of Devotion"
    OATH_OF_GLORY = "Oath of Glory"
    OATH_OF_REDEMPTION = "Oath of Redemption"
    OATH_OF_ANCIENTS = "Oath of Ancients"
    OATH_OF_CROWN = "Oath of Crown"
    OATH_OF_WATCHERS = "Oath of Watchers"
    OATH_OF_VENGEANCE = "Oath of Vengeance"
    OATHBREAKER = "Oathbreaker"
    BEFORE_SUBCLASS = ""


class Ranger(Enum):
    BEAST_MASTER = "Beastmaster"
    DRAKEWARDEN = "Drakewarden"
    FEY_WANDERER = "Fey Wanderer"
    GLOOM_STALKER = "Gloomstalker"
    HORIZON_WALKER = "Horizon Walker"
    HUNTER = "Hunter"
    MONSTER_SLAYER = "Monster Slayer"
    SWARMKEEPER = "Swarmkeeper"
    BEFORE_SUBCLASS = ""


class Rogue(Enum):
    ARCANE_TRICKSTER = "Arcane Trickster"
    ASSASSIN = "Assassin"
    INQUISITIVE = "Inquisitive"
    PHANTOM = "Phantom"
    MASTERMIND = "Mastermind"
    SCOUT = "Scout"
    SOULKNIFE = "Soulknife"
    SWASHBUCKLER = "Swashbuckler"
    THIEF = "Thief"
    BEFORE_SUBCLASS = ""


class Monk(Enum):
    WAY_OF_MERCY = "Way of Mercy"
    WAY_OF_SHADOW = "Way of Shadow"
    WAY_OF_THE_ASCENDANT_DRAGON = "Way of the Ascendant Dragon"
    WAY_OF_ASTRAL_SELF = "Way of Astral Self"
    WAY_OF_DRUNKEN_MASTER = "Way of the Drunken Master"
    WAY_OF_THE_FOUR_ELEMENTS = "Way of the Four Elements"
    WAY_OF_KENSEI = "Way of the Kensei"
    WAY_OF_THE_LONG_DEATH = "Way of the Long Death"
    WAY_OF_THE_OPEN_HAND = "Way of the Open Hand"
    WAY_OF_THE_SUN_SOUL = "Way of the Sun Soul"
    BEFORE_SUBCLASS = ""


class Sorcerer(Enum):
    ABERRANT_MIND = "Aberrant Mind"
    CLOCKWORK_SOUL = "Clockwork Soul"
    DIVINE_SOUL = "Divine Soul"
    DRACONIC_BLOODLINE = "Draconic Bloodline"
    SHADOW_MAGIC = "Shadow Magic"
    STORM_SORCERY = "Storm Sorcery"
    WILD_MAGIC = "Wild Magic"


class Warlock(Enum):
    THE_ARCHFEY = "The Archfey"
    THE_CELESTIAL = "The Celestial"
    THE_FATHOMLESS = "The Fathomless"
    THE_FIEND = "The Fiend"
    THE_GENIE = "The Genie"
    THE_GREAT_OLD_ONE = "The Great Old one"
    THE_HEXBLADE = "The Hexblade"
    THE_UNDEAD = "The Undead"
    THE_UNDYING = "The Undying"


class Wizard(Enum):
    BLADESINGER = "Bladesinger"
    CHRONURGY = "Chronurgy"
    GRAVITURGY = "Graviturgy"
    ORDER_OF_SCRIBES = "Order of Scribes"
    ABJURATION = "Abjuration"
    CONJURATION = "Conjuration"
    DIVINATION = "Divination"
    ENCHANTMENT = "Enchantment"
    EVOCATION = "Evocation"
    ILLUSION = "Illusion"
    NECROMANCY = "Necromancy"
    TRANSMUTATION = "Transmutation"
    WAR_MAGIC = "War Magic"
    BEFORE_SUBCLASS = ""


class Monster(Enum):
    HUMANOID = "Humanoid"
    GIANT = "Giant"
    MONSTROSITY = "Monstrosity"
    BEAST = "Beast"
    UNDEAD = "Undead"
    DRAGON = "Dragon"
    CONSTRUCT = "Construct"
    ELEMENTAL = "Elemental"
    ABERRATION = "Aberration"
    FEY = "Fey"
    OOZE = "Ooze"
    PLANT = "Plant"
    FIEND = "Fiend"


class Class:
    ARTIFICER = Artificer
    BARBARIAN = Barbarian
    BARD = Bard
    CLERIC = Cleric
    DRUID = Druid
    FIGHTER = Fighter
    PALADIN = Paladin
    RANGER = Ranger
    ROGUE = Rogue
    MONK = Monk
    SORCERER = Sorcerer
    WARLOCK = Warlock
    WIZARD = Wizard
    MONSTER = Monster


class SpellcastingResourceType(Enum):
    SPELLSLOTS = auto()
    SPECIAL = auto()


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
    BludgeoningMagical = 13
    SlashingMagical = 14
    PiercingMagical = 15
    Random = 16  # Pseudotype (used for Chaosbolt)

    def __str__(self):
        return self.name


TO_MAGICAL = {
    DamageType.Bludgeoning: DamageType.BludgeoningMagical,
    DamageType.Slashing: DamageType.SlashingMagical,
    DamageType.Piercing: DamageType.PiercingMagical,
}


class PhaseOfTurn(Enum):
    START_OF_TURN = auto()
    END_OF_TURN = auto()
    ACTION = auto()


class Statistics(Enum):
    VICTORIES = 1
    AT_LEAST_ONE_DIED = 2
    AT_LEAST_TWO_DIED = 3
    AT_LEAST_THREE_DIED = 4


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


SIGN = {"+": 1, "-": -1}


def reconcile_roll_types(types):
    """

    @param types: set of modifiers
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
def generate_outcomes(dice):
    # Generate all possible outcomes for a given dice configuration
    outcomes = []
    for _ in range(dice[0]):
        outcomes.append(range(1, dice[1] + 1))
    return list(product(*outcomes))


def find_percentile_value(outcomes, percentile):
    # Find the value at the given percentile in the sorted outcomes
    index = int(len(outcomes) * (percentile / 100.0))
    return sorted(outcomes)[index]

@cache
def percentile_roll(dice, percentile):
    # Generate and sum all possible outcomes
    all_outcomes = [sum(combination) for combination in generate_outcomes(dice)]
    return find_percentile_value(all_outcomes, percentile)


# Use the function and handle logging outside the Numba-compiled function
def roll_dice_with_reroll(dice, reroll_max_value):
    result, reroll_log = nf.roll_dice_with_reroll_and_log(dice, reroll_max_value)
    for original, reroll in reroll_log:
        logger.info(f"Re-rolling {original} as {reroll}")
    return result


# njit candidate
def roll_saving_throw(bonus, dc, roll_type):
    d20 = (1, 20)
    if roll_type is RollType.STRAIGHT:
        roll = nf.roll_dice(d20)
    elif roll_type is RollType.ADVANTAGE:
        roll = max(nf.roll_dice(d20), nf.roll_dice(d20))
    else:
        roll = min(nf.roll_dice(d20), nf.roll_dice(d20))

    if roll == 20:
        return True
    return roll + bonus >= dc


# njit candidate
def roll_ability_check(bonus, dc, roll_type):
    d20 = (1, 20)
    if roll_type is RollType.STRAIGHT:
        return nf.roll_dice(d20) + bonus >= dc
    elif roll_type is RollType.ADVANTAGE:
        return max(nf.roll_dice(d20), nf.roll_dice(d20)) + bonus >= dc
    else:
        return min(nf.roll_dice(d20), nf.roll_dice(d20)) + bonus >= dc


def roll_dice_chaos_bolt(dice):
    dice_sum = 0
    numbers_rolled = []
    for i in range(dice[0]):
        rolled = random.randint(1, dice[1])
        dice_sum += rolled
        numbers_rolled.append(rolled)
    return dice_sum, numbers_rolled


def roll_chaos_bolt_dmg(dmg_dice, additional_dmg_dice):
    primary_dmg, numbers = roll_dice_chaos_bolt(dmg_dice[0])
    secondary_dmg = nf.roll_dice(additional_dmg_dice[0])
    return primary_dmg + secondary_dmg, numbers


def percent_of_curr_hp(combatant, dmg):
    return dmg / (combatant.curr_hp * 0.01)


def get_factory_of_type(factories, factory_type):
    for f in factories:
        if f[0] is factory_type:
            return f[1]
    return None


def get_attack_factories(combatant):
    attacks = [af[1] for af in combatant.action_factories if FactoryFlags.IS_ATTACK_LIKE in af[1].flags]
    attacks.extend([baf[1] for baf in combatant.bonus_action_factories if FactoryFlags.IS_ATTACK_LIKE in baf[1].flags])
    return attacks


def get_strength_based_attack_factories(combatant):
    attacks = [af[1] for af in combatant.action_factories if (FactoryFlags.IS_ATTACK_LIKE in af[1].flags and FactoryFlags.USES_DEX not in af[1].flags)]
    attacks.extend([baf[1] for baf in combatant.bonus_action_factories if FactoryFlags.IS_ATTACK_LIKE in baf[1].flags])
    return attacks


def get_haste_eligible_attacks(combatant):
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


class Visibility(Enum):
    NONE = 0
    THREE_QUARTERS_COVER = 1
    HALF_COVER = 2
    FULL = 3


THREE_QUARTERS_COVER_ERROR_THRESHOLD = 0.25
HALF_COVER_ERROR_THRESHOLD = 0.35
FULL_VISIBILITY_ERROR_THRESHOLD = 0.45


def get_missing_hp(combatant):
    return combatant.max_hp + combatant.max_hp_modifier - combatant.curr_hp


@staticmethod
def get_superiority_dice(level):
    match level:
        case lvl if 3 <= lvl <= 9:
            return (1, 8)
        case lvl if 10 <= lvl <= 17:
            return (1, 10)
        case lvl if 18 <= lvl <= 20:
            return (1, 12)
        case _:
            logger.error("Incorrect Battlemaster level")
            return (1, 8)


@staticmethod
def get_num_superiority_dice(level):
    match level:
        case lvl if 3 <= lvl <= 6:
            return 4
        case lvl if 7 <= lvl <= 14:
            return 5
        case lvl if 15 <= lvl <= 20:
            return 6
        case _:
            logger.error("Incorrect Battlemaster level")
            return 4
