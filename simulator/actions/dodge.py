from simulator.actions.actoid import Actoid
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.action_types import BonusAction
from simulator.threat_calculator import ThreatModifier, FactoryThreat
from simulator.misc import SavingThrow, RollModifier
import logging

logger = logging.getLogger(__name__)

class DodgeFactory(FactoryThreat):

    def __init__(self, combatant):
        self.combatant = combatant
    def create_best(self, combatant, battle_map):
        return Dodge(combatant)

    def calculate_threat_mod_approx(self, combatant, battle_map, *args, **kwargs):
        return 0 # no need

    def calculate_threat_approx(self, battle_map, *args, **kwargs):
        """
        Calculate how much dmg would the dodge potentially mitigate. This will be the same as the one for the instance.
        """
        return 0


class Dodge(Actoid, CombatantEffect, LimitedDurationEffect, ThreatModifier):

    def __init__(self, combatant):
        Actoid.__init__(self, actoid_type=Actoid.Type.IS_DODGE)
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, rounds=1)

    def activate(self):
        self.combatant.is_dodging = True
        self.combatant.saving_throws[SavingThrow.DEX][1].append(RollModifier.ADVANTAGE)

    def deactivate(self):
        logger.debug(f"{self.combatants[0]}'s dodge fades")
        self.combatant.is_dodging = False
        self.combatant.saving_throws[SavingThrow.DEX][1].remove(RollModifier.ADVANTAGE)


    def calculate_threat_mod(self, combatant, battle_map, actions, *args, **kwargs):
        """
        Calculate how much dmg would the dodge potentially mitigate. This will be the same as the one for the factory.
        """
        # TODO
        return 0