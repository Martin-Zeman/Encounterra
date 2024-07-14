import numpy as np
from cachetools.keys import hashkey

from ..actions.action_types import Action
from ..actions.actoid import FactoryFlags, Actoid, ActoidFlags
from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key, \
    _get_free_coords_in_hop_range, _reconstruct_from_shortest_path
from ..conditions import Conditions, is_affected_by_any, get_swallower
from ..misc import _is_path_straight
from ..threat_interfaces import DirectThreat
from ..factory_interfaces import DirectThreatFactory
from ..threat_utils import get_saving_throw_success_prob
import logging


logger = logging.getLogger("Encounterra")


class PounceFactory(DirectThreatFactory):

    def __init__(self, combatant, primary_attack, secondary_attack, distance):
        DirectThreatFactory.__init__(self)
        self.combatant = combatant
        self.primary_attack = primary_attack
        self.secondary_attack = secondary_attack
        self.distance = distance
        self.action_type = Action.POUNCE
        self.flags |= FactoryFlags.IS_MELEE

    def __str__(self):
        return "PounceFactory"

    def get_ability_name(self):
        return "Pounce"

    def get_eligible_targets(self):
        swallower = get_swallower(self.combatant)
        if swallower:
            return []
        battle_map = Map.get()
        return [e for e in battle_map.get_non_swallowed_enemies_without_hop_distance(self.combatant, self.distance - 1)]

    def create(self, target):
        return Pounce(target, self)

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [Pounce(t, self) for t in targets]

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates the threat the factory is capable of dealing to a specific target.
        This is useful for calculating threat_in from the abilities of enemies
        """
        # TODO include the threat of the PRONE in the calculation
        p_fail = 1 - get_saving_throw_success_prob(self.primary_attack[1].on_hit[0].dc, target.saving_throws[self.primary_attack[1].on_hit[0].st])
        return self.primary_attack[1].calculate_threat_to_target(target) + p_fail * self.secondary_attack[1].calculate_threat_to_target(target)

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications.
        This is useful calculating the potential reduction of threat_in caused by abilities of enemies, e.g. advantage on saving throw
        against fireball or bane on attack rolls etc.
        """
        p_fail = 1 - get_saving_throw_success_prob(self.primary_attack[1].on_hit[0].dc, target.saving_throws[self.primary_attack[1].on_hit[0].st])
        return self.primary_attack[1].calculate_threat_to_target_delta(target, modifiers) + p_fail * self.secondary_attack[1].calculate_threat_to_target_delta(target, modifiers)

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        if not targets:
            return 0
        return max([self.calculate_threat_to_target(t) for t in targets])


class Pounce(Actoid, DirectThreat):

    def __init__(self, target, factory):
        Actoid.__init__(self, ActoidFlags.IS_ATTACK_LIKE)
        self.target = target
        self.factory = factory

    def __str__(self):
        return f"Pounce on {self.target}"

    def shorthand_str(self):
        return "Pounce"

    def is_straight_line_path(self, start_coord, end_coord, shortest_paths):
        # Calculate the distance using Dijkstra's algorithm results
        path = _reconstruct_from_shortest_path(shortest_paths, start_coord.get()[0], np.array(end_coord, dtype=np.int64))
        if path.shape[0] == 0:
            return False
        # Check if the path is straight and at least 4 squares long
        return _is_path_straight(path, self.factory.distance)


    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            all_coords = _get_free_coords_in_hop_range(
                battle_map.grid,
                battle_map.get_combatant_position(self.target).get(),
                distances,
                inflate_to_dist=self.factory.combatant.size.value,
                rng=1,
                combatant_id=self.factory.combatant.id)
            eligible_coords = []
            for coord in all_coords:
                if self.is_straight_line_path(battle_map.get_combatant_position(self.factory.combatant), coord, shortest_paths):
                    eligible_coords.append(coord)
            return eligible_coords
        elif battle_map.get_hop_distance_combatants(self.factory.combatant, self.target) >= self.factory.distance:
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
        return None

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        """
        Threat estimation generated by the instantiated ability.
        """
        return self.factory.calculate_threat_to_target(self.target)

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        self.calculate_threat_delta.cache_clear()
        #self.get_eligible_coords.cache_clear()

    @map_toggled_cache_with_key(key=lambda self, modifiers, *args, **kwargs: hashkey(self.factory.name, tuple(modifiers.items()), tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        """
        The delta in threat when modifiers are applied on this ability.
        """
        return self.factory.calculate_threat_to_target_delta(self.target, modifiers)
