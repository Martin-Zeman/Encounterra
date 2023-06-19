from functools import cache

from simulator.actions.action_types import BonusAction
from simulator.combatant_coords import CombatantCoords
from simulator.spells.spell import SpellStats
from simulator.misc import SavingThrow, DamageType
from simulator.actions.actoid import Actoid, ActoidFlags, FactoryFlags
from simulator.threat_utils import mean_dmg_dc_attack
from simulator.threat_interfaces import DirectThreat, DirectThreatFactory
import numpy as np

class FireballFactory(DirectThreatFactory):
    level = 3
    range = SpellStats.Range.FEET_150.value
    target = SpellStats.Target.RADIUS_20
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.HARMFUL
    dmg_type = DamageType.Fire

    def __init__(self, dc, action_type, caster, has_spell_sculpting=False, **kwargs):
        super().__init__()
        self.flags |= FactoryFlags.DEX_SAVE_APPLIES
        self.dc = dc
        self.action_type = action_type  # FIREBALL, QUICKENED_FIREBALL
        self.saving_throw = SavingThrow.DEX
        self.dmg_dice = "8d6"
        self.additional_upcast_dmg = "1d6"
        self.combatant = caster
        self.has_spell_sculpting = has_spell_sculpting


    def __str__(self):
        """
        Important for FSM building
        """
        return "FireballFactory"

    def get_twinned_kwargs(self):
        return {'dc': self.dc, 'caster': self.combatant, 'has_spell_sculpting': self.has_spell_sculpting}

    def get_quickened_kwargs(self):
        return {'dc': self.dc, 'caster': self.combatant, 'has_spell_sculpting': self.has_spell_sculpting}

    def find_best_args(self, combatant, battle_map):
        coord, _, _ = battle_map.find_best_placement_harmful_circular(combatant, FireballFactory.range, SpellStats.TRANSLATE_RADIUS[FireballFactory.target])
        return coord[0]

    def create_all(self, battle_map):
        # Here there really is no need to iterate over all coords. Just find the best score
        return [Fireball(self.find_best_args(self.combatant, battle_map), self)]

    def create(self, coord):
        return Fireball(coord, self)

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        Calculates threat to one specific target
        """
        if battle_map.get_cartesian_distance(self.combatant, target) <= FireballFactory.range + SpellStats.TRANSLATE_RADIUS[FireballFactory.target]:
            return mean_dmg_dc_attack(self.dc, self.dmg_dice, True, target.saving_throws[self.saving_throw])
        return 0

    def calculate_threat_to_target_delta(self, battle_map, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0  # No need

class Fireball(Actoid, DirectThreat):

    def __init__(self, coord, factory,  **kwargs):
        super().__init__(actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_DIRECT_THREAT)
        # self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.coord = coord
        self.factory = factory
        self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.heightened = False if "heightened " not in kwargs or not kwargs["heightened "] else True

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FIREBALL else "") + f"Fireball at {np.squeeze(self.coord)}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FIREBALL else "") + "Fireball"


    def clear_cache(self):
        self.calculate_threat.cache_clear()

    @cache
    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        affected = battle_map.get_combatants_affected_by_aoe(self.factory.combatant, FireballFactory.target, FireballFactory.type, self.coord)
        acc = 0
        for aff in affected:
            mean_dmg = mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, True, aff.saving_throws[self.factory.saving_throw])
            acc += (1 if battle_map.teams.are_enemies(combatant, aff) else -1) * mean_dmg
        return acc

    def calculate_threat_delta(self, battle_map, modifiers, *args, **kwargs):
        return 0  # Not relevant for this ability

    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        return battle_map.get_free_coords_in_cartesian_range(CombatantCoords(self.coord),  # not actually combatant coords
                                                             distances,
                                                             inflate_to_size=self.factory.combatant.size,
                                                             rng=FireballFactory.range,
                                                             combatant=self.factory.combatant)

    def is_current_coord_eligible(self, battle_map):
        return battle_map.get_cartesian_distance(self.factory.combatant, np.array([self.coord])) <= FireballFactory.range
