from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, mean_dmg, percent_of_curr_hp
from simulator.actoid import Actoid
from itertools import accumulate
import logging

logger = logging.getLogger(__name__)


class Firebolt(Actoid):

    level = 0
    spell_range = SpellStats.Range.FEET_120
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.HARMFUL
    dc = None
    dmg_type = DamageType.Fire

    class Stats:
        def __init__(self, to_hit, combatant_level, eligible_action_types):
            self.to_hit = to_hit
            self.eligible_action_types = eligible_action_types  # FIREBOLT, TWINNED_FIREBOLT, QUICKENED_FIREBOLT
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
            potential_targets = battle_map.get_enemies_within_radius(combatant, super().spell_range.value)
            hp_percentages = [percent_of_curr_hp(pt, mean_dmg(self.to_hit, self.dmg_dice, 0, pt.ac, 1)) for pt in potential_targets]
            potential_targets = list(zip(potential_targets, hp_percentages))
            potential_targets.sort(key=lambda e: e[1], reverse=True)
            return potential_targets[0][0]

    def __init__(self, action_type, targets, stats, **kwargs):
        self.action_type = action_type
        self.targets = targets
        self.stats = stats
        self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True

    @staticmethod
    def calculate_threat_approx(combatant, battle_map, *args, **kwargs):
        potential_targets = battle_map.get_enemies_within_radius(super().spell_range.value)
        dmg_dice = Firebolt.Stats.get_dmg_dice(combatant.level)
        dmg_acc = accumulate(potential_targets, lambda pt: mean_dmg(combatant.spell_to_hit, dmg_dice, 0, pt.ac, 1, pt.is_resistant_to(Firebolt.dmg_type)))
        dmg_acc /= len(potential_targets)
        return dmg_acc

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        acc = 0
        p_acc = 1
        P_SAME = 4 / 43  # 8/86 = 4 / 43
        dmg_dice = "+".join(self.dmg_dice, self.additional_dmg_dice)
        for target in self.target_combatants:
            acc += mean_dmg(self.stats.to_hit, dmg_dice, 0, target.ac) * p_acc
            p_acc *= P_SAME
        return acc

