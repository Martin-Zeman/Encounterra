from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import BonusAction, HasteAction
from ..actions.actoid import Actoid, ActoidFlags
import logging
from ..battle_map import Map, map_toggled_cache_with_key
from ..conditions import Conditions, is_affected_by_any
from ..threat_interfaces import AttackThreatModifier
from ..factory_interfaces import Factory

logger = logging.getLogger("Encounterra")


class DashFactory(Factory):
    def __init__(self, action_type, combatant):
        super().__init__()
        self.combatant = combatant
        self.action_type = action_type  # DASH, CUNNING_DASH, AGGRESSIVE

    def __str__(self):
        """
        Important for FSM building
        """
        return "DashFactory"

    def create_all(self, previous_action_in_dag=None):
        return [Dash(self)]

    def create(self, target):
        return Dash(self)


class Dash(AttackThreatModifier):
    def __init__(self, factory):
        AttackThreatModifier.__init__(self, ActoidFlags.IS_DASH | ActoidFlags.LOCATION_INDEPENDENT)
        self.name = "Dash"
        self.factory = factory
        if self.factory.action_type is BonusAction.AGGRESSIVE:
            self.actoid_flags |= ActoidFlags.IS_PRIORITY

    def __str__(self):
        if self.factory.action_type is BonusAction.CUNNING_DASH:
            return f"Cunning Dash {self.factory.combatant}"
        elif self.factory.action_type is HasteAction.HASTE_DASH:
            return f"Hasted Dash of {self.factory.combatant}"
        elif self.factory.action_type is BonusAction.AGGRESSIVE:
            return f"Aggressive movement of {self.factory.combatant}"
        return f"Dash of {self.factory.combatant}"

    def shorthand_str(self):
        if self.factory.action_type is BonusAction.CUNNING_DASH:
            return "Cunning Dash"
        elif self.factory.action_type is HasteAction.HASTE_DASH:
            return "Hasted Dash"
        elif self.factory.action_type is BonusAction.AGGRESSIVE:
            return "Aggressive movement"
        return "Dash"

    @map_toggled_cache_with_key(key=lambda self, **kwargs: hashkey(kwargs["movement_threat"], self.factory.combatant.movement, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def calculate_threat(self, **kwargs):
        movement_threat = kwargs["movement_threat"]
        if self.factory.action_type is BonusAction.AGGRESSIVE:
            if len(movement_threat) - 1 > self.factory.combatant.movement:
                # We always want this to be used if the destination can't be reached, the moving towards an enemy part is always assumed
                return 1
            return -1
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
        if is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED, Conditions.SWALLOWED):
            return None
        # if self.factory.combatant.movement > 0:
        return battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)
        # return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
