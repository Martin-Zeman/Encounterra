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

class FlamingSphereRamFactory(DirectThreatFactory):
    def __init__(self, action_type, caster, **kwargs):
        super().__init__()
        self.action_type = action_type  # FLAMING_SPHERE_RAM
        self.dmg_dice = "2d6"
        self.combatant = caster


    def __str__(self):
        """
        Important for FSM building
        """
        return "FlamingSphereRamFactory"

    def create_all(self, battle_map):
        # Here there really is no need to iterate over all coords. Just find the best score
        return [FlamingSphereRam(self.find_best_args(self.combatant, battle_map), self)]

    def create(self, coord):
        return FlamingSphereRam(coord, self)

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        Calculates threat to one specific target
        """
        try:
            consider_dist = kwargs["consider_dist"]
        except KeyError:
            consider_dist = False

        if not consider_dist or battle_map.get_cartesian_distance(self.combatant, target) <= FlamingSphereRamFactory.range + SpellStats.TRANSLATE_RADIUS[FlamingSphereRamFactory.target]:
            return avg_roll(self.dmg_dice)
        return 0

    def calculate_threat_to_target_delta(self, battle_map, target, modified_stats, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0 # No need


class FlamingSphereRam(Actoid, AoeSquareEffect, DirectThreat, AoEThreat):

    def __init__(self, coord, factory,  **kwargs):
        super().__init__(actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_DIRECT_THREAT)
        LimitedDurationEffect.__init__(self, turns=10)
        AoeSquareEffect.__init__(self, coord, SpellStats.TRANSLATE_BOX[FlamingSphereRamFactory.target])
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FLAMING_SPHERE else "") + f"Flaming Sphere at {np.squeeze(self.combatant)}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FLAMING_SPHERE else "") + f"Flaming Sphere"

    def on_start_of_turn(self, combatant):
        pass

    def on_end_of_turn(self, combatant):
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        combatant.receive_dmg(dmg, FlamingSphereRamFactory.dmg_type)

    def on_enter(self, combatant):
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        combatant.receive_dmg(dmg, FlamingSphereRamFactory.dmg_type)

    def on_move_within(self, combatant):
        return 0

    def is_affecting(self, combatant, battle_map):
        return False

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
        affected = battle_map.get_combatants_affected_by_aoe(self.factory.combatant, SpellStats.Target.BOX_5, FlamingSphereRamFactory.type, self.coord)
        acc = 0
        for aff in affected:
            if battle_map.teams.are_enemies(self.factory.combatant, aff):
                acc += avg_roll(self.factory.dmg_dice)
            else:
                acc -= avg_roll(self.factory.dmg_dice)
        return acc

    def calculate_threat_delta(self, battle_map, modified_stats, *args, **kwargs):
        return 0  # Not relevant for this ability

    def on_start_of_turn(self, combatant):
        pass

    def on_end_of_turn(self, combatant):
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        combatant.receive_dmg(dmg, FlamingSphereFactory.dmg_type)

    def on_enter(self, combatant):
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        combatant.receive_dmg(dmg, FlamingSphereFactory.dmg_type)

    def on_move_within(self, combatant):
        return 0

    def is_affecting(self, combatant, battle_map):
        return False

    def calculate_threat_delta(self, battle_map, modified_stats, *args, **kwargs):
        return 0  # Not relevant for this ability

    def threat_on_end_of_turn(self, battle_map, target, *args, **kwargs):
        return avg_roll(self.factory.dmg_dice)

    def threat_on_enter(self, battle_map, target, *args, **kwargs):
        return avg_roll(self.factory.dmg_dice)

    def threat_on_start_of_turn(self, battle_map, target, *args, **kwargs):
        return 0

    def threat_on_move_within(self, battle_map, target, *args, **kwargs):
        return 0

    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        return battle_map.get_all_accessible_coords(shortest_paths)

    def is_current_coord_eligible(self, battle_map):
        return True
