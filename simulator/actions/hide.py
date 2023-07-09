from functools import cache

from simulator.actions.action_types import HasteAction, BonusAction
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.battle_map import Map
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.effect import EffectType
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.threat_interfaces import ThreatModifier, ThreatModifierFactory
import logging

logger = logging.getLogger("EncounTroll")

class HideFactory(ThreatModifierFactory):

    def __init__(self, action_type, combatant):
        super().__init__()
        self.combatant = combatant
        self.action_type = action_type  # DISENGAGE, CUNNING_DISENGAGE

    def __str__(self):
        """
        Important for FSM building
        """
        return "DisengageFactory"

    def get_kwargs(self):
        return {'combatant': self.combatant, 'action_type': self.action_type}

    def create_all(self):
        return [Hide(self.combatant, self)]

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates the direct AoO threat the disengage would avoid
        """
        return 0  # TODO


class Hide(Actoid, CombatantEffect, ThreatModifier):

    def __init__(self, combatant, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[combatant])
        self.factory = factory

    def get_effect_type(self):
        return EffectType.HIDE

    def __str__(self):
        prefix = ""
        if self.factory.action_type is BonusAction.CUNNING_HIDE:
            prefix = "Cunning "
        elif self.factory.action_type is HasteAction.HASTE_HIDE:
            prefix = "Hasted "
        return prefix + f"Hide of {self.factory.combatant}"

    def shorthand_str(self):
        prefix = ""
        if self.factory.action_type is BonusAction.CUNNING_HIDE:
            prefix = "Cunning "
        elif self.factory.action_type is HasteAction.HASTE_HIDE:
            prefix = "Hasted "
        return prefix + f"Hide"

    def activate(self):
        logger.info(f"{self.combatants[0]} attempts to hide")
        self.factory.combatant.has_disengaged = True

    def deactivate(self):
        logger.info(f"{self.combatants[0]} is no longer hidden")
        self.factory.combatant.has_disengaged = False


    def calculate_threat(self, **kwargs):
        """
        Calculate how much dmg would the Disengage potentially mitigate. This will be the same as the one for the factory.
        """
        return 0  # TODO account for the potential sneak attack + advantage

    def get_eligible_coords(self, distances, shortest_paths):
        # TODO Find a hiding spot
        battle_map = Map.get()
        # return None  # We don't want to have any coords pre-pended in the DAG
        return battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)

    def is_current_coord_eligible(self):
        # TODO is this a hiding spot
        return True