from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.action_types import BonusAction
from simulator.threat_calculator import ThreatModifier, ThreatModifierFactory, DirectThreatFactory
from simulator.misc import SavingThrow, RollModifier
import logging

logger = logging.getLogger(__name__)

class DodgeFactory(ThreatModifierFactory):

    def __init__(self, combatant):
        super().__init__()
        self.combatant = combatant
    def create_best(self, combatant, battle_map):
        return Dodge(combatant)

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        Calculates the maximum threat reduction the factory can cause by imposing disadvantage on the target enemy
        """
        max_threat = 0
        for af in target.action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in af.flags:
                threat_mod = af[1].calculate_threat_to_target_mod(battle_map, self.combatant, {"roll_modifier": RollModifier.DISADVANTAGE})
                max_threat = max(max_threat, threat_mod)
        for af in target.bonus_action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in af.flags:
                threat_mod = af[1].calculate_threat_to_target_mod(battle_map, self.combatant, {"roll_modifier": RollModifier.DISADVANTAGE})
                max_threat = max(max_threat, threat_mod)
        for af in target.haste_action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in af.flags:
                threat_mod = af[1].calculate_threat_to_target_mod(battle_map, self.combatant, {"roll_modifier": RollModifier.DISADVANTAGE})
                max_threat = max(max_threat, threat_mod)
        return max_threat



class Dodge(Actoid, CombatantEffect, LimitedDurationEffect, ThreatModifier):

    def __init__(self, combatant):
        Actoid.__init__(self, actoid_type=ActoidFlags.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, rounds=1)

    def activate(self):
        self.combatant.is_dodging = True
        self.combatant.saving_throws[SavingThrow.DEX][1].append(RollModifier.ADVANTAGE)

    def deactivate(self):
        logger.debug(f"{self.combatants[0]}'s dodge fades")
        self.combatant.is_dodging = False
        self.combatant.saving_throws[SavingThrow.DEX][1].remove(RollModifier.ADVANTAGE)


    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        """
        Calculate how much dmg would the dodge potentially mitigate. This will be the same as the one for the factory.
        """
        # TODO
        return 0