import math

from simulator.actions.action_types import Action, BonusAction
from simulator.actions.actoid import Actoid, ActoidFlags, FactoryFlags
from simulator.combatants.brown_bear import BrownBear
from simulator.combatants.dire_wolf import DireWolf
from simulator.combatants.giant_constrictor_snake import GiantConstrictorSnake
from simulator.combatants.giant_spider import GiantSpider
from simulator.combatants.giant_toad import GiantToad
from simulator.combatants.quetzalcoatlus import Quetzalcoatlus
from simulator.combatants.saber_toothed_tiger import SaberToothedTiger
from simulator.effects.combatant_effect import CombatantEffect

from simulator.threat_interfaces import TransformerFactory, DirectThreat
import logging

logger = logging.getLogger("EncounTroll")


class WildshapeFactory(TransformerFactory):

    def __init__(self, combatant, action_type):
        TransformerFactory.__init__()
        self.flags |= FactoryFlags.TARGETS_SELF
        self.combatant = combatant
        self.action_type = action_type

    def __str__(self):
        """
        Important for FSM building
        """
        return "WildshapeFactory"

    @staticmethod
    def get_wildshape_uses(level):
        match level:
            case 20:
                return math.inf
            case _:
                return 2

    @staticmethod
    def get_available_forms(level, action_type):
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
    def get_eligible_targets(self, battle_map):
        pass # No need due to the TARGETS_SELF flag


    def preallocate_wildshape_forms(self):
        available_forms = WildshapeFactory.get_available_forms(self.combatant.level, self.action_type)
        return [Wildshape(self.combatant, form, self) for form in available_forms]
    def create_all(self, battle_map):
        return self.combatant.available_wildshape_forms

    def create(self, form):
        # Doesn't make much sense here
        return Wildshape(self.combatant, form, self)

class Wildshape(Actoid, CombatantEffect, DirectThreat):

    def __init__(self, combatant, form, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[combatant])
        self.actoid_flags |= ActoidFlags.IS_POSITIONING_INDEPENDENT
        self.form = form
        self.factory = factory

    def __str__(self):
        return f"Wildshape of {self.factory.combatant} into {self.form}"

    def activate(self, battle_map):
        logger.info(f"{self.combatants[0]} wildshapes into {self.form}")
        # TODO set the curr hp of the form to the maximum hp
        # TODO set int, wis and char of the target and the STs to be the same as the humanoid form
        # TODO set the has_actions of the wildshape to be the same
        # TODO set is_concentrating of the wildshape to be the same
        # self.combatants[0].ability_dmg_bonus += self.rage_bonus
        # self.combatants[0].resistances.update([DamageType.Slashing, DamageType.Bludgeoning, DamageType.Piercing])

    def deactivate(self, battle_map):
        logger.info(f"{self.combatants[0]}'s wildshape fades")
        # self.combatants[0].ability_dmg_bonus -= self.rage_bonus
        # self.combatants[0].resistances.remove(DamageType.Slashing)
        # self.combatants[0].resistances.remove(DamageType.Bludgeoning)
        # self.combatants[0].resistances.remove(DamageType.Piercing)

    def clear_cache(self):
        pass

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        return self.form.max_hp - combatant.curr_hp

    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        return battle_map.get_all_accessible_coords(shortest_paths)

    def is_current_coord_eligible(self, battle_map):
        return True