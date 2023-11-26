from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import Action
from ..actions.actoid import Actoid, FactoryFlags
from ..battle_map import Map, map_toggled_cache_with_key
from ..effects.combatant_effect import CombatantEffect
from ..effects.effect import EffectType
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..threat_utils import calculate_threat_in_delta
from ..threat_interfaces import Threat
from ..factory_interfaces import ThreatModifierFactory
from ..misc import SavingThrow
import logging
from ..utils.roll_types import RollType, ThreatModifierType

logger = logging.getLogger("Encounterra")

class DodgeFactory(ThreatModifierFactory):

    def __init__(self, combatant):
        super().__init__()
        self.combatant = combatant
        self.action_type = Action.DODGE
        self.flags |= FactoryFlags.USES_CALCULATE_THREAT_IN_DELTA

    def __str__(self):
        """
        Important for FSM building
        """
        return "DodgeFactory"

    def create_all(self, previous_action_in_dag=None):
        return [Dodge(self.combatant, self)]

    def create(self):
        return Dodge(self.combatant, self)

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates the maximum threat reduction the factory can cause by imposing disadvantage on the target enemy
        """
        # The target is irrelevant here
        return -1 * calculate_threat_in_delta(self.combatant, 6, {ThreatModifierType.ROLL_TYPE: RollType.DISADVANTAGE}, FactoryFlags.IS_ATTACK_LIKE | FactoryFlags.DEX_SAVE_APPLIES)[0] / 2


class Dodge(Actoid, CombatantEffect, LimitedDurationEffect, Threat):

    def __init__(self, combatant, factory):
        Actoid.__init__(self)
        CombatantEffect.__init__(self, combatant, combatants=[combatant])
        LimitedDurationEffect.__init__(self, combatant, turns=1)
        self.factory = factory

    def __str__(self):
        return f"Dodge of {self.factory.combatant}"

    def get_effect_type(self):
        return EffectType.DODGE

    def shorthand_str(self):
        return f"Dodge"

    def activate(self):
        self.combatants[0].is_dodging = True
        self.combatants[0].saving_throws_roll_type_mod[SavingThrow.DEX].add(RollType.ADVANTAGE)

    def deactivate(self):
        logger.info(f"{self.combatants[0]}'s dodge fades")
        self.combatants[0].is_dodging = False
        try:
            self.combatants[0].saving_throws_roll_type_mod[SavingThrow.DEX].remove(RollType.ADVANTAGE)
        except KeyError:
            pass  # may not be present if called by reset

    def calculate_threat(self, **kwargs):
        """
        Calculate how much dmg would the dodge potentially mitigate. This will be the same as the one for the factory.
        """
        # return -1 * calculate_threat_in_delta(combatant, 6, battle_map, {ThreatModifierType.ROLL_TYPE: RollType.DISADVANTAGE}, FactoryFlags.IS_ATTACK_LIKE | FactoryFlags.DEX_SAVE_APPLIES) / 2
        return 0  # Threat that a Dodge would potentially mitigate is calculated using accumulate_threat_along_path

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]  # It's a priority action so the coord is not relevant

