from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, mean_dmg
from itertools import pairwise
import logging

logger = logging.getLogger(__name__)


class Chaosbolt:
    DMG_TYPE = (
        DamageType.Acid, DamageType.Cold, DamageType.Fire, DamageType.Force, DamageType.Lightning, DamageType.Poison, DamageType.Psychic,
        DamageType.Thunder)

    class Stats(SpellStats):
        def __init__(self, to_hit,  eligible_action_types):
            super().__init__(level=1,
                             spell_range=SpellStats.Range.FEET_120,
                             target=SpellStats.Target.ONE_CREATURE,
                             duration=SpellStats.Duration.INSTANTANEOUS,
                             concentration=False,
                             type=SpellStats.Type.HARMFUL,
                             dc=None,
                             dmg_type=None)
            self.to_hit = to_hit
            self.eligible_action_types = eligible_action_types  # CHAOSBOLT, TWINNED_CHAOSBOLT, QUICKENED_CHAOSBOLT
            self.dmg_dice = "2d8"
            self.additional_dmg_dice = "1d6"

        def find_best_args(self, combatant, battle_map):
            # TODO consider prioritizing the ones you have a change to finish off
            potential_targets = battle_map.get_enemies_within_radius(combatant.movement + self.range - 1)
            potential_targets.sort(key=lambda e: e.curr_hp / e.max_hp)
            for i in range(0, len(potential_targets)):
                if battle_map.get_cartesian_distance(potential_targets[i], potential_targets[i + 1]) > SpellStats.Range.FEET_30:
                    break
            return potential_targets[:i]

    def __init__(self, targets, stats):
        # self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.targets = targets
        self.stats = stats


    @staticmethod
    def calculate_threat_approx(combatant, battle_map, *args, **kwargs):
        return 0 # TODO


    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        acc = 0
        p_acc = 1
        P_SAME = 4 / 43  # 8/86 = 4 / 43
        for target in self.target_combatants:
            acc += mean_dmg(self.stats.to_hit, self.stats.dmg_dice, 0, target.ac) * p_acc
            acc += mean_dmg(self.stats.to_hit, self.stats.additional_dmg_dice, 0, target.ac) * p_acc
            p_acc += P_SAME
        return acc
