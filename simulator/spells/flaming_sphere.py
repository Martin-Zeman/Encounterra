import logging
from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import BonusAction
from ..actions.flaming_sphere_ram import FlamingSphereRamFactory
from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key, _get_cartesian_distance_coords, \
    _get_free_coords_in_cartesian_range, _get_free_coords_in_hop_range
from ..combatant_coords import Coords
from ..effects.action_enabler_effect import ActionEnablerEffect
from ..effects.aoe_square_effect import AoeSquareEffect
from ..effects.effect import EffectType
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..spells.spell import SpellStats
from ..misc import DamageType, ROUND_HORIZON, SavingThrow, _roll_dice
from ..conditions import Conditions, is_affected_by_any, get_swallower
from ..actions.actoid import Actoid, ActoidFlags
from ..threat_interfaces import AoEThreat, Threat
from ..factory_interfaces import DirectThreatFactory
import numpy as np

from ..threat_utils import _mean_dmg_dc_attack

logger = logging.getLogger("Encounterra")


class FlamingSphereFactory(DirectThreatFactory):
    level = 2
    range = SpellStats.Range.FEET_60.value
    target = SpellStats.Target.BOX_5
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL
    dmg_type = DamageType.Fire

    def __init__(self, dc, action_type, caster, resource):
        super().__init__()
        self.action_type = action_type  # FLAMING_SPHERE, QUICKENED_FLAMING_SPHERE
        self.dmg_dice = ((2, 6),)
        self.dc = dc
        self.combatant = caster
        self.saving_throw = SavingThrow.DEX
        self.resource = resource

    def __str__(self):
        """
        Important for FSM building
        """
        return "FlamingSphereFactory"

    def get_ability_name(self):
        return "Flaming Sphere"

    def create_all(self, previous_action_in_dag=None):
        # Getting coords around enemies
        battle_map = Map.get()
        enemies = battle_map.get_non_swallowed_enemies(self.combatant)
        coords = set()
        for enemy in enemies:
            # Just take the one that is on the far side of the enemy from the combatant's PoV
            coords_around_enemy = _get_free_coords_in_hop_range(battle_map.grid, battle_map.get_combatant_position(enemy).get(), rng=1)
            coords_around_enemy.sort(key=lambda coord: _get_cartesian_distance_coords(np.array([coord]), battle_map.get_combatant_position(self.combatant).get()), reverse=True)
            coords.add(coords_around_enemy[0])

        # Here there really is no need to iterate over all coords. Just find the best score
        return [FlamingSphere(np.array(coord, dtype=np.int32), self) for coord in coords]

    def create(self, coord):
        return FlamingSphere(np.array(coord, dtype=np.int32), self)

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates threat to one specific target
        """
        return min(target.curr_hp, _mean_dmg_dc_attack(self.dc, self.dmg_dice, True,
                                                      target.saving_throws[self.saving_throw],
                                                      target.is_immune_to(self.dmg_type),
                                                      target.is_resistant_to(self.dmg_type))) * ROUND_HORIZON

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0  # No need

    def calculate_max_threat(self):
        targets = Map.get().get_non_swallowed_enemies(self.combatant)
        if not targets:
            return 0
        return max([self.calculate_threat_to_target(t) for t in targets])


class FlamingSphere(Actoid, LimitedDurationEffect, ActionEnablerEffect, AoeSquareEffect, Threat, AoEThreat):

    def __init__(self, coord, factory,  **kwargs):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, factory.combatant, turns=10)
        AoeSquareEffect.__init__(self, factory.combatant, coord, SpellStats.TRANSLATE_BOX[FlamingSphereFactory.target])
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FLAMING_SPHERE else "") + f"Flaming Sphere at {np.squeeze(self.origin)}"

    def get_effect_type(self):
        return EffectType.FLAMING_SPHERE

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FLAMING_SPHERE else "") + f"Flaming Sphere"

    def activate(self, **kwargs):
        Map.get().effect_tracker.add(self)
        self.factory.combatant.concentration_effect = self
        self.factory.combatant.bonus_action_factories.append((BonusAction.FLAMING_SPHERE_RAM, FlamingSphereRamFactory(self.factory.combatant, self.factory.dc, self)))

    def deactivate(self):
        logger.info(f"Flaming Sphere fades")  # TODO remove this
        self.factory.combatant.break_concentration()
        self.factory.combatant.get_current_form().bonus_action_factories = [baf for baf in self.factory.combatant.get_current_form().bonus_action_factories if baf[0] is not BonusAction.FLAMING_SPHERE_RAM]
        self.factory.combatant.bonus_action_factories = [baf for baf in self.factory.combatant.bonus_action_factories if baf[0] is not BonusAction.FLAMING_SPHERE_RAM]  # Doesn't carry over with deactivation of wildshape

    def deactivate_for_combatant(self, combatant):
        assert False

    def enable(self):
        self.factory.combatant.bonus_action_factories.append((BonusAction.FLAMING_SPHERE_RAM, FlamingSphereRamFactory(self.factory.combatant, self.factory.dc, self)))

    def disable(self):
        self.factory.combatant.bonus_action_factories = [baf for baf in self.factory.combatant.bonus_action_factories if baf[0] is not BonusAction.FLAMING_SPHERE_RAM]

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        # Get the average ram damage times ROUND_HORIZON. This is a rough estimation
        enemies = Map.get().get_non_swallowed_enemies_within_hop_distance(self.factory.combatant, FlamingSphereFactory.range)
        if not enemies:
            return 0
        acc = 0
        for enemy in enemies:
            acc += min(enemy.curr_hp, _mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, True,
                                                         enemy.saving_throws[self.factory.saving_throw],
                                                         enemy.is_immune_to(self.factory.dmg_type),
                                                         enemy.is_resistant_to(self.factory.dmg_type)))
        return acc / len(enemies) * ROUND_HORIZON

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        #self.get_eligible_coords.cache_clear()

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        if get_swallower(self.factory.combatant):
            return None  # Not possible while blinded
        battle_map = Map.get()
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return _get_free_coords_in_cartesian_range(
                battle_map.grid,
                Coords(self.origin).get(),  # not actually combatant coords
                distances,
                inflate_to_dist=self.factory.combatant.size.value,
                rng=FlamingSphereFactory.range,
                combatant_id=self.factory.combatant.id)
        elif _get_cartesian_distance_coords(battle_map.get_combatant_position(self.factory.combatant).get(), np.array([self.origin])) <= FlamingSphereFactory.range:
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
        return None

    def on_start_of_turn(self, combatant):
        pass

    def on_end_of_turn(self, combatant):
        dmg = _roll_dice(self.factory.dmg_dice)
        logger.info(f"{combatant} is burned by Flaming Sphere for {dmg} damage")
        combatant.receive_dmg(dmg, FlamingSphereFactory.dmg_type)
        Map.get().remove_combatant_if_dead(combatant)

    def on_enter(self, combatant):
        # It's not explicitly written in the rules, but it makes sense
        dmg = _roll_dice(self.factory.dmg_dice)
        logger.info(f"{combatant} is burned by Flaming Sphere for {dmg} damage")
        combatant.receive_dmg(dmg, FlamingSphereFactory.dmg_type)
        Map.get().remove_combatant_if_dead(combatant)

    def on_move_within(self, combatant):
        return 0

    def on_exit(self, combatant):
        return 0

    def is_affecting(self, combatant):
        return False

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0  # Not relevant for this ability

    def threat_on_end_of_turn(self, target, *args, **kwargs):
        return min(target.curr_hp, _mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice,
                                                      True,
                                                      target.saving_throws[self.factory.saving_throw],
                                                      target.is_immune_to(self.factory.dmg_type),
                                                      target.is_resistant_to(self.factory.dmg_type)))

    def threat_on_enter(self, target, *args, **kwargs):
        # It's not explicitly written in the rules, but it makes sense
        return min(target.curr_hp, _mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, True,
                                                      target.saving_throws[self.factory.saving_throw],
                                                      target.is_immune_to(self.factory.dmg_type),
                                                      target.is_resistant_to(self.factory.dmg_type)))

    def threat_on_start_of_turn(self, target, *args, **kwargs):
        return 0

    def threat_on_move_within(self, target, *args, **kwargs):
        return 0

    def get_affected_coords(self):
        """
        We model the fact that it deals damage to adjacent squares
        """
        return Map.get().get_coords_affected_by_square_aoe((self.origin[0] - 1, self.origin[1] - 1), self.length + 2)
