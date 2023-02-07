from functools import reduce

from simulator.actions.actoid import Actoid
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.action_types import BonusAction
from simulator.threat_calculator import ThreatModifier, FactoryThreat
from simulator.misc import SavingThrow, RollModifier
import logging

logger = logging.getLogger(__name__)

class DisengageFactory(FactoryThreat):

    def __init__(self, combatant, action_type):
        self.combatant = combatant
        self.action_type = action_type  # DISENGAGE, CUNNING DISENGAGE

    def create_best(self, combatant, battle_map):
        return Disengage(combatant, self)


    def calculate_threat_approx_mod(self, battle_map, modified_stats, *args, **kwargs):
        """
        Calculates the threat delta of the factory given stat modifications. This is a general estimation with no specific target.
        This is useful for evaluation the threat_out of (de)buff abilities. It's meant to be called from the threat calculation methods
        of (de)buff abilities.
        """
        return 0 # no need

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        Calculates the direct AoO threat the disengage would avoid
        """
        return target.aoo_factory[1].calculate_threat_to_target(battle_map, self.combatant)

    def calculate_threat_to_target_mod(self, battle_map, target, modified_stats, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications.
        This is useful calculating the potential reduction of threat_in caused by abilities of enemies, e.g. advantage on saving throw
        against fireball or bane on attack rolls etc.
        """
        return 0 # no need


class Disengage(Actoid, CombatantEffect, LimitedDurationEffect, ThreatModifier):

    def __init__(self, combatant, factory):
        Actoid.__init__(self, actoid_type=Actoid.Type.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, rounds=1)
        self.factory = factory

    def activate(self):
        self.factory.combatant.has_disengaged = True

    def deactivate(self):
        logger.debug(f"{self.combatants[0]}'s disengage fades")
        self.factory.combatant.has_disengaged = False


    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        """
        Calculate how much dmg would the disengage potentially mitigate. This will be the same as the one for the factory.
        """
        adjacent_enemies = battle_map.get_adjacent_enemies(combatant)
        return reduce(lambda acc, ae: ae.aoo_factory[1].calculate_threat_to_target(battle_map, self.combatant), adjacent_enemies)