import copy

import numpy as np
from cachetools import cached
from cachetools.keys import hashkey

from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key
from ..combatant_coords import Coords
from ..effects.aoe_square_effect import AoeSquareEffect
from ..effects.combatant_effect import CombatantEffect
from ..effects.effect import EffectType
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..spells.spell import SpellStats
from ..actions.action_types import BonusAction, Passive
from ..actions.actoid import Actoid, ActoidFlags, FactoryFlags
from ..threat_interfaces import Threat
from ..factory_interfaces import ThreatModifierFactory
from functools import cache
from ..misc import roll_saving_throw, reconcile_roll_types, SavingThrow
from ..conditions import Conditions, is_affected_by_any, get_swallower, remove_condition
import logging
from ..threat_utils import calculate_threat_in_delta
from ..utils.roll_types import ThreatModifierType, RollType

logger = logging.getLogger("Encounterra")


class FaerieFireFactory(ThreatModifierFactory):
    level = 1
    range = SpellStats.Range.FEET_60.value
    target = SpellStats.Target.BOX_20
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL
    dmg_type = None

    def __init__(self, dc, action_type, caster, resource):
        super().__init__()
        self.flags |= FactoryFlags.PREVENT_ENDLESS_RECURSION
        self.dc = dc
        self.action_type = action_type  # QUICKENED_FAERIE_FIRE, FAERIE_FIRE
        self.combatant = caster
        self.saving_throw = SavingThrow.DEX
        self.resource = resource

    def __str__(self):
        """
        Important for FSM building
        """
        return "FaerieFireFactory"

    def get_ability_name(self):
        return "Faerie Fire"

    def get_quickened_kwargs(self):
        return {'combatant': self.combatant, 'resource': self.resource}

    def find_best_args(self, combatant):
        coord, _, _ = Map.get().find_best_placement_harmful_square(combatant, FaerieFireFactory.range, SpellStats.TRANSLATE_BOX[FaerieFireFactory.target])
        return coord

    def create_all(self, previous_action_in_dag=None):
        # Here there really is no need to iterate over all coords. Just find the best score
        coord = self.find_best_args(self.combatant)
        if coord is not None:
            return [FaerieFire(coord, self)]
        return []

    def create(self, coord):
        return FaerieFire(coord, self)

    def calculate_threat_to_target(self, target, **kwargs):
        """
        For the given target ally it finds the attack with the highest mean dmg across all enemies withing range. It then adds
        estimated dmg prevention given by the AC bonus and by the saving throw advantage.
        """
        ret = calculate_threat_in_delta(target, 6, {ThreatModifierType.ROLL_TYPE: RollType.ADVANTAGE}, FactoryFlags.IS_ATTACK_LIKE)[1]
        return -ret

    def calculate_max_threat(self):
        ret = FaerieFire(self.find_best_args(self.combatant), self).calculate_threat()
        return ret


class FaerieFire(Actoid, LimitedDurationEffect, Threat, AoeSquareEffect, CombatantEffect):

    def __init__(self, coord, factory,  **kwargs):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, factory.combatant, turns=10)
        AoeSquareEffect.__init__(self, factory.combatant, coord, SpellStats.TRANSLATE_BOX[FaerieFireFactory.target])
        CombatantEffect.__init__(self, factory.combatant, [])
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FAERIE_FIRE else "") + f"Faerie Fire at {self.origin}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FAERIE_FIRE else "") + "Faerie Fire"

    def get_effect_type(self):
        return EffectType.FAERIE_FIRE

    def is_affecting(self, combatant):
        return CombatantEffect.is_affecting(self, combatant)

    def activate(self, **kwargs):
        potentially_affected_combatants = Map.get().get_combatants_affected_by_aoe(self.factory.combatant, FaerieFireFactory.target, FaerieFireFactory.type, self.origin)
        failed_count = 0
        for pac in potentially_affected_combatants:
            st = self.factory.saving_throw
            roll_type_modifiers = copy.copy(pac.saving_throws_roll_type_mod[st])
            if pac.has_passive(Passive.MAGIC_RESISTANCE):
                roll_type_modifiers.add(RollType.ADVANTAGE)
            if not roll_saving_throw(pac.saving_throws[st], self.factory.dc, reconcile_roll_types(roll_type_modifiers)):
                logger.info(f"{pac} failed the save against Faerie Fire")
                failed_count += 1
                remove_condition(pac, Conditions.INVISIBLE)
                self.combatants.append(pac)
            else:
                logger.info(f"{pac} saved against Faerie Fire")
        if failed_count:
            self.factory.combatant.concentration_effect = self
            Map.get().effect_tracker.add(self)

    def deactivate(self):
        self.factory.combatant.break_concentration()
        self.combatants.clear()

    def deactivate_for_combatant(self, combatant):
        assert False

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        battle_map = Map.get()
        affected = battle_map.get_combatants_affected_by_aoe(self.factory.combatant, FaerieFireFactory.target, FaerieFireFactory.type, self.origin)
        acc = 0
        for aff in affected:
            threat_delta = calculate_threat_in_delta(aff, 6, {ThreatModifierType.ROLL_TYPE: RollType.ADVANTAGE}, FactoryFlags.IS_ATTACK_LIKE)[1]
            acc += (1 if battle_map.teams.are_enemies(self.factory.combatant, aff) else -3) * threat_delta
        return -acc

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        #self.get_eligible_coords.cache_clear()

    def threat_on_end_of_turn(self, target, *args, **kwargs):
        return 0

    def threat_on_enter(self, target, *args, **kwargs):
        return 0

    def threat_on_start_of_turn(self, target, *args, **kwargs):
        return 0

    def threat_on_move_within(self, target, *args, **kwargs):
        return 0

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        if get_swallower(self.factory.combatant):
            return None
        battle_map = Map.get()
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return Map.get().get_free_coords_in_cartesian_range(Coords(self.origin),  # not actually combatant coords
                                                                 distances,
                                                                 inflate_to_dist=self.factory.combatant.size.value,
                                                                 rng=FaerieFireFactory.range, combatant=self.factory.combatant)
        elif battle_map.get_cartesian_distance_coords(battle_map.get_combatant_position(self.factory.combatant).get(), np.array([self.origin])) <= FaerieFireFactory.range:
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
        return None

    def on_enter(self, combatant):
        pass

    def on_move_within(self, combatant):
        pass

    def on_exit(self, combatant):
        pass

    def on_start_of_turn(self, combatant):
        pass

    def on_end_of_turn(self, combatant):
        pass
