from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, mean_dmg, percent_of_curr_hp
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import reduce
from simulator.threat_calculator import DirectThreat, DirectThreatFactory
from simulator.spells.firebolt import FireboltFactory
from simulator.misc import ROUND_HORIZON
import logging

logger = logging.getLogger(__name__)

class TwinnedFireboltFactory(DirectThreatFactory):
    def __init__(self, to_hit, combatant_level, action_type):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.to_hit = to_hit
        self.action_type = action_type  # FIREBOLT, TWINNED_FIREBOLT, QUICKENED_FIREBOLT
        self.dmg_dice = self.get_dmg_dice(combatant_level)

    def find_best_args(self, combatant, battle_map):
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
            to_hit_bonus = modified_stats['to_hit']
            potential_targets = battle_map.get_enemies_within_radius(TwinnedFirebolt.spell_range.value)
            dmg_acc = reduce(lambda acc, pt: acc + mean_dmg(self.to_hit + to_hit_bonus, self.dmg_dice, 0, pt.ac, 1, pt.is_resistant_to(TwinnedFirebolt.dmg_type)) - mean_dmg(self.to_hit, self.dmg_dice, 0, pt.ac, 1, pt.is_resistant_to(TwinnedFirebolt.dmg_type)), potential_targets)
            dmg_acc /= len(potential_targets)
            return dmg_acc * 2
        except IndexError:
            return 0

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        if battle_map.get_cartesian_distance(self.caster, target) <= TwinnedFirebolt.spell_range.value:
            return mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(TwinnedFirebolt.dmg_type))
        else:
            return 0

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
        super().__init__(actoid_type=ActoidFlags.IS_SPELL | ActoidFlags.IS_ATTACK_LIKE | ActoidFlags.IS_DIRECT_THREAT)
        self.targets = targets
        self.factory = factory
        self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True

    def __str__(self):
        return "Twinned Firebolt"

    # @staticmethod
    # def calculate_threat_approx(combatant, battle_map, *args, **kwargs):
    #     potential_targets = battle_map.get_enemies_within_radius(TwinnedFirebolt.spell_range.value)
    #     dmg_dice = TwinnedFireboltFactory.get_dmg_dice(combatant.level)
    #     dmg_acc = accumulate(potential_targets, lambda pt: mean_dmg(combatant.spell_to_hit, dmg_dice, 0, pt.ac, 1, pt.is_resistant_to(TwinnedFirebolt.dmg_type)))
    #     dmg_acc /= len(potential_targets)
    #     dmg_acc *= 2
    #     return dmg_acc

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        dmg_acc = mean_dmg(self.factory.to_hit, self.factory.dmg_dice, 0, self.targets[0].ac, 1, self.target.is_resistant_to(TwinnedFirebolt.dmg_type))
        if self.targets[1] is not None:
            dmg_acc += mean_dmg(self.factory.to_hit, self.factory.dmg_dice, 0, self.targets[1].ac, 1, self.target.is_resistant_to(TwinnedFirebolt.dmg_type))
        return dmg_acc


