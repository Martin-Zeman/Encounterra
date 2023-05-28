import logging

from simulator.effects.aoe_square_effect import AoeSquareEffect
from simulator.effects.post_haste_lethargy import PostHasteLethargy
from simulator.effects.aoe_spheric_effect import AoeSphericEffect

logger = logging.getLogger("EncounTroll")

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
                if not e[0].new_turn(self.battle_map):
                    continue
            if getattr(e[0], "start_of_turn", False) and e[1] is combatant:
                if not e[0].start_of_turn(self.battle_map):
                    continue
            effects.append(e)
        self.effects = effects

    def end_of_turn(self, combatant):
        effects = []
        for e in self.effects:
            if getattr(e[0], "end_of_turn", False) and e[1] is combatant:
                if not e[0].end_of_turn(self.battle_map):
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

    def get_aoe_effects(self):
        return [e[0] for e in self.effects if isinstance(e[0], AoeSquareEffect) or isinstance(e[0], AoeSphericEffect)]

    def combatant_died(self, combatant):
        self.effects = [e for e in self.effects if e[1] is not combatant]

    def create_post_haste_lethargy(self, combatant):
        self.effects.append((PostHasteLethargy(combatant), combatant))

    def reset(self):
        logger.warning("Resetting effect tracker")
        for effect in self.effects:
            effect[0].deactivate(self.battle_map)
        self.effects.clear()