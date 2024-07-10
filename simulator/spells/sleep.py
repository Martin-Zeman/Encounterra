import logging
from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import BonusAction, Action, Passive
from ..actions.shake_ally_awake import ShakeAllyAwakeFactory
from ..battle_map import Map, map_position_toggled_cache, _get_free_coords_in_cartesian_range, \
    _get_cartesian_distance_coords
from ..combatant_coords import Coords
from ..effects.combatant_effect import CombatantEffect
from ..effects.effect import EffectType
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..spells.spell import SpellStats
from ..misc import roll_dice, ROUND_HORIZON, avg_roll
from ..conditions import Conditions, Condition, is_affected_by_any, get_swallower, apply_condition, \
    remove_condition
from ..actions.actoid import Actoid, ActoidFlags, FactoryFlags
from ..threat_utils import calculate_threat_in_delta
from ..threat_interfaces import DirectThreat
from ..factory_interfaces import DirectThreatFactory
import numpy as np

from ..utils.roll_types import ThreatModifierType, RollType

logger = logging.getLogger("Encounterra")


class SleepFactory(DirectThreatFactory):
    level = 1
    range = SpellStats.Range.FEET_90.value
    target = SpellStats.Target.RADIUS_20
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL
    dmg_type = None

    mean_sleep_hp = avg_roll((5, 8))
    max_sleep_hp = 40

    def __init__(self, action_type, caster, resource):
        super().__init__()
        self.action_type = action_type  # SLEEP, QUICKENED_SLEEP
        self.combatant = caster
        self.resource = resource
        self.flags |= FactoryFlags.PREVENT_ENDLESS_RECURSION

    def __str__(self):
        """
        Important for FSM building
        """
        return "SleepFactory"

    def get_ability_name(self):
        return "Sleep"

    def get_twinned_kwargs(self):
        return {'caster': self.combatant, 'resource': self.resource}

    def get_quickened_kwargs(self):
        return {'caster': self.combatant, 'resource': self.resource}

    def find_best_args(self, combatant):
        coord, _ = Map.get().find_best_placement_harmful_circular(combatant, SleepFactory.range, SpellStats.TRANSLATE_RADIUS[SleepFactory.target], self)
        return coord[0]

    def create_all(self, previous_action_in_dag=None):
        if get_swallower(self.combatant):
            return []
        # Here there really is no need to iterate over all coords. Just find the best score
        return [Sleep(self.find_best_args(self.combatant), self)]

    def create(self, coord):
        return Sleep(coord, self)

    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates threat to one specific target
        """
        if target.curr_hp > SleepFactory.max_sleep_hp:
            return 0
        if target.has_passive(Passive.CHARM_IMMUNITY):
            return 0
        if is_affected_by_any(target, Conditions.PARALYZED, Conditions.UNCONSCIOUS, Conditions.STUNNED):
            return 0
        if Map.get().get_cartesian_distance_combatants(self.combatant, target) > SleepFactory.range:
            return 0
        multiplier = min(1, SleepFactory.mean_sleep_hp / target.curr_hp)

        prevented_threat_out_acc = 0
        # Haste factories wouldn't change the result here, so we're omitting them
        # This is an approximation, we're only looking at the best action overall, not the action + bonus_action combo
        max_action_threat = 0
        for f in target.action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags and FactoryFlags.PREVENT_ENDLESS_RECURSION not in f[1].flags:
                max_action_threat = max(max_action_threat, f[1].calculate_max_threat())
        for f in target.bonus_action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags and FactoryFlags.PREVENT_ENDLESS_RECURSION not in f[1].flags:
                max_action_threat = max(max_action_threat, f[1].calculate_max_threat())
        prevented_threat_out_acc += max_action_threat

        mods = {ThreatModifierType.ROLL_TYPE: RollType.ADVANTAGE, ThreatModifierType.AUTO_CRIT: True}
        # Neglecting the auto-crit in melee range only
        threat_in_delta = min(target.curr_hp, calculate_threat_in_delta(target, 6, mods, FactoryFlags.IS_ATTACK_LIKE)[1])
        threat_round_total = prevented_threat_out_acc + threat_in_delta

        return threat_round_total * ROUND_HORIZON * multiplier

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0  # No need

    def calculate_max_threat(self):
        return Sleep(self.find_best_args(self.combatant), self).calculate_threat()


class Sleep(Actoid, LimitedDurationEffect, CombatantEffect, DirectThreat):

    def __init__(self, coord, factory,  **kwargs):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, factory.combatant, turns=10)
        affected = Map.get().get_combatants_affected_by_sphere_aoe(factory.combatant, SleepFactory.target, SleepFactory.type, coord)
        affected.sort(key=lambda cmbt: cmbt.curr_hp)
        put_to_sleep = []
        hp_acc = 0
        total_hp_affected = roll_dice((5, 8))
        for combatant in affected:
            if combatant.has_passive(Passive.CHARM_IMMUNITY):
                continue
            if hp_acc + combatant.curr_hp <= total_hp_affected:
                put_to_sleep.append(combatant)
                hp_acc += combatant.curr_hp
            else:
                break
        CombatantEffect.__init__(self, factory.combatant, put_to_sleep)
        self.origin = coord
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FIREBALL else "") + f"Sleep at {np.squeeze(self.origin)}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FIREBALL else "") + "Sleep"

    def get_effect_type(self):
        return EffectType.SLEEP

    def activate(self, **kwargs):
        if self.combatants:
            battle_map = Map.get()
            battle_map.effect_tracker.add(self)
            self.factory.combatant.concentration_effect = self
            for combatant in self.combatants:
                logger.info(f"{combatant} is put to sleep.")
                apply_condition(combatant, Condition(Conditions.UNCONSCIOUS | Conditions.AWAKENED_BY_DMG | Conditions.CAN_BE_SHAKEN_AWAKE, self.factory.combatant, self))
            enemies = battle_map.get_enemies(self.factory.combatant)
            for e in enemies:
                e.action_factories.append((Action.SHAKE_ALLY_AWAKE, ShakeAllyAwakeFactory(e)))
        else:
            logger.info(f"Sleep failed to affect anyone. The rolled HP wasn't high enough.")

    def _deactivate(self):
        self.factory.combatant.break_concentration()
        enemies = Map.get().get_enemies(self.factory.combatant)
        for e in enemies:
            e.action_factories = [factory for factory in e.action_factories if not isinstance(factory[1], ShakeAllyAwakeFactory)]

    def deactivate(self):
        for combatant in self.combatants:
            remove_condition(combatant, Conditions.UNCONSCIOUS | Conditions.AWAKENED_BY_DMG | Conditions.CAN_BE_SHAKEN_AWAKE)
        self.combatants.clear()
        self._deactivate()

    def deactivate_for_combatant(self, combatant):
        remove_condition(combatant, Conditions.UNCONSCIOUS | Conditions.AWAKENED_BY_DMG | Conditions.CAN_BE_SHAKEN_AWAKE)
        try:
            self.combatants.remove(combatant)
        except ValueError:  # Happens when the last affected combatant is awaked by dmg, the condition's already been removed in receive_dmg/receive_compound_dmg
            self._deactivate()
            return False
        if not self.combatants:
            self._deactivate()
            return False
        return True


    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        acc = 0
        battle_map = Map.get()
        for combatant in self.combatants:
            threat = self.factory.calculate_threat_to_target(combatant)
            # Discourage self-targeting
            acc += threat * (1 if battle_map.teams.are_enemies(self.factory.combatant, combatant) else -4 if combatant.is_alive() else 0)
        return acc

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        #self.get_eligible_coords.cache_clear()

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0  # Not relevant for this ability

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        if get_swallower(self.factory.combatant):
            return None
        battle_map = Map.get()
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return _get_free_coords_in_cartesian_range(
                battle_map.grid,
                Coords(self.origin).get(),  # not actually combatant coords
                distances,
                inflate_to_dist=self.factory.combatant.size.value,
                rng=SleepFactory.range,
                combatant_id=self.factory.combatant.id)
        elif _get_cartesian_distance_coords(battle_map.get_combatant_position(self.factory.combatant).get(), np.array([self.origin])) <= SleepFactory.range:
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
        return None
