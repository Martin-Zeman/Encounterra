from simulator.action_resolver import resolve_dmg_saving_throw
from simulator.action_types import BonusActionOrdering, BonusAction
from simulator.combatant_coords import CombatantCoords
from simulator.effects.aoe_spheric_effect import AoeSphericEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.spells.spell import SpellStats
from simulator.misc import SavingThrow, DamageType, avg_roll, roll_spell_dmg, Conditions
from simulator.actions.actoid import Actoid, ActoidFlags, FactoryFlags
from simulator.threat import mean_dmg_dc_attack
from simulator.threat_calculator import DirectThreat, DirectThreatFactory, AoEThreatFactory
import numpy as np

class HungerOfHadarFactory(DirectThreatFactory, AoEThreatFactory):
    def __init__(self, dc, action_type, caster, **kwargs):
        super().__init__()
        self.flags |= FactoryFlags.DEX_SAVE_APPLIES
        self.bonus_action_ordering = BonusActionOrdering.INDEPENDENT  # In case this became a bonus action
        self.dc = dc
        self.action_type = action_type  # HUNGER_OF_HADAR, QUICKENED_HUNGER_OF_HADAR
        self.saving_throw = SavingThrow.DEX
        self.dmg_dice = "2d6"
        self.caster = caster


    def __str__(self):
        """
        Important for FSM building
        """
        return "HungerOfHadarFactory"

    def find_best_args(self, combatant, battle_map):
        # TODO Deprecated
        coord, _, _ = battle_map.find_best_placement_harmful_circular(combatant, HungerOfHadar.spell_range.value, SpellStats.TRANSLATE_RADIUS[HungerOfHadar.target])
        return coord

    def create_best(self, combatant, battle_map, **kwargs):
        return HungerOfHadar(self.find_best_args(combatant, battle_map), self,  **kwargs)

    def create_all(self, battle_map):
        # Here there really is no need to iterate over all coords. Just find the best score
        return [HungerOfHadar(self.find_best_args(self.caster, battle_map), self)]

    def create(self, coord):
        return HungerOfHadar(coord, self)


    def calculate_threat_approx_mod(self, battle_map, modified_stats, *args, **kwargs):
        return 0 # no need

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        Calculates threat to one specific target
        """
        try:
            consider_dist = kwargs["consider_dist"]
        except KeyError:
            consider_dist = False

        if not consider_dist or battle_map.get_cartesian_distance(self.caster, target) <= HungerOfHadar.spell_range.value + SpellStats.TRANSLATE_RADIUS[HungerOfHadar.target]:
            # The 0.5 is a heuristic which expresses the fact that most targets would leave the area immediately
            return avg_roll(self.dmg_dice) + 0.5 * mean_dmg_dc_attack(self.dc, self.dmg_dice, False, target.saving_throws[self.saving_throw])
        return 0

    def calculate_threat_to_target_mod(self, battle_map, target, modified_stats, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0 # No need

    def threat_on_end_of_turn(self, battle_map, target, *args, **kwargs):
        return mean_dmg_dc_attack(self.dc, self.dmg_dice, False, target.saving_throws[self.saving_throw], target.is_resistant_to(DamageType.Acid))

    def threat_on_enter(self, battle_map, target, *args, **kwargs):
        return 0

    def threat_on_start_of_turn(self, battle_map, target, *args, **kwargs):
        threat = avg_roll(self.dmg_dice)
        return threat if not target.is_resistant_to(HungerOfHadar.dmg_type) else threat / 2

class HungerOfHadar(Actoid, LimitedDurationEffect, AoeSphericEffect, DirectThreat):

    level = 3
    spell_range = SpellStats.Range.FEET_150
    target = SpellStats.Target.RADIUS_20
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = True
    type = SpellStats.Type.HARMFUL
    dmg_type = DamageType.Cold


    def __init__(self, coord, factory,  **kwargs):
        super().__init__(actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_DIRECT_THREAT)
        LimitedDurationEffect.__init__(self, turns=10)
        AoeSphericEffect.__init__(self, coord, SpellStats.TRANSLATE_RADIUS[HungerOfHadar.target])
        self.factory = factory

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_HUNGER_OF_HADAR else "") + f"HungerOfHadar at {np.squeeze(self.coord)}"


    def on_start_of_turn(self, combatant):
        combatant.apply_condition(Conditions.BLINDED)
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        combatant.receive_dmg(dmg, self.dmg_type)

    def on_end_of_turn(self, combatant):
        combatant.apply_condition(Conditions.BLINDED)
        dmg = roll_spell_dmg(self.factory.dmg_dice)
        self.dmg_type = DamageType.Acid
        resolve_dmg_saving_throw(self, dmg, combatant)
        self.dmg_type = DamageType.Cold

    def on_enter(self, combatant):
        combatant.apply_condition(Conditions.BLINDED)

    def is_affecting(self, combatant, battle_map):
        coords = self.get_affected_coords(battle_map)
        return battle_map.get_hop_distance(combatant, coords) == 0


    def activate(self):
        pass

    def deactivate(self):
        pass  # TODO remove concentration?

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        affected = battle_map.get_combatants_affected_by_aoe(self.factory.caster, HungerOfHadar.target, HungerOfHadar.type, self.coord)
        acc = 0
        for aff in affected:
            acc += avg_roll(self.factory.dmg_dice)  # the initial cold dmg
            # The 0.5 is a heuristic which expresses the fact that most targets would leave the area immediately
            acc += 0.5 * mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, False, aff.saving_throws[self.factory.saving_throw], aff.is_resistant_to(DamageType.Acid))
        return acc

    def get_eligible_coords(self, battle_map):
        return battle_map.get_free_coords_in_cartesian_range(CombatantCoords(self.coord),  # not actually combatant coords
                                                             inflate_to_size=self.factory.caster.size,
                                                             rng=self.spell_range.value, combatant=self.factory.caster)
