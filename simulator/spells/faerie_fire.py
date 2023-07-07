import numpy as np

from simulator.battle_map import Map
from simulator.combatant_coords import CombatantCoords
from simulator.effects.aoe_square_effect import AoeSquareEffect
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.effect import EffectType
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.spells.spell import SpellStats
from simulator.actions.action_types import BonusAction
from simulator.actions.actoid import Actoid, ActoidFlags, FactoryFlags
from simulator.threat_interfaces import ThreatModifier, ThreatModifierFactory
from functools import cache
from simulator.misc import roll_saving_throw, reconcile_roll_types, SavingThrow, Conditions
import logging

from simulator.threat_utils import calculate_threat_in_delta
from simulator.utils.roll_types import ThreatModifierType, RollType

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
        self.flags |= FactoryFlags.USES_CALCULATE_THREAT_IN_DELTA
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


    def find_best_args(self, combatant):
        coord, _, _ = Map.get().find_best_placement_harmful_square(combatant, FaerieFireFactory.range, SpellStats.TRANSLATE_BOX[FaerieFireFactory.target])
        return coord[0]

    def create_all(self):
        # Here there really is no need to iterate over all coords. Just find the best score
        return [FaerieFire(self.find_best_args(self.combatant), self)]

    def create(self, coord):
        return FaerieFire(coord, self)

    def calculate_threat_to_target(self, target, **kwargs):
        """
        For the given target ally it finds the attack with the highest mean dmg across all enemies withing range. It then adds
        estimated dmg prevention given by the AC bonus and by the saving throw advantage.
        """
        ret = calculate_threat_in_delta(target, 6, {ThreatModifierType.ROLL_TYPE: RollType.ADVANTAGE}, FactoryFlags.IS_ATTACK_LIKE)[1]
        logger.info(f"MY DEBUG {self} threat = {ret}")
        return ret

    def calculate_max_threat(self):
        ret = FaerieFire(self.find_best_args(self.combatant), self).calculate_threat()
        logger.info(f"MY DEBUG {self} calculate_max_threat = {ret}")
        return ret

class FaerieFire(Actoid, LimitedDurationEffect, ThreatModifier, AoeSquareEffect, CombatantEffect):

    def __init__(self, coord, factory,  **kwargs):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, turns=10)
        AoeSquareEffect.__init__(self, coord, SpellStats.TRANSLATE_BOX[FaerieFireFactory.target])
        CombatantEffect.__init__(self, [])
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FAERIE_FIRE else "") + f"Faerie Fire at {self.origin}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FAERIE_FIRE else "") + "Faerie Fire"

    def get_effect_type(self):
        return EffectType.FAERIE_FIRE

    def activate(self):
        potentially_affected_combatants = Map.get().get_combatants_affected_by_aoe(self.factory.combatant, FaerieFireFactory.target, FaerieFireFactory.type, self.origin)
        failed_count = 0
        for pac in potentially_affected_combatants:
            st = self.factory.saving_throw
            if not roll_saving_throw(pac.saving_throws[st], self.factory.dc, reconcile_roll_types(pac.saving_throws_roll_type_mod[st])):
                logger.info(f"{pac} failed save against Faerie Fire")
                failed_count += 1
                pac.remove_condition(Conditions.INVISIBLE)
                self.combatants.append(pac)
            else:
                logger.info(f"{pac} saved against Faerie Fire")
        if failed_count:
            self.factory.combatant.concentration_effect = self
            Map.get().effect_tracker.add(self)


    def deactivate(self):
        self.factory.combatant.break_concentration()
        self.combatants.clear()


    def calculate_threat(self, **kwargs):
        battle_map = Map.get()
        affected = battle_map.get_combatants_affected_by_aoe(self.factory.combatant, FaerieFireFactory.target, FaerieFireFactory.type, self.origin)
        acc = 0
        for aff in affected:
            threat_delta = calculate_threat_in_delta(aff, 6, {ThreatModifierType.ROLL_TYPE: RollType.ADVANTAGE}, FactoryFlags.IS_ATTACK_LIKE)[1]
            acc += (1 if battle_map.teams.are_enemies(self.factory.combatant, aff) else -3) * threat_delta
        logger.info(f"MY DEBUG {self} calculate_threat = {acc}")
        return acc

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