import numpy as np

from simulator.combatant_coords import CombatantCoords
from simulator.effects.aoe_square_effect import AoeSquareEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.spells.spell import SpellStats
from simulator.actions.action_types import BonusAction
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.threat_utils import mean_dmg, dmg_decrement_for_ac_flat
from simulator.threat_interfaces import ThreatModifier, ThreatModifierFactory, AoEThreat
from functools import reduce, cache
from simulator.misc import ROUND_HORIZON, get_attacks, get_haste_eligile_attacks, roll_saving_throw, reconcile_roll_modifiers, SavingThrow, \
    Conditions
import logging

logger = logging.getLogger("EncounTroll")

class FaerieFireFactory(ThreatModifierFactory):
    level = 1
    range = SpellStats.Range.FEET_60.value
    target = SpellStats.Target.BOX_20
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL
    dmg_type = None


    def __init__(self, dc, action_type, caster, effect_tracker):
        super().__init__()
        self.dc = dc
        self.action_type = action_type  # QUICKENED_FAERIE_FIRE, FAERIE_FIRE
        self.caster = caster
        self.saving_throw = SavingThrow.DEX
        self.effect_tracker = effect_tracker

    def __str__(self):
        """
        Important for FSM building
        """
        return "FaerieFireFactory"

    def get_quickened_kwargs(self):
        return {'effect_tracker': self.effect_tracker, 'caster': self.caster}


    def get_eligible_targets(self, battle_map):
        ret = battle_map.get_allies_within_radius(self.caster, FaerieFireFactory.range)
        ret.append(self.caster)
        ret = [a for a in ret if len(a.haste_action_factories) == 0]
        return ret

    def create_all(self, battle_map):
        targets = self.get_eligible_targets(battle_map)
        return [FaerieFire(t, self) for t in targets]

    def create(self, target_combatant):
        return FaerieFire(target_combatant, self)

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        For the given target ally it finds the attack with the highest mean dmg across all enemies withing range. It then adds
        estimated dmg prevention given by the AC bonus and by the saving throw advantage.
        """
        return 0 # TODO

class FaerieFire(Actoid, LimitedDurationEffect, ThreatModifier, AoeSquareEffect):

    def __init__(self, coord, factory,  **kwargs):
        Actoid.__init__(actoid_flags=ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, turns=10)
        AoeSquareEffect.__init__(self, coord, FaerieFireFactory.target)
        self.factory = factory
        self.affected_combatants = []

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FAERIE_FIRE else "") + f"Faerie Fire at {self.target}"

    def is_affecting(self, combatant, battle_map):
        return combatant in self.affected_combatants

    def activate(self, battle_map):
        potentially_affected_combatants = battle_map.get_combatants_affected_by_aoe(self.factory.caster, FaerieFireFactory.target, FaerieFireFactory.type, self.coord)
        for pac in potentially_affected_combatants:
            st = self.factory.saving_throw
            saved = roll_saving_throw(pac.saving_throws[st], self.factory.dc, reconcile_roll_modifiers(pac.saving_throws_roll_mod[st]))
            if not saved:
                pac.remove_condition(Conditions.INVISIBLE)
                self.affected_combatants.append(pac)


    def deactivate(self, battle_map):
        pass  # TODO remove concentration?

    def clear_cache(self):
        self.calculate_threat.cache_clear()

    @cache
    def calculate_threat(self, combatant, battle_map, combatant_coords: CombatantCoords = None, *args, **kwargs):
        return 0  # TODO

    def calculate_threat_mod(self, battle_map, modified_stats, *args, **kwargs):
        return 0  # Not relevant for this ability

    def threat_on_end_of_turn(self, battle_map, target, *args, **kwargs):
        return 0

    def threat_on_enter(self, battle_map, target, *args, **kwargs):
        return 0

    def threat_on_start_of_turn(self, battle_map, target, *args, **kwargs):
        return 0

    def threat_on_move_within(self, battle_map, target, *args, **kwargs):
        return 0

    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        return battle_map.get_free_coords_in_cartesian_range(CombatantCoords(self.coord),  # not actually combatant coords
                                                             distances,
                                                             inflate_to_size=self.factory.caster.size,
                                                             rng=FaerieFireFactory.range, combatant=self.factory.caster)

    def is_current_coord_eligible(self, battle_map):
        return battle_map.get_cartesian_distance(self.factory.caster, np.array([self.coord])) <= FaerieFireFactory.range

    def on_enter(self, combatant):
        pass

    def on_move_within(self, combatant):
        pass

    def on_start_of_turn(self, combatant):
        pass

    def on_end_of_turn(self, combatant):
        pass