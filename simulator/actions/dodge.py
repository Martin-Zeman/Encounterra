from simulator.action_types import Action
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.threat import calculate_threat_in_mod
from simulator.threat_calculator import ThreatModifier, ThreatModifierFactory
from simulator.misc import SavingThrow
import logging

from simulator.utils.roll_modifiers import RollModifier

logger = logging.getLogger(__name__)

class DodgeFactory(ThreatModifierFactory):

    def __init__(self, combatant):
        super().__init__()
        self.combatant = combatant
        self.action_type = Action.DODGE

    def __str__(self):
        """
        Important for FSM building
        """
        return "DodgeFactory"

    def create_best(self, combatant, battle_map):
        return Dodge(combatant, self)

    def create_mock(self):
        return Dodge(None, self)

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        Calculates the maximum threat reduction the factory can cause by imposing disadvantage on the target enemy
        """
        # The target is irrelevant here
        return -1 * calculate_threat_in_mod(self.combatant, 6, battle_map, RollModifier.DISADVANTAGE, FactoryFlags.IS_ATTACK_LIKE | FactoryFlags.DEX_SAVE_APPLIES) / 2

    def calculate_threat_to_target_using_attack(self, battle_map, target, attack_factory, *args, **kwargs):
        return 0


class Dodge(Actoid, CombatantEffect, LimitedDurationEffect, ThreatModifier):

    def __init__(self, combatant, factory):
        Actoid.__init__(self, actoid_type=ActoidFlags.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, turns=1)
        self.factory = factory

    def activate(self):
        self.combatants[0].is_dodging = True
        self.combatants[0].saving_throws_roll_mod[SavingThrow.DEX].add(RollModifier.ADVANTAGE)

    def deactivate(self):
        logger.info(f"{self.combatants[0]}'s dodge fades")
        self.combatants[0].is_dodging = False
        try:
            self.combatants[0].saving_throws_roll_mod[SavingThrow.DEX].remove(RollModifier.ADVANTAGE)
        except KeyError:
            pass  # may not be present if called by reset


    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        """
        Calculate how much dmg would the dodge potentially mitigate. This will be the same as the one for the factory.
        """
        return -1 * calculate_threat_in_mod(combatant, 6, battle_map, RollModifier.DISADVANTAGE, FactoryFlags.IS_ATTACK_LIKE | FactoryFlags.DEX_SAVE_APPLIES) / 2