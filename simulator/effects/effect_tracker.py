import logging

from simulator.abilities.wildshape import Wildshape
from simulator.effects.aoe_square_effect import AoeSquareEffect
from simulator.effects.post_haste_lethargy import PostHasteLethargy
from simulator.effects.aoe_spheric_effect import AoeSphericEffect

logger = logging.getLogger("EncounTroll")

class EffectTracker:
    """
    Manages all lasting effects.
    """
    def __init__(self):
        self.effects = []
        self.battle_map = None

    def add(self, effect):
        # TODO: Do I need the initiator? Every effect has a factory with a combatant
        # Refresh existing effect if available
        # for idx in range(len(self.effects)):
        #     if type(self.effects[idx][0]) == type(effect) and initiator is self.effects[idx][1]:
        #         logger.info(f"Refreshing {effect}")
        #         self.effects[idx][0] = effect
        #         break
        self.effects.append(effect)

    def remove(self, effect):
        self.effects.remove(effect)

    def start_of_turn(self, combatant):
        """
        Manages all effects with a fixed duration measurable in rounds which end just before the beginning of one of your turns.
        Also manages effects which can be saved against at the beginning of a combatant's turn.
        :return:
        """
        effects = []
        for e in self.effects:
            if getattr(e, "new_turn", False) and e.factory.combatant is combatant:
                if not e.new_turn():
                    continue  # Effect expired
            if getattr(e, "start_of_turn", False) and e.factory.combatant is combatant:
                if not e.start_of_turn():
                    continue  # Effect's been saved against
            effects.append(e)  # Effect persists
        self.effects = effects

    def end_of_turn(self, combatant):
        effects = []
        for e in self.effects:
            if getattr(e, "end_of_turn", False) and e.factory.combatant is combatant:
                if not e.end_of_turn():
                    continue
            effects.append(e)
        self.effects = effects

    def get_all_affecting_combatant(self, combatant):
        """
        Returns all effects affecting a combatant as a set
        :param combatant:
        :return: set of all effects affecting a combatant
        """
        return {e for e in self.effects if e.is_affecting(combatant)}

    def is_affecting_combatant(self, combatant, effect_type):
        """
        Determines whether a combatant is affected by an effect of a certain type
        :param combatant:
        :param effect_type: class of the effect
        :return: True if the combatant is affected, False otherwise
        """
        for e in self.effects:
            if type(e) is effect_type and e.is_affecting(combatant):
                return True
        return False

    def get_aoe_effects(self):
        return [e for e in self.effects if isinstance(e, AoeSquareEffect) or isinstance(e, AoeSphericEffect)]

    def get_effect_by_initiator(self, initiator):
        return [e for e in self.effects if e.factory.combatant is initiator]

    def combatant_died(self, combatant):
        self.effects = [e for e in self.effects if e.factory.combatant is not combatant]

    def create_post_haste_lethargy(self, combatant):
        self.effects.append((PostHasteLethargy(combatant), combatant))

# TODO add function for wildshape replacement

    def deactivate_wildshape(self, combatant):
        for e in self.effects:
            if e.is_affecting(combatant) and isinstance(e, Wildshape):
                e.deactivate()
                break  # There should only be one

    def reset(self):
        for effect in self.effects:
            effect.deactivate()
        self.effects.clear()