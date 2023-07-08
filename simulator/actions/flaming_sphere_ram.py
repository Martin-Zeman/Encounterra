from functools import cache

from simulator.actions.action_types import BonusAction
from simulator.battle_map import Map
from simulator.misc import DamageType, SavingThrow, Conditions
from simulator.actions.actoid import Actoid, ActoidFlags, FactoryFlags
from simulator.threat_interfaces import DirectThreat, DirectThreatFactory
import numpy as np

from simulator.threat_utils import mean_dmg_dc_attack

import logging

logger = logging.getLogger("EncounTroll")

class FlamingSphereRamFactory(DirectThreatFactory):

    RANGE = 6

    def __init__(self, caster, dc, action_enabler_effect, **kwargs):
        super().__init__()
        self.flags |= FactoryFlags.TRANSITIONS_TO_WILDSHAPE
        self.action_type = BonusAction.FLAMING_SPHERE_RAM
        self.dmg_dice = "2d6"
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

    def create_all(self):
        battle_map = Map.get()
        enemies = [e for e in battle_map.get_enemies(self.combatant) if not e.is_affected_by(Conditions.SWALLOWED)]
        result = []
        for enemy in enemies:
            # Just take the one that is on the far side of the enemy from the combatant's PoV
            coords_around_enemy = list(battle_map.get_free_coords_in_hop_range(battle_map.get_combatant_position(enemy), rng=1))
            coords_around_enemy.sort(key=lambda coord: battle_map.get_cartesian_distance(np.array([coord]), self.combatant), reverse=True)
            result.append(FlamingSphereRam(enemy, coords_around_enemy[0], self))
        return result

    def create(self, target, coord):
        return FlamingSphereRam(target, coord, self)

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates threat to one specific target
        """
        return mean_dmg_dc_attack(self.dc, self.dmg_dice, True, target.saving_throws[self.saving_throw], target.is_resistant_to(self.dmg_type))

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0  # No need


    def calculate_max_threat(self):
        enemies = [e for e in Map.get().get_enemies(self.combatant) if not e.is_affected_by(Conditions.SWALLOWED)]
        return max([self.calculate_threat_to_target(e) for e in enemies])


class FlamingSphereRam(Actoid, DirectThreat):

    def __init__(self, target, coord, factory,  **kwargs):
        super().__init__(actoid_flags=ActoidFlags.IS_DIRECT_THREAT)
        self.factory = factory
        self.target = target  # target of the ramming
        self.coord = coord  # but still has to end up at an adjacent unoccupied space

    def __str__(self):
        return f"Flaming Sphere Ram into {np.squeeze(self.target)}"

    def shorthand_str(self):
        return f"Flaming Sphere Ram"


    def calculate_threat(self, **kwargs):
        return self.factory.calculate_threat_to_target(self.target)

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0  # Doesn't apply here


    def get_eligible_coords(self, distances, shortest_paths):
        return Map.get().get_all_accessible_coords(shortest_paths, self.factory.combatant)

    def is_current_coord_eligible(self):
        return True

    def move_effect(self, coord):
        self.factory.action_enabler_effect.origin = coord
