import logging

from ..effects.aoe_square_effect import AoeSquareEffect
from ..effects.effect import EffectType
from ..effects.post_haste_lethargy import PostHasteLethargy
from ..effects.aoe_spheric_effect import AoeSphericEffect

logger = logging.getLogger("Encounterra")

class EffectTracker:
    """
    Manages all lasting effects.
    """
    def __init__(self):
        self.effects = []
        self.battle_map = None

    def add(self, effect):
        self.effects.append(effect)

    def remove(self, effect):
        try:
            effect.deactivate()
            self.effects.remove(effect)
        except ValueError:
            print("FIXME")

    def start_of_turn(self, combatant):
        """
        Manages all effects with a fixed duration measurable in rounds which end just before the beginning of combatant's turn.
        Also manages effects which can be saved against at the beginning of a combatant's turn.
        :return:
        """
        effects = []
        for e in self.effects:
            if getattr(e, "target", None) is combatant or combatant in getattr(e, "targets", []):
                if not e.new_turn():
                    e.deactivate()
                    continue  # Effect expired
                if not e.start_of_turn():
                    e.deactivate()
                    continue  # Effect's been saved against
            effects.append(e)  # Effect persists
        self.effects = effects

    def end_of_turn(self, combatant):
        effects = []
        for e in self.effects:
            if getattr(e, "target", None) is combatant or combatant in getattr(e, "targets", []):
                if not e.end_of_turn():
                    e.deactivate()
                    continue  # Effect's been saved against
            effects.append(e)
        self.effects = effects

    def get_affecting_combatant(self, combatant):
        """
        Returns a set of all effects affecting a combatant
        :param combatant: the combatant
        :return:  set of all effects affecting the combatant
        """
        try:
            return {e for e in self.effects if e.is_affecting(combatant)}
        except AttributeError:
            print("FIXME")

    def is_affecting_combatant(self, combatant, effect_type):
        """
        Determines whether a combatant is affected by an effect of a certain type
        :param combatant:
        :param effect_type: EffectType enum
        :return: True if the combatant is affected, False otherwise
        """
        for e in self.effects:
            if e.get_effect_type() is effect_type and e.is_affecting(combatant):
                return True
        return False

    def get_aoe_effects(self):
        return [e for e in self.effects if isinstance(e, AoeSquareEffect) or isinstance(e, AoeSphericEffect)]

    def get_effects_by_initiator(self, initiator):
        return [e for e in self.effects if e.initiator is initiator]

    def combatant_died(self, combatant):
        for e in self.get_effects_by_initiator(combatant):
            e.deactivate()
        self.effects = [e for e in self.effects if e.initiator is not combatant]

    def create_post_haste_lethargy(self, initiator, combatant):
        self.effects.append(PostHasteLethargy(initiator, combatant))

# TODO add function for wildshape replacement

    def remove_effect_by_type(self, combatant, type):
        effects = []
        for e in self.effects:
            if e.is_affecting(combatant) and e.get_effect_type() is type:
                e.deactivate()
            else:
                effects.append(e)
        self.effects = effects

    def is_combatant_hidden_from(self, combatant, target):
        """

        :param combatant: the hiding combatant
        :param target: the one hiding from
        :return: True if the combatant is hidden from target
        """
        for e in self.get_effects_by_initiator(combatant):
            if e.get_effect_type() is EffectType.HIDE and e.target is target:
                return True
        return False

    def reset(self):
        for effect in self.effects:
            try:
                effect.deactivate()
            except AttributeError:
                print("FIXME")
        self.effects.clear()