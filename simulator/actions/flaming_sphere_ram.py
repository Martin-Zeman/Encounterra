from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import BonusAction
from ..battle_map import Map, map_position_toggled_cache, _get_cartesian_distance_coords, _get_free_coords_in_hop_range
from ..misc import DamageType, SavingThrow
from ..actions.actoid import Actoid, FactoryFlags
from ..threat_interfaces import DirectThreat
from ..factory_interfaces import DirectThreatFactory
import numpy as np
from ..threat_utils import mean_dmg_dc_attack
import logging

logger = logging.getLogger("Encounterra")

class FlamingSphereRamFactory(DirectThreatFactory):

    RANGE = 6

    def __init__(self, caster, dc, action_enabler_effect, **kwargs):
        super().__init__()
        self.flags |= FactoryFlags.TRANSITIONS_TO_WILDSHAPE
        self.action_type = BonusAction.FLAMING_SPHERE_RAM
        self.dmg_dice = ((2, 6),)
        self.combatant = caster
        self.dc = dc
        self.action_enabler_effect = action_enabler_effect
        self.saving_throw = SavingThrow.DEX
        self.dmg_type = DamageType.Fire


    def __str__(self):
        """
        Important for FSM building
        """
        return "FlamingSphereRamFactory"

    def create_all(self, previous_action_in_dag=None):
        battle_map = Map.get()
        enemies = [e for e in battle_map.get_non_swallowed_enemies(self.combatant)]
        result = []
        for enemy in enemies:
            # Just take the one that is on the far side of the enemy from the combatant's PoV
            coords_around_enemy = _get_free_coords_in_hop_range(battle_map.grid, battle_map.get_combatant_position(enemy).get(), rng=1)
            coords_around_enemy.sort(key=lambda coord: _get_cartesian_distance_coords(np.array([coord]), battle_map.get_combatant_position(self.combatant).get()), reverse=True)
            result.append(FlamingSphereRam(enemy, np.array(coords_around_enemy[0], dtype=np.int32), self))
        return result

    def create(self, target, coord):
        return FlamingSphereRam(target, np.array(coord, dtype=np.int32), self)

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates threat to one specific target
        """
        return min(target.curr_hp, mean_dmg_dc_attack(self.dc, self.dmg_dice, True,
                                                      target.saving_throws[self.saving_throw],
                                                      target.is_immune_to(self.dmg_type),
                                                      target.is_resistant_to(self.dmg_type)))

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0  # No need

    def calculate_max_threat(self):
        enemies = [e for e in Map.get().get_non_swallowed_enemies(self.combatant)]
        return max([self.calculate_threat_to_target(e) for e in enemies])


class FlamingSphereRam(Actoid, DirectThreat):

    def __init__(self, target, coord, factory,  **kwargs):
        Actoid.__init__(self)
        self.factory = factory
        self.target = target  # target of the ramming
        self.coord = coord  # but still has to end up at an adjacent unoccupied space

    def __str__(self):
        return f"Flaming Sphere Ram into {np.squeeze(self.target)}"

    def shorthand_str(self):
        return f"Flaming Sphere Ram"

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        return self.factory.calculate_threat_to_target(self.target)

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        #self.get_eligible_coords.cache_clear()

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0  # Doesn't apply here

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        # if self.factory.combatant.movement > 0:
        #     return battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)
        return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]

    def move_effect(self, coord: np.array):
        self.factory.action_enabler_effect.origin = coord
