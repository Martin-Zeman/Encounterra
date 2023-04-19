from functools import reduce

from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.action_types import BonusAction
from simulator.threat_calculator import ThreatModifier, ThreatModifierFactory
from simulator.misc import SavingThrow, RollModifier
import logging

logger = logging.getLogger(__name__)

class DisengageFactory(ThreatModifierFactory):

    def __init__(self, combatant, action_type):
        super().__init__()
        self.combatant = combatant
        self.action_type = action_type  # DISENGAGE, CUNNING DISENGAGE

    # def __str__(self):
    #     """
    #     Important for FSM building
    #     """
    #     return "DisengageFactory"

    def create_best(self, combatant, battle_map):
        return Disengage(combatant, self)

    # def create_mock(self):
    #     return Disengage(None, self)

    def create_all(self, battle_map):
        return [Disengage(self.combatant, self)]

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        Calculates the direct AoO threat the disengage would avoid
        """
        return target.aoo_factory[1].calculate_threat_to_target(battle_map, self.combatant)

    def calculate_threat_to_target_using_attack(self, battle_map, target, attack_factory, *args, **kwargs):
        return 0



class Disengage(Actoid, CombatantEffect, LimitedDurationEffect, ThreatModifier):

    def __init__(self, combatant, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, turns=1)
        self.actoid_flags |= ActoidFlags.IS_POSITIONING_INDEPENDENT
        self.factory = factory

    def __str__(self):
        return f"Disengage of {self.factory.combatant}"

    def activate(self):
        self.factory.combatant.has_disengaged = True

    def deactivate(self):
        logger.info(f"{self.combatants[0]}'s disengage fades")
        self.factory.combatant.has_disengaged = False


    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        """
        Calculate how much dmg would the disengage potentially mitigate. This will be the same as the one for the factory.
        """
        adjacent_enemies = battle_map.get_adjacent_enemies(combatant)
        return reduce(lambda acc, ae: ae.aoo_factory[1].calculate_threat_to_target(battle_map, self.combatant), adjacent_enemies, 0)

    def get_eligible_coords(self, battle_map, shortest_paths):
        return None  # We don't want to have any coords pre-pended in the DAG
        # return battle_map.get_all_accessible_coords(shortest_paths)