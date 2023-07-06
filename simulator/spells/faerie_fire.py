import numpy as np

from simulator.battle_map import Map
from simulator.combatant_coords import CombatantCoords
from simulator.effects.aoe_square_effect import AoeSquareEffect
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.effect import EffectType
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.spells.spell import SpellStats
from simulator.actions.action_types import BonusAction
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.threat_interfaces import ThreatModifier, ThreatModifierFactory
from functools import cache
from simulator.misc import roll_saving_throw, reconcile_roll_types, SavingThrow, Conditions
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


    def __init__(self, dc, action_type, caster):
        super().__init__()
        self.dc = dc
        self.action_type = action_type  # QUICKENED_FAERIE_FIRE, FAERIE_FIRE
        self.combatant = caster
        self.saving_throw = SavingThrow.DEX

    def __str__(self):
        """
        Important for FSM building
        """
        return "FaerieFireFactory"

    def get_quickened_kwargs(self):
        return {'combatant': self.combatant}


    def get_eligible_targets(self):
        # TODO
        swallower = self.combatant.get_swallower()
        if swallower:
            return []
        ret = [a for a in Map.get().get_allies_within_radius(self.combatant, FaerieFireFactory.range) if not a.is_affected_by(Conditions.SWALLOWED)]
        ret.append(self.combatant)
        ret = [a for a in ret if len(a.haste_action_factories) == 0]
        return ret

    def create_all(self):
        targets = self.get_eligible_targets()
        return [FaerieFire(t, self) for t in targets]

    def create(self, target_combatant):
        return FaerieFire(target_combatant, self)

    def calculate_threat_to_target(self, target, *args, **kwargs):
        """
        For the given target ally it finds the attack with the highest mean dmg across all enemies withing range. It then adds
        estimated dmg prevention given by the AC bonus and by the saving throw advantage.
        """
        return 0 # TODO

    def calculate_max_threat(self):
        return 0  # TODO

class FaerieFire(Actoid, LimitedDurationEffect, ThreatModifier, AoeSquareEffect, CombatantEffect):

    def __init__(self, coord, factory,  **kwargs):
        Actoid.__init__(actoid_flags=ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, turns=10)
        AoeSquareEffect.__init__(self, coord, FaerieFireFactory.target)
        CombatantEffect.__init__(self, [])
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FAERIE_FIRE else "") + f"Faerie Fire at {self.origin}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FAERIE_FIRE else "") + "Faerie Fire"

    def get_effect_type(self):
        return EffectType.FAERIE_FIRE

    def activate(self):
        Map.get().effect_tracker.add(self)
        self.factory.combatant.concentration_effect = self
        potentially_affected_combatants = Map.get().get_combatants_affected_by_aoe(self.factory.combatant, FaerieFireFactory.target, FaerieFireFactory.type, self.origin)
        for pac in potentially_affected_combatants:
            st = self.factory.saving_throw
            saved = roll_saving_throw(pac.saving_throws[st], self.factory.dc, reconcile_roll_types(pac.saving_throws_roll_type_mod[st]))
            if not saved:
                pac.remove_condition(Conditions.INVISIBLE)
                self.combatants.append(pac)


    def deactivate(self):
        self.factory.combatant.get_current_form().concentration_effect = None
        self.combatants.clear()


    def calculate_threat(self, *args, **kwargs):
        return 0  # TODO

    def threat_on_end_of_turn(self, target, *args, **kwargs):
        return 0

    def threat_on_enter(self, target, *args, **kwargs):
        return 0

    def threat_on_start_of_turn(self, target, *args, **kwargs):
        return 0

    def threat_on_move_within(self, target, *args, **kwargs):
        return 0

    def get_eligible_coords(self, distances, shortest_paths):
        return Map.get().get_free_coords_in_cartesian_range(CombatantCoords(self.origin),  # not actually combatant coords
                                                             distances,
                                                             inflate_to_size=self.factory.combatant.size,
                                                             rng=FaerieFireFactory.range, combatant=self.factory.combatant)

    def is_current_coord_eligible(self):
        if self.factory.combatant.get_swallower():
            return False
        battle_map = Map.get()
        return battle_map.get_cartesian_distance(self.factory.combatant, np.array([self.origin])) <= FaerieFireFactory.range

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