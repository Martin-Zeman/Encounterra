import importlib
import inspect
import logging
import math
import pkgutil
import random
import numba_functions as nf
from .roll_types import RollType

logger = logging.getLogger("Encounterra")

HALF_SQUARE_DIAGONAL = math.sqrt(2) / 2


def get_combatant_classes():
    # Import the top-level module
    module = importlib.import_module('simulator.combatants')

    # Recursively iterate over all submodules
    classes = []
    for _, module_name, is_pkg in pkgutil.walk_packages(module.__path__):
        full_module_name = f'simulator.combatants.{module_name}'
        sub_module = importlib.import_module(full_module_name)

        for name, obj in inspect.getmembers(sub_module):
            # Check if the attribute is a class and a subclass of Combatant. Has to be done this way do to id(Combatant) being different from the one imported this way
            if inspect.isclass(obj) and "Combatant" in [base.__name__ for base in obj.__bases__] and obj.__name__ != "Combatant":
                # Add the subclass to the list
                classes.append(obj)

    return classes


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

from functools import cache
