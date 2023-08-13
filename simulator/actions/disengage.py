from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from simulator.actions.action_types import HasteAction, BonusAction
from simulator.actions.actoid import Actoid, FactoryFlags
from simulator.battle_map import Map, map_toggled_cache_with_key
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.effect import EffectType
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.misc import Conditions
from simulator.threat_interfaces import ThreatModifierFactory, Threat
import logging

logger = logging.getLogger("Encounterra")

class DisengageFactory(ThreatModifierFactory):

    def __init__(self, action_type, combatant):
        super().__init__()
        self.combatant = combatant
        self.action_type = action_type  # DISENGAGE, CUNNING_DISENGAGE
        self.flags |= FactoryFlags.DEFAULT

    def __str__(self):
        """
        Important for FSM building
        """
        return "DisengageFactory"

    def get_kwargs(self):
        return {'combatant': self.combatant, 'action_type': self.action_type}

    def create_all(self):
        return [Disengage(self.combatant, self)]

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates the direct AoO threat the disengage would avoid
        """
        return target.aoo_factory[1].calculate_threat_to_target(self.combatant)


class Disengage(Actoid, CombatantEffect, LimitedDurationEffect, Threat):

    def __init__(self, combatant, factory):
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, turns=1)
        self.factory = factory

    def get_effect_type(self):
        return EffectType.DISENGAGE

    def __str__(self):
        prefix = ""
        if isinstance(self.factory.action_type, HasteAction):
            prefix = "Hasted "
        elif self.factory.action_type is BonusAction.CUNNING_DISENGAGE:
            prefix = "Cunning "
        return prefix + f"Disengage of {self.factory.combatant}"

    def shorthand_str(self):
        prefix = ""
        if isinstance(self.factory.action_type, HasteAction):
            prefix = "Hasted "
        elif self.factory.action_type is BonusAction.CUNNING_DISENGAGE:
            prefix = "Cunning "
        return prefix + f"Disengage"

    def activate(self):
        logger.info(f"{self.combatants[0]} disengages")
        self.factory.combatant.has_disengaged = True

    def deactivate(self):
        logger.info(f"{self.combatants[0]}'s disengage fades")
        self.factory.combatant.has_disengaged = False

    def calculate_threat(self, **kwargs):
        """
        Calculate how much dmg would the Disengage potentially mitigate. This will be the same as the one for the factory.
        """
        return 0  # It's included in the accumulate_threat_along_path calculation

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED, Conditions.SWALLOWED) \
                or self.factory.combatant.movement == 0:
            return None  # Disenaging makes no sense if you can't move
        return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]  # It's a priority action, the coord is not relevant
