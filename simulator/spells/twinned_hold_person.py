from simulator.actions.action_types import BonusAction
from simulator.battle_map import Map
from simulator.effects.effect import EffectType
from simulator.effects.end_of_turn_combatant_effect import EndOfTurnEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.spells.hold_person import HoldPersonFactory
from simulator.spells.spell import SpellStats
from simulator.misc import SavingThrow, Conditions, ConditionWithoutDC
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import cache

from simulator.threat_utils import get_saving_throw_success_prob
from simulator.threat_interfaces import ThreatModifierFactory, ThreatModifier
import logging


logger = logging.getLogger("EncounTroll")

class TwinnedHoldPersonFactory(ThreatModifierFactory):
    level = 2
    range = SpellStats.Range.FEET_60.value
    target = SpellStats.Target.TWO_CREATURES
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL

    def __init__(self, dc, action_type, caster):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.dc = dc
        self.action_type = action_type  # HOLD_PERSON, QUICKENED_HOLD_PERSON
        self.combatant = caster
        self.saving_throw = SavingThrow.WIS


    def __str__(self):
        """
        Important for FSM building
        """
        return "HoldPersonFactory"


    def get_twinned_kwargs(self):
        return {'dc': self.dc, 'caster': self.combatant}

    def get_quickened_kwargs(self):
        return {'dc': self.dc, 'caster': self.combatant}


    def create_all(self):
        battle_map = Map.get()
        targets = battle_map.get_enemies(self.combatant)
        return [TwinnedHoldPerson(t, self) for t in targets]

    def create(self, target_combatant):
        return TwinnedHoldPerson(target_combatant, self)


    def calculate_threat_to_target(self, target, *args, **kwargs):
        if target.is_affected_by_any(Conditions.PARALYZED):
            return 0
        battle_map = Map.get()
        if battle_map.get_cartesian_distance(self.combatant, target) <= TwinnedHoldPersonFactory.range:
            return 0 * get_saving_throw_success_prob(self.dc, target.saving_throws[self.saving_throw])# TODO
        return 0


class TwinnedHoldPerson(Actoid, LimitedDurationEffect, EndOfTurnEffect, ThreatModifier):
    def __init__(self, target, factory, **kwargs):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, turns=10)
        EndOfTurnEffect.__init__(self, factory.combatant, factory.saving_throw, factory.dc)
        self.target = target
        self.factory = factory


    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_HOLD_PERSON else "") + f"Hold Person on {self.target}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_HOLD_PERSON else "") + "Hold Person"

    def get_effect_type(self):
        return EffectType.HOLD_PERSON

    def activate(self,):
        self.target.apply_condition(ConditionWithoutDC(Conditions.PARALYZED, self))

    def deactivate(self):
        self.target.remove_condition(Conditions.PARALYZED, self)

    def is_affecting(self, combatant):
        return combatant is self.target


    def calculate_threat(self, *args, **kwargs):
        return self.factory.calculate_threat_to_target(self.target)


    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        return battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.target),
                                                             distances,
                                                             inflate_to_size=self.factory.combatant.size,
                                                             rng=HoldPersonFactory.range, combatant=self.factory.combatant)

    def is_current_coord_eligible(self):
        if self.factory.combatant.get_swallower():
            return False  # Impossible when blinded
        battle_map = Map.get()
        return battle_map.get_cartesian_distance(self.factory.combatant, self.target) <= HoldPersonFactory.range
