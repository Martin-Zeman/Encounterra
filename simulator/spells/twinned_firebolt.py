from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, mean_dmg, percent_of_curr_hp
from simulator.actions.actoid import Actoid
from itertools import accumulate
from simulator.threat_calculator import DirectThreat, FactoryThreat
import logging

logger = logging.getLogger(__name__)

class TwinnedFireboltFactory(FactoryThreat):
    def __init__(self, to_hit, combatant_level, action_type):
        self.to_hit = to_hit
        self.action_type = action_type  # FIREBOLT, TWINNED_FIREBOLT, QUICKENED_FIREBOLT
        self.dmg_dice = self.get_dmg_dice(combatant_level)

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

    def calculate_threat_approx(self, battle_map, *args, **kwargs):
        # TODO
        return 0

    def calculate_threat_approx_mod(self, battle_map, modified_stats, *args, **kwargs):
        return 0

    def calculate_threat_approx(self, battle_map, *args, **kwargs):
        """
        Calculates the average dmg over all targets in range
        """
        potential_targets = battle_map.get_enemies_within_radius(Firebolt.spell_range.value)
        dmg_dice = FireboltFactory.get_dmg_dice(self.caster.level)
        dmg_acc = accumulate(potential_targets, lambda pt: mean_dmg(self.to_hit, dmg_dice, 0, pt.ac, 1, pt.is_resistant_to(Firebolt.dmg_type)))
        dmg_acc /= len(potential_targets)
        return dmg_acc * ROUND_HORIZON

    def calculate_threat_approx_mod(self, battle_map, modified_stats, *args, **kwargs):
        """
        Calculates the average dmg increment over all targets in range
        """
        try:
            to_hit_bonus = modified_stats['to_hit']
            potential_targets = battle_map.get_enemies_within_radius(Firebolt.spell_range.value)
            dmg_acc = accumulate(potential_targets,
                                 lambda pt: (self.to_hit, self.dmg_dice, 0, pt.ac, to_hit_bonus, 1,   pt.is_resistant_to(Firebolt.dmg_type)))
            dmg_acc /= len(potential_targets)
            return dmg_acc
        except IndexError:
            return 0

class TwinnedFirebolt(Actoid, DirectThreat):

    level = 0
    spell_range = SpellStats.Range.FEET_120
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.HARMFUL
    dc = None
    dmg_type = DamageType.Fire


    def __init__(self, targets, factory, **kwargs):
        super().__init__(actoid_type=Actoid.Type.IS_SPELL, is_direct_dmg_dealing=True)
        self.targets = targets
        self.factory = factory
        self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True

    @staticmethod
    def calculate_threat_approx(combatant, battle_map, *args, **kwargs):
        potential_targets = battle_map.get_enemies_within_radius(TwinnedFirebolt.spell_range.value)
        dmg_dice = TwinnedFireboltFactory.get_dmg_dice(combatant.level)
        dmg_acc = accumulate(potential_targets, lambda pt: mean_dmg(combatant.spell_to_hit, dmg_dice, 0, pt.ac, 1, pt.is_resistant_to(TwinnedFirebolt.dmg_type)))
        dmg_acc /= len(potential_targets)
        dmg_acc *= 2
        return dmg_acc

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        dmg_acc = mean_dmg(self.factory.to_hit, self.factory.dmg_dice, 0, self.targets[0].ac, 1, self.target.is_resistant_to(TwinnedFirebolt.dmg_type))
        if self.targets[1] is not None:
            dmg_acc += mean_dmg(self.factory.to_hit, self.factory.dmg_dice, 0, self.targets[1].ac, 1, self.target.is_resistant_to(TwinnedFirebolt.dmg_type))
        return dmg_acc


