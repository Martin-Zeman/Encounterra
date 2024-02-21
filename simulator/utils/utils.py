import importlib
import inspect
import logging
import math
import pkgutil
from ..abilities.wildshape import Wildshape
from ..actions.action_types import Action, BonusAction
from ..combatants.brown_bear import BrownBear
from ..combatants.dire_wolf import DireWolf
from ..combatants.giant_constrictor_snake import GiantConstrictorSnake
from ..combatants.giant_spider import GiantSpider
from ..combatants.giant_toad import GiantToad
from ..combatants.quetzalcoatlus import Quetzalcoatlus
from ..combatants.saber_toothed_tiger import SaberToothedTiger

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


def get_available_wildshape_forms(level, action_type):
    if action_type is Action.WILDSHAPE:
        pass
    elif action_type is BonusAction.MOON_WILDSHAPE:
        match level:
            case lvl if 2 <= lvl <= 5:
                # return [DireWolf, BrownBear, GiantToad, GiantSpider]
                return [GiantToad]
            case lvl if 6 <= lvl <= 8:
                return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, SaberToothedTiger]
            case lvl if 9 <= lvl <= 11:
                return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, SaberToothedTiger]
                # return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, Quetzalcoatlus, SaberToothedTiger, Ankylosaurus, GiantScorpion]
            case lvl if 12 <= lvl <= 14:
                return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, SaberToothedTiger]
                # return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, Quetzalcoatlus, SaberToothedTiger, Ankylosaurus, GiantScorpion, Stegosaurus]
            case lvl if 15 <= lvl <= 17:
                return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, SaberToothedTiger]
                # return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, Quetzalcoatlus, SaberToothedTiger, Ankylosaurus, GiantScorpion, Stegosaurus, GiantCrocodile]
            case lvl if 18 <= lvl <= 20:
                return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, SaberToothedTiger]
                # return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, Quetzalcoatlus, SaberToothedTiger, Ankylosaurus, GiantScorpion, Stegosaurus, GiantCrocodile, Mammoth]
            case _:
                logger.error("Incorrect character level. No wildshape forms added!")
    return []


def preallocate_wildshape_forms(combatant, action_type, factory):
    available_forms = get_available_wildshape_forms(combatant.level, action_type)
    return [Wildshape(combatant, form, factory) for form in available_forms]

from functools import cache
