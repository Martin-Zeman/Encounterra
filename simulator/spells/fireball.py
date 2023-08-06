from functools import cache
from simulator.actions.action_types import BonusAction
from simulator.battle_map import Map, map_position_toggled_cache
from simulator.combatant_coords import Coords
from simulator.spells.spell import SpellStats
from simulator.misc import SavingThrow, DamageType, Conditions
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

    def find_best_args(self, combatant):
        coord, _ = Map.get().find_best_placement_harmful_circular(combatant, FireballFactory.range, SpellStats.TRANSLATE_RADIUS[FireballFactory.target], self)
        return coord[0]

    def create_all(self):
        # Here there really is no need to iterate over all coords. Just find the best score
        return [Fireball(self.find_best_args(self.combatant), self)]

    def create(self, coord):
        return Fireball(coord, self)

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates threat to one specific target
        """
        if Map.get().get_cartesian_distance(self.combatant, target) <= FireballFactory.range + SpellStats.TRANSLATE_RADIUS[FireballFactory.target]:
            return mean_dmg_dc_attack(self.dc, self.dmg_dice, True, target.saving_throws[self.saving_throw])
        return 0

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0  # No need

    def calculate_max_threat(self):
        return Fireball(self.find_best_args(self.combatant), self).calculate_threat()

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

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        battle_map = Map.get()
        affected = battle_map.get_combatants_affected_by_aoe(self.factory.combatant, FireballFactory.target, FireballFactory.type, self.coord)
        acc = 0
        for aff in affected:
            mean_dmg = mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, True, aff.saving_throws[self.factory.saving_throw])
            acc += (1 if battle_map.teams.are_enemies(self.factory.combatant, aff) else -3) * mean_dmg
        return acc

    def clear_cache(self):
        self.calculate_threat.cache_clear()

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0  # Not relevant for this ability

    def get_eligible_coords(self, distances, shortest_paths):
        if self.factory.combatant.get_swallower():
            return None
        battle_map = Map.get()
        if self.factory.combatant.movement > 0 and not self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return battle_map.get_free_coords_in_cartesian_range(Coords(self.coord),  # not actually combatant coords
                                                                 distances,
                                                                 inflate_to_size=self.factory.combatant.size,
                                                                 rng=FireballFactory.range,
                                                                 combatant=self.factory.combatant)
        elif battle_map.get_cartesian_distance(self.factory.combatant, np.array([self.coord])) <= FireballFactory.range:
            return set([tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])])
        return None
