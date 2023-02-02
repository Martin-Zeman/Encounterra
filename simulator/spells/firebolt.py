from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, mean_dmg, percent_of_curr_hp, ROUND_HORIZON, RollModifier, avg_roll, ROLL_MODIFIER, \
    ROLL_MODIFIER_CRIT
from simulator.actions.actoid import Actoid
from functools import reduce
from simulator.threat_calculator import DirectThreat, FactoryThreat
import logging

logger = logging.getLogger(__name__)

class FireboltFactory(FactoryThreat):
    def __init__(self, to_hit, combatant_level, action_type, caster):
        self.to_hit = to_hit
        self.action_type = action_type  # FIREBOLT, TWINNED_FIREBOLT, QUICKENED_FIREBOLT
        self.dmg_dice = self.get_dmg_dice(combatant_level)
        self.caster = caster

    @staticmethod
    def get_dmg_dice(level):
        match level:
            case lvl if 1 <= lvl <= 4:
                return "1d10"
            case lvl if 5 <= lvl <= 10:
                return "2d10"
            case lvl if 11 <= lvl <= 16:
                return "3d10"
            case lvl if lvl <= 17:
                return "4d10"
            case _:
                logger.error("Incorrect caster level of Firebolt")
                return "1d10"

    def find_best_args(self, combatant, battle_map):
        # TODO Should this include action type? Cause for a twinned version you would need multiple targets
        potential_targets = battle_map.get_enemies_within_radius(combatant, Firebolt.spell_range.value)
        hp_percentages = [percent_of_curr_hp(pt, mean_dmg(self.to_hit, self.dmg_dice, 0, pt.ac, 1)) for pt in potential_targets]
        potential_targets = list(zip(potential_targets, hp_percentages))
        potential_targets.sort(key=lambda e: e[1], reverse=True)
        return potential_targets[0][0]

    def create_best(self, combatant, battle_map):
        return Firebolt(self.find_best_args(combatant, battle_map), self)

    # def calculate_threat_approx(self, battle_map, *args, **kwargs):
    #     """
    #     Calculates the average dmg over all targets in range
    #     """
    #     potential_targets = battle_map.get_enemies_within_radius(Firebolt.spell_range.value)
    #     dmg_dice = FireboltFactory.get_dmg_dice(self.caster.level)
    #     dmg_acc = accumulate(potential_targets, lambda pt: mean_dmg(self.to_hit, dmg_dice, 0, pt.ac, 1, pt.is_resistant_to(Firebolt.dmg_type)))
    #     dmg_acc /= len(potential_targets)
    #     return dmg_acc

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
            mod_to_hit_die = ''
        try:
            roll_modifier = modified_stats['roll_modifier']
        except KeyError:
            roll_modifier = RollModifier.STRAIGHT

            to_hit_total = self.to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
            total_crit = len(self.crit_range) * ROLL_MODIFIER_CRIT[roll_modifier]

            potential_targets = battle_map.get_enemies_within_radius(Firebolt.spell_range.value)
            dmg_acc = reduce(lambda acc, pt: acc + mean_dmg(to_hit_total + ROLL_MODIFIER[roll_modifier][pt.ac - to_hit_total], self.dmg_dice, 0, pt.ac, total_crit, pt.is_resistant_to(Firebolt.dmg_type)) - mean_dmg(self.to_hit, self.dmg_dice, 0, pt.ac, 1, pt.is_resistant_to(Firebolt.dmg_type)), potential_targets)
            dmg_acc /= len(potential_targets)
            return dmg_acc
        except KeyError:
            return 0

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        if battle_map.get_cartesian_distance(self.caster, target) <= Firebolt.spell_range.value:
            return mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(Firebolt.dmg_type))
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
            mod_to_hit_die = ''
        try:
            roll_modifier = modified_stats['roll_modifier']
        except KeyError:
            roll_modifier = RollModifier.STRAIGHT

        to_hit_total = self.to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
        to_hit_total += ROLL_MODIFIER[roll_modifier][target.ac - to_hit_total]
        total_crit = len(self.crit_range) * ROLL_MODIFIER_CRIT[roll_modifier]

        return mean_dmg(to_hit_total, self.dmg_dice, 0, target.ac, total_crit, target.is_resistant_to(Firebolt.dmg_type)) - mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(
                    Firebolt.dmg_type))


class Firebolt(Actoid, DirectThreat):

    level = 0
    spell_range = SpellStats.Range.FEET_120
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.HARMFUL
    dc = None
    dmg_type = DamageType.Fire


    def __init__(self, target, factory, **kwargs):
        super().__init__(actoid_type=Actoid.Type.IS_SPELL, is_direct_dmg_dealing=True)
        self.target = target
        self.factory = factory
        self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        return mean_dmg(self.factory.to_hit, self.factory.dmg_dice, 0, self.target.ac, 1, self.target.is_resistant_to(Firebolt.dmg_type))

