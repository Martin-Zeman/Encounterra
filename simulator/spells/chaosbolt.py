from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, mean_dmg
from itertools import pairwise
import logging
from simulator.actoid import Actoid
from simulator.misc import percent_of_curr_hp
from functools import partial

logger = logging.getLogger(__name__)


class Chaosbolt(Actoid):
    DMG_TYPE = (
        DamageType.Acid, DamageType.Cold, DamageType.Fire, DamageType.Force, DamageType.Lightning, DamageType.Poison, DamageType.Psychic,
        DamageType.Thunder)

    level = 1
    spell_range = SpellStats.Range.FEET_120
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.HARMFUL
    dc = None
    dmg_type = None

    class Stats:
        def __init__(self, to_hit,  eligible_action_types):
            self.to_hit = to_hit
            self.eligible_action_types = eligible_action_types  # CHAOSBOLT, TWINNED_CHAOSBOLT, QUICKENED_CHAOSBOLT
            self.dmg_dice = "2d8"
            self.additional_dmg_dice = "1d6"

        @staticmethod
        def get_sorted_chain( battle_map, potential_targets, threat_calc_func):
            hp_percentages = [percent_of_curr_hp(pt, threat_calc_func(pt.ac)) for pt in potential_targets]
            potential_targets = list(zip(potential_targets, hp_percentages))
            potential_targets.sort(key=lambda e: e[1], reverse=True)
            for i in range(1, len(potential_targets)):
                if battle_map.get_cartesian_distance(potential_targets[i - 1][0], potential_targets[i][0]) > SpellStats.Range.FEET_30:
                    break
            return list(zip(*potential_targets[:i]))[0]

        def find_best_args(self, combatant, battle_map):
            potential_targets = battle_map.get_enemies_within_radius(combatant, super().spell_range.value)
            dmg_dice = "+".join(self.dmg_dice, self.additional_dmg_dice)
            mean_dmg_func = partial(mean_dmg, to_hit=self.to_hit, dmg_dice=dmg_dice, dmg_bonus=0, crit_range=1)
            return self.get_sorted_chain(battle_map, potential_targets, mean_dmg_func)



    def __init__(self, action_type, targets, stats):
        super().__init__(Actoid.Type.IS_SPELL)
        # self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.action_type = action_type
        self.targets = targets
        self.stats = stats


    @staticmethod
    def calculate_threat_approx(combatant, battle_map, *args, **kwargs):
        potential_targets = battle_map.get_enemies_within_radius(super().spell_range.value)
        dmg_dice = "+".join(super().dmg_dice, super().additional_dmg_dice)
        mean_dmg_func = partial(mean_dmg, to_hit=combatant.to_hit, dmg_dice=dmg_dice, dmg_bonus=0, crit_range=1)
        sorted_targets = Chaosbolt.Stats.get_sorted_chain(battle_map, potential_targets, mean_dmg_func)
        acc = 0
        p_acc = 1
        P_SAME = 4 / 43  # 8/86 = 4 / 43
        for target in sorted_targets:
            acc += mean_dmg(combatant.spell_to_hit, dmg_dice, 0, target.ac) * p_acc
            p_acc *= P_SAME
        return acc


    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        acc = 0
        p_acc = 1
        P_SAME = 4 / 43  # 8/86 = 4 / 43
        dmg_dice = "+".join(self.dmg_dice, self.additional_dmg_dice)
        for target in self.target_combatants:
            acc += mean_dmg(self.stats.to_hit, dmg_dice, 0, target.ac) * p_acc
            p_acc *= P_SAME
        return acc
