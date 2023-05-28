import logging

from simulator.abilities.wildshape import Wildshape
from simulator.actions.action_types import Action, BonusAction
from simulator.combatants.brown_bear import BrownBear
from simulator.combatants.dire_wolf import DireWolf
from simulator.combatants.giant_constrictor_snake import GiantConstrictorSnake
from simulator.combatants.giant_spider import GiantSpider
from simulator.combatants.giant_toad import GiantToad
from simulator.combatants.quetzalcoatlus import Quetzalcoatlus
from simulator.combatants.saber_toothed_tiger import SaberToothedTiger

logger = logging.getLogger("EncounTroll")

def get_available_wildshape_forms(level, action_type):
    if action_type is Action.WILDSHAPE:
        pass
    elif action_type is BonusAction.MOON_WILDSHAPE:
        match level:
            case lvl if 2 <= lvl <= 5:
                return [DireWolf, BrownBear, GiantToad, GiantSpider]
            case lvl if 6 <= lvl <= 8:
                return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, Quetzalcoatlus, SaberToothedTiger]
            case lvl if 9 <= lvl <= 11:
                return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, Quetzalcoatlus, SaberToothedTiger]
                # return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, Quetzalcoatlus, SaberToothedTiger, Ankylosaurus, GiantScorpion]
            case lvl if 12 <= lvl <= 14:
                return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, Quetzalcoatlus, SaberToothedTiger]
                # return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, Quetzalcoatlus, SaberToothedTiger, Ankylosaurus, GiantScorpion, Stegosaurus]
            case lvl if 15 <= lvl <= 17:
                return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, Quetzalcoatlus, SaberToothedTiger]
                # return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, Quetzalcoatlus, SaberToothedTiger, Ankylosaurus, GiantScorpion, Stegosaurus, GiantCrocodile]
            case lvl if 18 <= lvl <= 20:
                return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, Quetzalcoatlus, SaberToothedTiger]
                # return [DireWolf, BrownBear, GiantToad, GiantSpider, GiantConstrictorSnake, Quetzalcoatlus, SaberToothedTiger, Ankylosaurus, GiantScorpion, Stegosaurus, GiantCrocodile, Mammoth]
            case _:
                logger.error("Incorrect character level. No wildshape forms added!")
    return []

def preallocate_wildshape_forms(combatant, action_type):
    available_forms = get_available_wildshape_forms(combatant.level, action_type)
    return [Wildshape(combatant, form, combatant) for form in available_forms]