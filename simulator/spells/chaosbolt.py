from simulator.action_types import BonusActionOrdering
from simulator.spells.spell import SpellStats
from simulator.misc import DamageType
import logging
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from simulator.threat import mean_dmg
from simulator.threat_calculator import DirectThreat, DirectThreatFactory
from simulator.misc import percent_of_curr_hp
from functools import partial
from functools import reduce

from simulator.utils.roll_modifiers import RollModifier, ROLL_MODIFIER, ROLL_MODIFIER_CRIT

logger = logging.getLogger(__name__)

class ChaosboltFactory(DirectThreatFactory):
    def __init__(self, to_hit, action_type, caster):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.bonus_action_ordering = BonusActionOrdering.INDEPENDENT  # In case this became a bonus action
        self.to_hit = to_hit
        self.action_type = action_type  # CHAOSBOLT, QUICKENED_CHAOSBOLT
        self.dmg_dice = "2d8"
        self.additional_dmg_dice = "1d6"
        self.caster = caster

    def __str__(self):
        """
        Important for FSM building
        """
        return "ChaosboltFactory"

    @staticmethod
    def get_sorted_chain(battle_map, potential_targets, threat_calc_func):
        hp_percentages = [percent_of_curr_hp(pt, threat_calc_func(pt.ac)) for pt in potential_targets]
        potential_targets = list(zip(potential_targets, hp_percentages))
        potential_targets.sort(key=lambda e: e[1], reverse=True)
        for i in range(1, len(potential_targets)):
            if battle_map.get_cartesian_distance(potential_targets[i - 1][0], potential_targets[i][0]) > SpellStats.Range.FEET_30:
                break
        return list(zip(*potential_targets[:i]))[0]

    def find_best_args(self, combatant, battle_map):
        potential_targets = battle_map.get_enemies_within_radius(combatant, Chaosbolt.spell_range.value)
        dmg_dice = "+".join([self.dmg_dice, self.additional_dmg_dice])
        mean_dmg_func = partial(mean_dmg, to_hit=self.to_hit, dmg_dice=dmg_dice, dmg_bonus=0, crit_range=1)
        return self.get_sorted_chain(battle_map, potential_targets, mean_dmg_func)

    def create_best(self, combatant, battle_map):
        return Chaosbolt(self.find_best_args(combatant, battle_map), self)

    def create_mock(self):
        return Chaosbolt(None, self)

    def create(self, target_combatant):
        return Chaosbolt([target_combatant], self)

    def calculate_threat_approx_mod(self, battle_map, modified_stats, *args, **kwargs):
        """
        Calculates the threat diff based on provided stat modifications. Relevant bonuses are:
        - to_hit
        """
        # TODO implement once I have spells that do this, e.g. Bless
        try:
            to_hit_bonus = modified_stats['to_hit']
            potential_targets = battle_map.get_enemies_within_radius(self.caster, Chaosbolt.spell_range.value)
            dmg_dice = "+".join([self.dmg_dice, self.additional_dmg_dice])
            mean_dmg_func = partial(mean_dmg, to_hit=self.to_hit, dmg_dice=dmg_dice, dmg_bonus=0, crit_range=1)
            mean_dmg_func_mod = partial(mean_dmg, to_hit=self.to_hit + to_hit_bonus, dmg_dice=dmg_dice, dmg_bonus=0, crit_range=1)
            sorted_targets = ChaosboltFactory.get_sorted_chain(battle_map, potential_targets, mean_dmg_func)
            acc = 0
            p_acc = 1
            P_SAME = 4 / 43  # 8/86 = 4 / 43
            for target in sorted_targets:
                acc += (mean_dmg_func_mod(ac=target.ac) - mean_dmg_func(ac=target.ac)) * p_acc
                p_acc *= P_SAME
            return acc
        except IndexError:
            return 0

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        Calculates threat to a specific target
        """
        if battle_map.get_cartesian_distance(self.caster, target) <= Chaosbolt.spell_range.value:
            dmg_dice = "+".join([self.dmg_dice, self.additional_dmg_dice])
            return mean_dmg(self.to_hit, dmg_dice, 0, target.ac)
        return 0

    def calculate_threat_to_target_mod(self, battle_map, target, modified_stats, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        try:
            to_hit_bonus = modified_stats['to_hit']
        except KeyError:
            to_hit_bonus = 0

        try:
            roll_modifier = modified_stats['roll_modifier']
        except KeyError:
            roll_modifier = RollModifier.STRAIGHT

        if battle_map.get_cartesian_distance(self.caster, target) <= Chaosbolt.spell_range.value:
            to_hit_total = self.to_hit + to_hit_bonus
            to_hit_total += ROLL_MODIFIER[roll_modifier][target.ac - to_hit_total]
            total_crit = ROLL_MODIFIER_CRIT[roll_modifier]

            dmg_dice = "+".join([self.dmg_dice, self.additional_dmg_dice])
            return mean_dmg(to_hit_total, dmg_dice, 0, target.ac, total_crit) - mean_dmg(self.to_hit, dmg_dice, 0, target.ac)
        else:
            return 0


class Chaosbolt(Actoid, DirectThreat):
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


    def __init__(self, targets, factory, **kwargs):
        super().__init__(actoid_type=ActoidFlags.IS_SPELL | ActoidFlags.IS_ATTACK_LIKE | ActoidFlags.IS_DIRECT_THREAT)
        self.targets = targets
        self.factory = factory
        self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.roll_modifier = RollModifier.STRAIGHT

    def __str__(self):
        return f"Chaosbolt on {self.targets[0]}"


    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        acc = 0
        p_acc = 1
        P_SAME = 4 / 43  # 8/86 = 4 / 43
        dmg_dice = "+".join([self.factory.dmg_dice, self.factory.additional_dmg_dice])
        for target in self.targets:
            acc += mean_dmg(self.factory.to_hit, dmg_dice, 0, target.ac) * p_acc
            p_acc *= P_SAME
        return acc

