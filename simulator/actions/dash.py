from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from simulator.actions.action_types import BonusAction, HasteAction
from simulator.actions.actoid import Actoid, ActoidFlags
import logging
from simulator.battle_map import Map, map_position_toggled_cache
from simulator.misc import Conditions
from simulator.threat_interfaces import Factory, AttackThreatModifier
from simulator.threat_utils import get_danger_zone_threat

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

    def create_all(self):
        return [Dash(self)]

    def create(self):
        return Dash(self)


class Dash(Actoid, AttackThreatModifier):
    def __init__(self, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_DASH)
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

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        movement_threat = kwargs["movement_threat"]
        baseline = -1 * movement_threat[min(self.factory.combatant.movement, len(movement_threat) - 1)]
        modified = -1 * movement_threat[min(self.factory.combatant.movement + self.factory.combatant.movement, len(movement_threat) - 1)]
        return max(0, baseline - modified)  # We're only interested in this if used defensively, we don't want it to play a role if used offensively

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        self.get_eligible_coords.cache_clear()

    def calculate_threat_for_attack(self, combatant, attack, *args, **kwargs):
        return 0  # TODO do the distance mod here

    @cached(cache={}, key=lambda self, distances, shortest_paths: hashkey(self.factory.combatant.name))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED, Conditions.SWALLOWED):
            return None
        if self.factory.combatant.movement > 0:
            return battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)
        return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
