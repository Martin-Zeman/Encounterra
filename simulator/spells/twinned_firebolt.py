from simulator.spells.firebolt import FireboltFactory
from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, percent_of_curr_hp, avg_roll
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import reduce

from simulator.threat import mean_dmg
from simulator.threat_calculator import DirectThreat, DirectThreatFactory
from itertools import combinations
import logging

from simulator.utils.roll_modifiers import RollModifier, ROLL_MODIFIER_CRIT, ROLL_MODIFIER

logger = logging.getLogger(__name__)

class TwinnedFireboltFactory(DirectThreatFactory):
    def __init__(self, to_hit, action_type, caster):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.to_hit = to_hit
        self.action_type = action_type  # FIREBOLT, TWINNED_FIREBOLT, QUICKENED_FIREBOLT TODO
        self.dmg_dice = FireboltFactory.get_dmg_dice(caster.level)
        self.caster = caster

    def __str__(self):
        """
        Important for FSM building
        """
        return "TwinnedFireboltFactory"

    def find_best_args(self, combatant, battle_map):
        # TODO Deprecated
        # TODO Should this include action type? Cause for a twinned version you would need multiple targets
        potential_targets = battle_map.get_enemies_within_radius(combatant, TwinnedFirebolt.spell_range.value)
        hp_percentages = [percent_of_curr_hp(pt, mean_dmg(self.to_hit, self.dmg_dice, 0, pt.ac, 1)) for pt in potential_targets]
        potential_targets = list(zip(potential_targets, hp_percentages))
        potential_targets.sort(key=lambda e: e[1], reverse=True)
        try:
            target2 = potential_targets[1][0]
        except IndexError:
            target2 = None
        return potential_targets[0][0], target2

    def create_best(self, combatant, battle_map):
        return TwinnedFirebolt(self.find_best_args(combatant, battle_map), self)

    # def create_mock(self):
    #     return TwinnedFirebolt(None, self)

    def get_eligible_targets(self, battle_map):
        return combinations(battle_map.get_enemies(self.caster), 2)

    def create_all(self, battle_map):
        targets = self.get_eligible_targets(battle_map)
        return [TwinnedFirebolt(t, self) for t in targets]

    def create(self, targets):
        return TwinnedFirebolt(targets, self)

    # def calculate_threat_approx(self, battle_map, *args, **kwargs):
    #     """
    #     Calculates the average dmg over all targets in range
    #     """
    #     potential_targets = battle_map.get_enemies_within_radius(TwinnedFirebolt.spell_range.value)
    #     dmg_dice = FireboltFactory.get_dmg_dice(self.caster.level)
    #     dmg_acc = accumulate(potential_targets, lambda pt: mean_dmg(self.to_hit, dmg_dice, 0, pt.ac, 1, pt.is_resistant_to(TwinnedFirebolt.dmg_type)))
    #     dmg_acc /= len(potential_targets)
    #     return dmg_acc * ROUND_HORIZON

    def calculate_threat_approx_mod(self, battle_map, modified_stats, *args, **kwargs):
        """
        Calculates the average dmg increment over all targets in range
        """
        try:
            mod_to_hit_flat = modified_stats['to_hit_flat']
        except KeyError:
            mod_to_hit_flat = 0
        try:
            mod_to_hit_die = modified_stats['to_hit_die']
        except KeyError:
            mod_to_hit_die = '0d0'
        try:
            roll_modifier = modified_stats['roll_modifier']
        except KeyError:
            roll_modifier = RollModifier.STRAIGHT

            to_hit_total = self.to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
            total_crit = ROLL_MODIFIER_CRIT[roll_modifier]

            potential_targets = battle_map.get_enemies_within_radius(TwinnedFirebolt.spell_range.value)
            dmg_acc = reduce(
                lambda acc, pt: acc + mean_dmg(to_hit_total + ROLL_MODIFIER[roll_modifier][pt.ac - to_hit_total], self.dmg_dice, 0, pt.ac,
                                               total_crit, pt.is_resistant_to(TwinnedFirebolt.dmg_type))
                                - mean_dmg(self.to_hit, self.dmg_dice, 0, pt.ac, 1, pt.is_resistant_to(TwinnedFirebolt.dmg_type)),
                potential_targets)
            dmg_acc /= len(potential_targets)
            return dmg_acc * 2
        except IndexError:
            return 0

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        if battle_map.get_cartesian_distance(self.caster, target) <= TwinnedFirebolt.spell_range.value:
            # Cannot target the same combatant twice
            return mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(TwinnedFirebolt.dmg_type))
        else:
            return 0

    def calculate_threat_to_target_mod(self, battle_map, target, modified_stats, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications.
        This is useful calculating the potential reduction of threat_in caused by abilities of enemies, e.g. advantage on saving throw
        against fireball or bane on attack rolls etc.
        """
        try:
            mod_to_hit_flat = modified_stats['to_hit_flat']
        except KeyError:
            mod_to_hit_flat = 0
        try:
            mod_to_hit_die = modified_stats['to_hit_die']
        except KeyError:
            mod_to_hit_die = '0d0'
        try:
            roll_modifier = modified_stats['roll_modifier']
        except KeyError:
            roll_modifier = RollModifier.STRAIGHT

        to_hit_total = self.to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
        to_hit_total += ROLL_MODIFIER[roll_modifier][target.ac - to_hit_total]
        total_crit = ROLL_MODIFIER_CRIT[roll_modifier]

        return mean_dmg(to_hit_total, self.dmg_dice, 0, target.ac, total_crit, target.is_resistant_to(TwinnedFirebolt.dmg_type)) - mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(
                    TwinnedFirebolt.dmg_type))

class TwinnedFirebolt(Actoid, DirectThreat):

    level = 0
    spell_range = SpellStats.Range.FEET_120
    target = SpellStats.Target.TWO_CREATURES
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.HARMFUL
    dc = None
    dmg_type = DamageType.Fire


    def __init__(self, targets, factory, **kwargs):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_ATTACK_LIKE | ActoidFlags.IS_DIRECT_THREAT)
        self.targets = targets
        self.factory = factory
        self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.roll_modifier = RollModifier.STRAIGHT

    def __str__(self):
        return f"Twinned Firebolt on {self.targets[0]} and {self.targets[1]}"

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        dmg_acc = mean_dmg(self.factory.to_hit, self.factory.dmg_dice, 0, self.targets[0].ac, 1, self.targets[0].is_resistant_to(TwinnedFirebolt.dmg_type))
        if self.targets[1] is not None:
            dmg_acc += mean_dmg(self.factory.to_hit, self.factory.dmg_dice, 0, self.targets[1].ac, 1, self.targets[1].is_resistant_to(TwinnedFirebolt.dmg_type))
        return dmg_acc

    def get_eligible_coords(self, battle_map):
        coords_for_fist = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[0]),
                                                                        inflate_to_size=self.factory.caster.size,
                                                                        rng=self.spell_range.value,
                                                                        combatant=self.factory.caster)
        coords_for_second = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[1]),
                                                                          inflate_to_size=self.factory.caster.size,
                                                                          rng=self.spell_range.value,
                                                                          combatant=self.factory.caster)
        return coords_for_fist.intersection(coords_for_second)
