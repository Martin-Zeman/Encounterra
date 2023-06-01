import math

import numpy as np

from simulator.actions.action_types import Action, BonusAction
from simulator.actions.actoid import Actoid, ActoidFlags, FactoryFlags
from simulator.effects.action_enabler_effect import ActionEnablerEffect
from simulator.effects.combatant_effect import CombatantEffect
from simulator.misc import SavingThrow, Size

from simulator.threat_interfaces import TransformerFactory, DirectThreat
import logging

logger = logging.getLogger("EncounTroll")


class WildshapeFactory(TransformerFactory):

    def __init__(self, combatant, action_type):
        TransformerFactory.__init__(self)
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
    def get_wildshape_form_sizes(level, action_type):
        if action_type is Action.WILDSHAPE:
            return [Size.LARGE]
        elif action_type is BonusAction.MOON_WILDSHAPE:
            match level:
                case lvl if 2 <= lvl <= 5:
                    return [Size.LARGE]
                case lvl if 6 <= lvl <= 8:
                    return [Size.LARGE, Size.HUGE]
                case lvl if 9 <= lvl <= 11:
                    return [Size.LARGE, Size.HUGE]
                case lvl if 12 <= lvl <= 14:
                    return [Size.LARGE, Size.HUGE]
                case lvl if 15 <= lvl <= 17:
                    return [Size.LARGE, Size.HUGE]
                case lvl if 18 <= lvl <= 20:
                    return [Size.LARGE, Size.HUGE]
                case _:
                    logger.error("Incorrect character level. No wildshape forms added!")


    def create_all(self, battle_map):
        # TODO Filter out those who cannot fit to the current position by size
        return self.combatant.available_wildshape_forms

    def create(self, form):
        # Doesn't make much sense here
        return Wildshape(self.combatant, form, self)

    def calculate_threat(self, battle_map, *args, **kwargs):
        """
        Direct threat changes such as changes in HP. Doesn't account for newly added/lost action factories.
        """
        return max([hp for hp in self.combatant.available_wildshape_forms.curr_hp])

class Wildshape(Actoid, CombatantEffect, ActionEnablerEffect, DirectThreat):

    def __init__(self, combatant, form, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[combatant])
        self.actoid_flags |= ActoidFlags.IS_POSITIONING_INDEPENDENT
        self.form = form(factory.combatant.effect_tracker, f"{factory.combatant} wildshaped into {form.__name__}")
        def wildshape_get(self):
            return combatant

        self.form.get_original_form = wildshape_get.__get__(self, type(self.form))
        self.factory = factory

    def __str__(self):
        return f"Wildshape of {self.factory.combatant} into {self.form.__class__.__name__}"

    def activate(self, battle_map):
        logger.info(f"{self.combatants[0]} wildshapes into {self.form}")
        #


        battle_map.teams.replace_combatant(self.combatants[0], self.form)
        position = battle_map.get_combatant_position(self.combatants[0])
        battle_map.remove_combatant(self.combatants[0])
        battle_map.set_combatant_coordinates(self.form, position.get()[0])
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
        # TODO add function for wildshape replacement for effect tracker


    def deactivate(self, battle_map):
        logger.info(f"{self.combatants[0]}'s wildshape fades")
        battle_map.teams.replace_combatant(self.combatants[0].current_wildshape_form, self.combatants[0])
        position = battle_map.get_combatant_position(self.combatants[0].current_wildshape_form)
        battle_map.remove_combatant(self.combatants[0].current_wildshape_form)
        battle_map.set_combatant_coordinates(self.combatants[0], position.get()[0])
        self.combatants[0].current_wildshape_form = None
        self.combatants[0].has_action = self.form.has_action
        self.combatants[0].has_bonus_action = self.form.has_bonus_action
        self.combatants[0].has_haste_action = self.form.has_haste_action
        self.combatants[0].has_reaction = self.form.has_reaction
        self.combatants[0].is_concentrating = self.form.is_concentrating
        # TODO add function for wildshape replacement for effect tracker


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
        return self.form.max_hp

    def calculate_threat_delta(self, battle_map, modified_stats, *args, **kwargs):
        return 0

    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        # Find all the places on the map where the wildshape form will fit
        map_accessibility_matrix = np.zeros(battle_map.size, battle_map.size)
        for coord in shortest_paths.keys():
            map_accessibility_matrix[coord] = 1
        wilshape_matrix = np.ones((self.form.size.value() + 1, self.form.size.value() + 1))
        wilshape_matrix_shape = wilshape_matrix.shape
        result_matrix = np.zeros(battle_map.size)

        for i in range(battle_map.size - wilshape_matrix_shape[0] + 1):
            for j in range(battle_map.size - wilshape_matrix_shape[1] + 1):
                submatrix = map_accessibility_matrix[i:i + wilshape_matrix_shape[0], j:j + wilshape_matrix_shape[1]]
                subproduct = submatrix * wilshape_matrix
                if np.all(subproduct > 0):
                    result_matrix[i:i + wilshape_matrix_shape[0], j:j + wilshape_matrix_shape[1]] = 1
        coords = np.argwhere(result_matrix == 1)
        return {c for c in coords if c in shortest_paths.keys()}

    def is_current_coord_eligible(self, battle_map):
        return True