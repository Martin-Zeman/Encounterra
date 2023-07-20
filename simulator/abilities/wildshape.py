import math
from functools import cache
import numpy as np
from simulator.actions.action_types import Action, BonusAction
from simulator.actions.actoid import Actoid, FactoryFlags
from simulator.battle_map import Map
from simulator.effects.action_enabler_effect import ActionEnablerEffect
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.effect import EffectType
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


    def create_all(self):
        # TODO Filter out those who cannot fit to the current position by size
        return self.combatant.available_wildshape_forms

    def create(self, form):
        # Doesn't make much sense here
        return Wildshape(self.combatant, form, self)

    @cache
    def calculate_threat(self, **kwargs):
        """
        Direct threat changes such as changes in HP. Doesn't account for newly added/lost action factories.
        """
        return max([hp for hp in self.combatant.available_wildshape_forms.curr_hp])

    def calculate_max_threat(self):
        return self.calculate_threat()

class Wildshape(Actoid, CombatantEffect, ActionEnablerEffect, DirectThreat):

    def __init__(self, combatant, form, factory):
        CombatantEffect.__init__(self, combatants=[combatant])
        self.form = form(f"{factory.combatant} wildshaped into {form.__name__}")
        def wildshape_get(self):
            return combatant

        self.form.get_original_form = wildshape_get.__get__(self, type(self.form))
        self.factory = factory

    def __str__(self):
        return f"Wildshape of {self.factory.combatant} into {self.form.__class__.__name__}"

    def get_effect_type(self):
        return EffectType.WILDSHAPE

    def activate(self):
        """
        Activation happens when the ability is selected and is being resolved.
        """
        battle_map = Map.get()
        battle_map.effect_tracker.add(self)
        logger.info(f"{self.combatants[0]} wildshapes into {self.form}")
        battle_map.teams.replace_combatant(self.combatants[0], self.form)
        wildshape_coord = battle_map.find_wildshaped_coordinate(self.combatants[0], self.form.size)
        battle_map.remove_combatant(self.combatants[0])
        battle_map.set_combatant_coordinates(self.form, np.array(wildshape_coord))
        self.combatants[0].current_wildshape_form = self.form
        self.form.curr_hp = self.form.max_hp
        self.form.movement = max(0, self.form.speed - (self.combatants[0].speed - self.combatants[0].movement))
        self.form.saving_throws[SavingThrow.INT] = self.combatants[0].saving_throws[SavingThrow.INT]
        self.form.saving_throws[SavingThrow.WIS] = self.combatants[0].saving_throws[SavingThrow.WIS]
        self.form.saving_throws[SavingThrow.CHA] = self.combatants[0].saving_throws[SavingThrow.CHA]
        self.form.has_action = self.combatants[0].has_action
        self.form.has_bonus_action = self.combatants[0].has_bonus_action
        self.form.has_haste_action = self.combatants[0].has_haste_action
        self.form.has_reaction = self.combatants[0].has_reaction
        self.form.concentration_effect = self.combatants[0].concentration_effect
        self.form.action_factories.extend([af for af in self.combatants[0].action_factories if FactoryFlags.TRANSITIONS_TO_WILDSHAPE in af[1].flags])
        self.form.bonus_action_factories.extend([baf for baf in self.combatants[0].bonus_action_factories if FactoryFlags.TRANSITIONS_TO_WILDSHAPE in baf[1].flags])
        self.form.haste_action_factories.extend([haf for haf in self.combatants[0].haste_action_factories if FactoryFlags.TRANSITIONS_TO_WILDSHAPE in haf[1].flags])
        for af in self.form.action_factories:
            af[1].combatant = self.form
        for baf in self.form.bonus_action_factories:
            baf[1].combatant = self.form
        for haf in self.form.haste_action_factories:
            haf[1].combatant = self.form
        # TODO add function for wildshape replacement for effect tracker


    def deactivate(self):
        """
        Activation happens when the ability is either cancelled (loss of concentration) or expires
        """
        battle_map = Map.get()
        logger.info(f"{self.combatants[0]}'s wildshape fades")
        self.combatants[0].current_wildshape_form.on_die()
        battle_map.teams.replace_combatant(self.combatants[0].current_wildshape_form, self.combatants[0])
        position = battle_map.get_combatant_position(self.combatants[0].current_wildshape_form)
        battle_map.remove_combatant(self.combatants[0].current_wildshape_form)
        battle_map.set_combatant_coordinates(self.combatants[0], position.get()[0])
        self.combatants[0].movement = min(self.combatants[0].speed, self.combatants[0].current_wildshape_form.movement)
        self.combatants[0].current_wildshape_form = None
        self.combatants[0].has_action = self.form.has_action
        self.combatants[0].has_bonus_action = self.form.has_bonus_action
        self.combatants[0].has_haste_action = self.form.has_haste_action
        self.combatants[0].has_reaction = self.form.has_reaction
        # Remove the extra factories from the form, it may be reused again  TODO: do I really need this?
        self.form.action_factories = [af for af in self.form.action_factories if FactoryFlags.TRANSITIONS_TO_WILDSHAPE not in af[1].flags]
        self.form.bonus_action_factories = [baf for baf in self.form.bonus_action_factories if FactoryFlags.TRANSITIONS_TO_WILDSHAPE not in baf[1].flags]
        self.form.haste_action_factories = [haf for haf in self.form.haste_action_factories if FactoryFlags.TRANSITIONS_TO_WILDSHAPE not in haf[1].flags]
        for af in self.combatants[0].action_factories:
            af[1].combatant = self.combatants[0]
        for baf in self.combatants[0].bonus_action_factories:
            baf[1].combatant = self.combatants[0]
        for haf in self.combatants[0].haste_action_factories:
            haf[1].combatant = self.combatants[0]
        # TODO add function for wildshape replacement for effect tracker


    def enable(self):
        """
        Enabling happens when the ability is being explored during action FSM creation as an action enabler.
        """
        self.combatants[0].current_wildshape_form = self.form
        self.form.has_action = self.combatants[0].has_action
        self.form.has_bonus_action = self.combatants[0].has_bonus_action
        self.form.has_haste_action = self.combatants[0].has_haste_action
        self.form.has_reaction = self.combatants[0].has_reaction
        self.form.action_factories.extend([af for af in self.combatants[0].action_factories if FactoryFlags.TRANSITIONS_TO_WILDSHAPE in af[1].flags])
        self.form.bonus_action_factories.extend([baf for baf in self.combatants[0].bonus_action_factories if FactoryFlags.TRANSITIONS_TO_WILDSHAPE in baf[1].flags])
        self.form.haste_action_factories.extend([haf for haf in self.combatants[0].haste_action_factories if FactoryFlags.TRANSITIONS_TO_WILDSHAPE in haf[1].flags])
        for af in self.form.action_factories:
            af[1].combatant = self.form
        for baf in self.form.bonus_action_factories:
            baf[1].combatant = self.form
        for haf in self.form.haste_action_factories:
            haf[1].combatant = self.form

    def disable(self):
        """
        Disabling happens when the ability is finished being explored during action FSM creation as an action enabler.
        """
        self.combatants[0].current_wildshape_form = None
        self.combatants[0].has_action = self.form.has_action
        self.combatants[0].has_bonus_action = self.form.has_bonus_action
        self.combatants[0].has_haste_action = self.form.has_haste_action
        self.combatants[0].has_reaction = self.form.has_reaction
        self.form.action_factories = [af for af in self.form.action_factories if FactoryFlags.TRANSITIONS_TO_WILDSHAPE not in af[1].flags]
        self.form.bonus_action_factories = [baf for baf in self.form.bonus_action_factories if FactoryFlags.TRANSITIONS_TO_WILDSHAPE not in baf[1].flags]
        self.form.haste_action_factories = [haf for haf in self.form.haste_action_factories if FactoryFlags.TRANSITIONS_TO_WILDSHAPE not in haf[1].flags]
        for af in self.combatants[0].action_factories:
            af[1].combatant = self.combatants[0]
        for baf in self.combatants[0].bonus_action_factories:
            baf[1].combatant = self.combatants[0]
        for haf in self.combatants[0].haste_action_factories:
            haf[1].combatant = self.combatants[0]

    @cache
    def calculate_threat(self, **kwargs):
        return self.form.max_hp# * random.uniform(0.8, 1.20)  # We try to encourage trying out different wildshape forms

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0

    def get_eligible_coords(self, distances, shortest_paths):
        """
        Computes a list of coordinates that are eligible for wildshape but then reduces it down to those with a distance to the combatant
        equal to the minimum eligible distance.
        :param distances: the distances to all squares (result of Dijkstra)
        :param shortest_paths: the shortest paths to all squares (result of Dijkstra)
        :return: eligible coordinates
        """
        battle_map = Map.get()
        map_accessibility_matrix = np.zeros((battle_map.size, battle_map.size))
        for coord in shortest_paths.keys():
            map_accessibility_matrix[coord] = 1
        original_coordinate = battle_map.get_combatant_position(self.factory.combatant).get()[0]
        map_accessibility_matrix[original_coordinate[0], original_coordinate[1]] = 1
        map_accessibility_matrix = np.transpose(map_accessibility_matrix)
        wilshape_size_increment = self.form.size.value
        result_matrix = np.zeros((battle_map.size, battle_map.size))

        for col in range(battle_map.size - wilshape_size_increment):
            for row in range(battle_map.size - wilshape_size_increment):
                submatrix = map_accessibility_matrix[row:row + wilshape_size_increment + 1, col:col + wilshape_size_increment + 1]
                if np.all(submatrix > 0):
                    result_matrix[col, row] = 1  # Take care that axes are swapped here
        # Here we're only interested in the coords with the lowest distance from the original coordinate
        all_coords = np.argwhere(result_matrix == 1).tolist()
        all_coords.sort(key=lambda coord: distances[coord[0] * battle_map.size + coord[1]])
        final_coords = []
        curr_coord = all_coords[0]
        min_distance = distances[curr_coord[0] * battle_map.size + curr_coord[1]]
        curr_distance = min_distance
        idx = 1
        while curr_distance == min_distance:
            final_coords.append(tuple(curr_coord))
            curr_coord = all_coords[idx]
            curr_distance = distances[curr_coord[0] * battle_map.size + curr_coord[1]]
            idx += 1
        return final_coords

    def is_current_coord_eligible(self):
        return True if Map.get().find_wildshaped_coordinate(self.factory.combatant, self.form.size) else False
