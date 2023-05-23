from functools import cache

from simulator.actions.action_types import HasteAction
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.threat_interfaces import ThreatModifier, ThreatModifierFactory
import logging

logger = logging.getLogger("EncounTroll")

class DisengageFactory(ThreatModifierFactory):

    def __init__(self, combatant, action_type):
        super().__init__()
        self.combatant = combatant
        self.action_type = action_type  # DISENGAGE, CUNNING DISENGAGE

    def __str__(self):
        """
        Important for FSM building
        """
        return "DisengageFactory"

    def get_kwargs(self):
        return {'combatant': self.combatant, 'action_type': self.action_type}

    def create_best(self, combatant, battle_map):
        return Disengage(combatant, self)

    def create_all(self, battle_map):
        return [Disengage(self.combatant, self)]

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        Calculates the direct AoO threat the disengage would avoid
        """
        return target.aoo_factory[1].calculate_threat_to_target(battle_map, self.combatant)


class Disengage(Actoid, CombatantEffect, LimitedDurationEffect, ThreatModifier):

    def __init__(self, combatant, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, turns=1)
        self.actoid_flags |= ActoidFlags.IS_POSITIONING_INDEPENDENT
        self.factory = factory

    def __str__(self):
        return ("Hasted " if isinstance(self.factory.action_type, HasteAction) else "") + f"Disengage of {self.factory.combatant}"

    def activate(self, battle_map):
        self.factory.combatant.has_disengaged = True

    def deactivate(self, battle_map):
        logger.info(f"{self.combatants[0]}'s disengage fades")
        self.factory.combatant.has_disengaged = False


    def clear_cache(self):
        self.calculate_threat.cache_clear()

    @cache
    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        """
        Calculate how much dmg would the Disengage potentially mitigate. This will be the same as the one for the factory.
        """
        # adjacent_enemies = battle_map.get_adjacent_enemies(combatant)
        # return reduce(lambda acc, ae: ae.aoo_factory[1].calculate_threat_to_target(battle_map, combatant), adjacent_enemies, 0)
        return 0  # Threat that a Disengage would potentially mitigate is calculated in a different way

    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        return None  # We don't want to have any coords pre-pended in the DAG
        # return battle_map.get_all_accessible_coords(shortest_paths)

    def is_current_coord_eligible(self, battle_map):
        return True