from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import BonusAction, HasteAction
from ..actions.actoid import Actoid, ActoidFlags
import logging
from ..battle_map import Map, map_toggled_cache_with_key
from ..misc import Conditions
from ..threat_interfaces import AttackThreatModifier
from ..factory_interfaces import Factory

logger = logging.getLogger("Encounterra")

class DashFactory(Factory):
    def __init__(self, action_type, combatant):
        super().__init__()
        self.combatant = combatant
        self.action_type = action_type  # DASH, CUNNING_DASH

    def __str__(self):
        """
        Important for FSM building
        """
        return "DashFactory"

    def create_all(self, previous_action_in_dag=None):
        return [Dash(self)]

    def create(self):
        return Dash(self)


class Dash(Actoid, AttackThreatModifier):
    def __init__(self, factory):
        Actoid.__init__(self, ActoidFlags.IS_DASH)
        self.name = "Dash"
        self.factory = factory

    def __str__(self):
        prefix = ""
        if self.factory.action_type is BonusAction.CUNNING_DASH:
            prefix = "Cunning "
        elif self.factory.action_type is HasteAction.HASTE_DASH:
            prefix = "Hasted "
        return prefix + f"Dash of {self.factory.combatant}"

    def shorthand_str(self):
        prefix = ""
        if self.factory.action_type is BonusAction.CUNNING_DASH:
            prefix = "Cunning "
        elif self.factory.action_type is HasteAction.HASTE_DASH:
            prefix = "Hasted "
        return prefix + f"Dash"

    @map_toggled_cache_with_key(key=lambda self, **kwargs: hashkey(kwargs["movement_threat"], self.factory.combatant.movement, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def calculate_threat(self, **kwargs):
        movement_threat = kwargs["movement_threat"]
        baseline = -1 * movement_threat[min(int(self.factory.combatant.movement), len(movement_threat) - 1)]
        modified = -1 * movement_threat[min(int(self.factory.combatant.movement + self.factory.combatant.speed), len(movement_threat) - 1)]
        return max(0, baseline - modified)  # We're only interested in this if used defensively, we don't want it to play a role if used offensively

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        #self.get_eligible_coords.cache_clear()

    def calculate_threat_for_attack(self, combatant, attack, *args, **kwargs):
        return 0  # TODO do the distance mod here

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED, Conditions.SWALLOWED):
            return None
        # if self.factory.combatant.movement > 0:
        return battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)
        # return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
