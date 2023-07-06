import logging
from functools import cache

from simulator.actions.action_types import BonusAction
from simulator.actions.flaming_sphere_ram import FlamingSphereRamFactory
from simulator.battle_map import Map
from simulator.combatant_coords import CombatantCoords
from simulator.effects.action_enabler_effect import ActionEnablerEffect
from simulator.effects.aoe_square_effect import AoeSquareEffect
from simulator.effects.effect import EffectType
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, avg_roll, roll_spell_dmg, Size, ROUND_HORIZON, SavingThrow
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.threat_interfaces import DirectThreat, DirectThreatFactory, AoEThreat
import numpy as np

from simulator.threat_utils import mean_dmg_dc_attack

logger = logging.getLogger("EncounTroll")


class FlamingSphereFactory(DirectThreatFactory):
    level = 2
    range = SpellStats.Range.FEET_60.value
    target = SpellStats.Target.BOX_5
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL
    dmg_type = DamageType.Fire

    def __init__(self, dc, action_type, caster, **kwargs):
        super().__init__()
        self.action_type = action_type  # FLAMING_SPHERE, QUICKENED_FLAMING_SPHERE
        self.dmg_dice = "2d6"
        self.dc = dc
        self.combatant = caster
        self.saving_throw = SavingThrow.DEX


    def __str__(self):
        """
        Important for FSM building
        """
        return "FlamingSphereFactory"


    def create_all(self):
        # Getting coords around enemies
        battle_map = Map.get()
        enemies = battle_map.get_enemies(self.combatant)
        coords = set()
        for enemy in enemies:
            # Just take the one that is on the far side of the enemy from the combatant's PoV
            coords_around_enemy = list(battle_map.get_free_coords_in_hop_range(battle_map.get_combatant_position(enemy), rng=1))
            coords_around_enemy.sort(key=lambda coord: battle_map.get_cartesian_distance(np.array([coord]), self.combatant), reverse=True)
            coords.add(coords_around_enemy[0])

        # Here there really is no need to iterate over all coords. Just find the best score
        return [FlamingSphere(coord, self) for coord in coords]

    def create(self, coord):
        return FlamingSphere(coord, self)

    def calculate_threat_to_target(self, target, *args, **kwargs):
        """
        Calculates threat to one specific target
        """
        return mean_dmg_dc_attack(self.dc, self.dmg_dice, True, target.saving_throws[self.saving_throw], target.is_resistant_to(self.dmg_type)) * ROUND_HORIZON

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0  # No need

    def calculate_max_threat(self):
        targets = Map.get().get_enemies(self.combatant)
        return max([self.calculate_threat_to_target(t) for t in targets])


class FlamingSphere(Actoid, LimitedDurationEffect, ActionEnablerEffect, AoeSquareEffect, AoEThreat):

    def __init__(self, coord, factory,  **kwargs):
        super().__init__(actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_DIRECT_THREAT)
        LimitedDurationEffect.__init__(self, turns=10)
        AoeSquareEffect.__init__(self, coord, SpellStats.TRANSLATE_BOX[FlamingSphereFactory.target])
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FLAMING_SPHERE else "") + f"Flaming Sphere at {np.squeeze(self.origin)}"

    def get_effect_type(self):
        return EffectType.FLAMING_SPHERE

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FLAMING_SPHERE else "") + f"Flaming Sphere"

    def activate(self):
        Map.get().effect_tracker.add(self)
        self.factory.combatant.concentration_effect = self
        self.factory.combatant.bonus_action_factories.append((BonusAction.FLAMING_SPHERE_RAM, FlamingSphereRamFactory(self.factory.combatant, self.factory.dc, self)))

    def deactivate(self):
        logger.info(f"Flaming Sphere disappears")  # TODO remove this
        self.factory.combatant.get_current_form().concentration_effect = None
        self.factory.combatant.get_current_form().bonus_action_factories = [baf for baf in self.factory.combatant.get_current_form().bonus_action_factories if baf[0] is not BonusAction.FLAMING_SPHERE_RAM]
        self.factory.combatant.bonus_action_factories = [baf for baf in self.factory.combatant.bonus_action_factories if baf[0] is not BonusAction.FLAMING_SPHERE_RAM]  # Doesn't carry over with deactivation of wildshape

    def enable(self):
        self.factory.combatant.bonus_action_factories.append((BonusAction.FLAMING_SPHERE_RAM, FlamingSphereRamFactory(self.factory.combatant, self.factory.dc, self)))

    def disable(self):
        self.factory.combatant.bonus_action_factories = [baf for baf in self.factory.combatant.bonus_action_factories if baf[0] is not BonusAction.FLAMING_SPHERE_RAM]


    def calculate_threat(self, *args, **kwargs):
        # Get the average ram damage times ROUND_HORIZON. This is a rough estimation
        enemies = Map.get().get_enemies_within_hop_distance(self.factory.combatant, FlamingSphereFactory.range)
        if not enemies:
            return 0
        acc = 0
        for enemy in enemies:
            acc += mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, True, enemy.saving_throws[self.factory.saving_throw], enemy.is_resistant_to(self.factory.dmg_type))
        return acc / len(enemies) * ROUND_HORIZON

    def get_eligible_coords(self, distances, shortest_paths):
        return Map.get().get_free_coords_in_cartesian_range(CombatantCoords(self.origin),  # not actually combatant coords
                                                             distances,
                                                             inflate_to_size=self.factory.combatant.size,
                                                             rng=FlamingSphereFactory.range,
                                                             combatant=self.factory.combatant)

    def is_current_coord_eligible(self):
        if self.factory.combatant.get_swallower():
            return False  # Not possible while blinded
        return Map.get().get_cartesian_distance(self.factory.combatant, np.array([self.origin])) <= FlamingSphereFactory.range

    def on_start_of_turn(self, combatant):
        pass

    def on_end_of_turn(self, combatant):
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        logger.info(f"{combatant} is burned by Flaming Sphere for {dmg} damage")
        combatant.receive_dmg(dmg, FlamingSphereFactory.dmg_type)

    def on_enter(self, combatant):
        # It's not explicitly written in the rules, but it makes sense
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        logger.info(f"{combatant} is burned by Flaming Sphere for {dmg} damage")
        combatant.receive_dmg(dmg, FlamingSphereFactory.dmg_type)

    def on_move_within(self, combatant):
        return 0

    def on_exit(self, combatant):
        return 0

    def is_affecting(self, combatant):
        return False

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0  # Not relevant for this ability

    def threat_on_end_of_turn(self, target, *args, **kwargs):
        return mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, True, target.saving_throws[self.factory.saving_throw], target.is_resistant_to(self.factory.dmg_type))

    def threat_on_enter(self, target, *args, **kwargs):
        # It's not explicitly written in the rules, but it makes sense
        return mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, True, target.saving_throws[self.factory.saving_throw], target.is_resistant_to(self.factory.dmg_type))

    def threat_on_start_of_turn(self, target, *args, **kwargs):
        return 0

    def threat_on_move_within(self, target, *args, **kwargs):
        return 0

    def get_affected_coords(self):
        """
        We model the fact that it deals damage to adjacent squares
        """
        return Map.get().get_coords_affected_by_square_aoe((self.origin[0] - 1, self.origin[1] - 1), self.length + 2)