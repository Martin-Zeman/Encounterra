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
from simulator.effects.action_enabler_effect import ActionEnablerEffect
from simulator.effects.combatant_effect import CombatantEffect
from simulator.misc import SavingThrow

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


    def preallocate_wildshape_forms(self):
        available_forms = WildshapeFactory.get_available_forms(self.combatant.level, self.action_type)
        return [Wildshape(self.combatant, form, self) for form in available_forms]
    def create_all(self, battle_map):
        return self.combatant.available_wildshape_forms

    def create(self, form):
        # Doesn't make much sense here
        return Wildshape(self.combatant, form, self)

class Wildshape(Actoid, CombatantEffect, ActionEnablerEffect, DirectThreat):

    def __init__(self, combatant, form, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[combatant])
        self.actoid_flags |= ActoidFlags.IS_POSITIONING_INDEPENDENT
        self.form = form(factory.combatant.effect_tracker, f"{factory.combatant} wildshaped into {form.__name__}")
        self.factory = factory

    def __str__(self):
        return f"Wildshape of {self.factory.combatant} into {self.form}"

    def activate(self, battle_map):
        logger.info(f"{self.combatants[0]} wildshapes into {self.form}")
        self.combatants[0].current_wildshape_form = self.form
        self.form.curr_hp = self.form.max_hp
        self.form.saving_throws[SavingThrow.INT] = self.combatants[0].saving_throws[SavingThrow.INT]
        self.form.saving_throws[SavingThrow.WIS] = self.combatants[0].saving_throws[SavingThrow.WIS]
        self.form.saving_throws[SavingThrow.CHA] = self.combatants[0].saving_throws[SavingThrow.CHA]
        self.form.has_action = self.combatants[0].has_action
        self.form.has_bonus_action = self.combatants[0].has_bonus_action
        self.form.has_haste_action = self.combatants[0].has_haste_action
        self.form.has_reaction = self.combatants[0].has_reaction
        self.form.is_concentrating = self.combatants[0].is_concentrating

    def deactivate(self, battle_map):
        logger.info(f"{self.combatants[0]}'s wildshape fades")
        self.combatants[0].current_wildshape_form = None
        self.combatants[0].has_action = self.form.has_action
        self.combatants[0].has_bonus_action = self.form.has_bonus_action
        self.combatants[0].has_haste_action = self.form.has_haste_action
        self.combatants[0].has_reaction = self.form.has_reaction
        self.combatants[0].is_concentrating = self.form.is_concentrating

    def enable(self, battle_map):
        self.combatants[0].current_wildshape_form = self.form
        self.form.has_action = self.combatants[0].has_action
        self.form.has_bonus_action = self.combatants[0].has_bonus_action
        self.form.has_haste_action = self.combatants[0].has_haste_action
        self.form.has_reaction = self.combatants[0].has_reaction

    def disable(self, battle_map):
        self.combatants[0].current_wildshape_form = None
        self.combatants[0].has_action = self.form.has_action
        self.combatants[0].has_bonus_action = self.form.has_bonus_action
        self.combatants[0].has_haste_action = self.form.has_haste_action
        self.combatants[0].has_reaction = self.form.has_reaction

    def clear_cache(self):
        pass

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        return self.form.max_hp - combatant.curr_hp

    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        return battle_map.get_all_accessible_coords(shortest_paths)

    def is_current_coord_eligible(self, battle_map):
        return True