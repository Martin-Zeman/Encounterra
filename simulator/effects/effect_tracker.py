import logging
import numpy as np

from simulator.combatant_coords import CombatantCoords
from simulator.effects.aoe_square_effect import AoeSquareEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.effects.post_haste_lethargy import PostHasteLethargy
from simulator.effects.aoe_spheric_effect import AoeSphericEffect

logger = logging.getLogger(__name__)

class EffectTracker:
    """
    TODO: Could be the class that takes care of exceptional removal of effects (such as rage)
    """
    def __init__(self):
        self.effects = []
        self.battle_map = None

    def set_battle_map(self, battle_map):
        self.battle_map = battle_map

    def add(self, effect, originator):
        # TODO: Do I need the originator?
        self.effects.append((effect, originator))

    def new_turn(self, combatant):
        """
        Manages all effects with a fixed duration measurable in rounds which end just before the beginning of one of your turns.
        Also manages effects which can be saved against at the beginning of a combatant's turn.
        :return:
        """
        effects = []
        for e in self.effects:
            if getattr(e[0], "new_turn", False) and e[1] is combatant:
                if not e[0].new_turn():
                    continue
            if getattr(e[0], "start_of_turn", False) and e[1] is combatant:
                if not e[0].start_of_turn():
                    continue
            effects.append(e)
        self.effects = effects

    def end_of_turn(self, combatant):
        effects = []
        for e in self.effects:
            if getattr(e[0], "end_of_turn", False) and e[1] is combatant:
                if not e[0].end_of_turn():
                    continue
            effects.append(e)
        self.effects = effects

    def get_all_affecting_combatant(self, combatant):
        """
        Returns all effects affecting a combatant as a set
        :param combatant:
        :return: set of all effects affecting a combatant
        """
        return {e[0] for e in self.effects if e[0].is_affecting(combatant, self.battle_map)}

    def is_affecting_combatant(self, combatant, effect_type):
        """
        Determines whether a combatant is affected by an effect of a certain type
        :param combatant:
        :param effect_type: class of the effect
        :return: True if the combatant is affected, False otherwise
        """
        for e in self.effects:
            if type(e[0]) is effect_type and e[0].is_affecting(combatant, self.battle_map):
                return True
        return False

    # def get_all_affecting_coords(self, coords: CombatantCoords):
    #     """
    #     Returns all effects affecting a given coordinate
    #     :param coord: coordinate in question
    #     :return: set of all effects affecting a combatant
    #     """
    #     assert self.battle_map
    #     affecting = []
    #     for e in self.effects:
    #         if isinstance(e[0], AoeSquareEffect) and do_squares_overlap(e[0].origin, e[0].length, coords.get()[0], coords.size.value + 1):
    #             affecting.append(e)
    #         elif isinstance(e[0], AoeSphericEffect) and self.battle_map.get_cartesian_distance(coords, np.array([e[0].coord])) <= e[0].radius:
    #             affecting.append(e)
    #     return affecting

    # def get_aoe_coord_to_threat(self, combatant):
    #     """
    #     Returns all effects affecting a given coordinate
    #     :param combatant: the combatant who wants to move
    #     :return: a dictionary of coords -> (threat, source effect) asociated with the combatant entering that coord or staying there
    #     """
    #     coord_to_threat = dict()
    #     def add_to_coord_to_threat(coords, effect):
    #         threat = effect.factory.calculate_threat_to_target(self.battle_map, combatant)
    #         for coord in coords:
    #             try:
    #                 coord_to_threat[coord].append((threat, effect))
    #             except TypeError:
    #                 coord_to_threat[coord] = [(threat, effect)]
    #
    #
    #     for e in self.effects:
    #         if isinstance(e[0], AoeSquareEffect):
    #             coords = get_affected_by_square(e[0].origin, e[0].length, self.battle_map.size)
    #         elif isinstance(e[0], AoeSphericEffect):
    #             coords = get_affected_by_sphere(e[0].origin, e[0].radius, self.battle_map.size)
    #         else:
    #             continue
    #         add_to_coord_to_threat(coords, e[0])
    #     return coord_to_threat

    def get_aoe_effects(self):
        return [e[0] for e in self.effects if isinstance(e[0], AoeSquareEffect) or isinstance(e[0], AoeSphericEffect)]




    def combatant_died(self, combatant):
        self.effects = [e for e in self.effects if e[1] is not combatant]

    def create_post_haste_lethargy(self, combatant):
        self.effects.append((PostHasteLethargy(combatant), combatant))

    def reset(self):
        logger.info("Resetting effect tracker")
        for effect in self.effects:
            effect[0].deactivate()
        self.effects.clear()