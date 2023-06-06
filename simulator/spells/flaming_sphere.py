from functools import cache

from simulator.actions.action_types import BonusAction
from simulator.combatant_coords import CombatantCoords
from simulator.effects.action_enabler_effect import ActionEnablerEffect
from simulator.effects.aoe_square_effect import AoeSquareEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, avg_roll, roll_spell_dmg, Size
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.threat_interfaces import DirectThreat, DirectThreatFactory, AoEThreat
import numpy as np

class FlamingSphereFactory(DirectThreatFactory):
    level = 2
    range = SpellStats.Range.FEET_60.value
    target = SpellStats.Target.BOX_5
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL
    dmg_type = DamageType.Fire

    def __init__(self, action_type, caster, **kwargs):
        super().__init__()
        self.action_type = action_type  # FLAMING_SPHERE, QUICKENED_FLAMING_SPHERE
        self.dmg_dice = "2d6"
        self.combatant = caster


    def __str__(self):
        """
        Important for FSM building
        """
        return "FlamingSphereFactory"

    def find_best_args(self, combatant, battle_map):
        # TODO maybe find a smarter placement for this
        coord, _, _ = battle_map.find_best_placement_harmful_square(self.combatant, FlamingSphereFactory.range, 1)
        return coord

    def create_all(self, battle_map):
        # Here there really is no need to iterate over all coords. Just find the best score
        return [FlamingSphere(self.find_best_args(self.combatant, battle_map), self)]

    def create(self, coord):
        return FlamingSphere(coord, self)

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        Calculates threat to one specific target
        """
        try:
            consider_dist = kwargs["consider_dist"]
        except KeyError:
            consider_dist = False

        if not consider_dist or battle_map.get_cartesian_distance(self.combatant, target) <= FlamingSphereFactory.range + SpellStats.TRANSLATE_RADIUS[FlamingSphereFactory.target]:
            return avg_roll(self.dmg_dice)
        return 0

    def calculate_threat_to_target_delta(self, battle_map, target, modified_stats, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0 # No need


class FlamingSphere(Actoid, LimitedDurationEffect, ActionEnablerEffect):

    def __init__(self, coord, factory,  **kwargs):
        super().__init__(actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_DIRECT_THREAT)
        LimitedDurationEffect.__init__(self, turns=10)
        AoeSquareEffect.__init__(self, coord, SpellStats.TRANSLATE_BOX[FlamingSphereFactory.target])
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FLAMING_SPHERE else "") + f"Flaming Sphere at {np.squeeze(self.combatant)}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FLAMING_SPHERE else "") + f"Flaming Sphere"

    def activate(self, battle_map):
        pass  # TODO add FLAMING_SPHERE_RAM bonus action

    def deactivate(self, battle_map):
        pass # TODO remove FLAMING_SPHERE_RAM bonus action

    def enable(self, battle_map):
        pass # TODO add FLAMING_SPHERE_RAM bonus action

    def disable(self, battle_map):
        pass # TODO remove FLAMING_SPHERE_RAM bonus action


    def clear_cache(self):
        self.calculate_threat.cache_clear()

    @cache
    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        affected = battle_map.get_combatants_affected_by_aoe(self.factory.combatant, SpellStats.Target.BOX_15, FlamingSphereFactory.type, self.coord)
        acc = 0
        for aff in affected:
            if battle_map.teams.are_enemies(self.factory.combatant, aff):
                acc += avg_roll(self.factory.dmg_dice)
            else:
                acc -= avg_roll(self.factory.dmg_dice)
        return acc



    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        return battle_map.get_free_coords_in_cartesian_range(CombatantCoords(self.combatant),  # not actually combatant coords
                                                             distances,
                                                             inflate_to_size=Size.MEDIUM,
                                                             rng=FlamingSphereFactory.range, combatant=None)

    def is_current_coord_eligible(self, battle_map):
        return False
