import logging

from ..effects.aoe_square_effect import AoeSquareEffect
from ..effects.effect import EffectType
from ..effects.post_haste_lethargy_effect import PostHasteLethargyEffect
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
        effect.deactivate()
        self.effects.remove(effect)

    def start_of_turn_tick(self, combatant):
        """
        Manages all effects with a fixed duration measurable in rounds which end just before the beginning of combatant's turn.
        :param combatant: the initiating combatant
        :return:
        """
        effects = []
        for e in self.effects:
            if e.initiator is combatant:
                try:
                    keep = e.start_of_turn_tick()
                    if not keep:
                        e.deactivate()
                        continue  # Effect expired
                except AttributeError:  # This skips
                    pass
            effects.append(e)  # Effect persists
        self.effects = effects

    def start_of_turn(self, combatant):
        """
        Manages effects which take effect at the start of a combatant's turn.
        Also manages effects that can be saved against at the start of a combatant's turn.
        :param combatant: the affected combatant
        :return:
        """
        effects = []
        for e in self.effects:
            if e.is_affecting(combatant):
                if not e.start_of_turn_for_combatant(combatant):
                    e.deactivate_for_combatant(combatant)  # TODO: at the moment this does nothing (regeneration and digestion only)
                    continue  # Effect's been cancelled
            effects.append(e)  # Effect persists
        self.effects = effects

    def end_of_turn(self, combatant):
        effects = []
        for e in self.effects:
            if e.is_affecting(combatant):
                if not e.combatant_saved_at_end_of_turn(combatant):
                    if not e.deactivate_for_combatant(combatant):
                        continue  # Effect's been saved against or somehow ceased on all combatants -> can be removed
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
        self.effects.append(PostHasteLethargyEffect(initiator, combatant))

# TODO add function for wildshape replacement

    def remove_effect_from_combatant_by_type(self, combatant, effect_type):
        effects = []
        for e in self.effects:
            if e.is_affecting(combatant) and e.get_effect_type() is effect_type:
                if not e.deactivate_for_combatant(combatant):
                    continue
            effects.append(e)
        self.effects = effects

    def remove_effect_from_combatant(self, combatant, effect):
        if not effect.deactivate_for_combatant(combatant):
            self.effects.remove(effect)

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

    def is_affected_by_vow_of_enmity(self, initiator, target):
        for e in self.get_effects_by_initiator(initiator):
            if e.get_effect_type() is EffectType.VOW_OF_ENMITY and e.combatants[0] is target:
                return True
        return False

    def reset(self):
        for effect in self.effects:
            effect.deactivate()
        self.effects.clear()
