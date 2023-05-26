from simulator.combatant_coords import CombatantCoords
from simulator.spells.firebolt import FireboltFactory
from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, percent_of_curr_hp, avg_roll
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import reduce, cache

from simulator.threat_utils import mean_dmg
from simulator.threat_interfaces import DirectThreat, DirectThreatFactory
from itertools import combinations_with_replacement
import logging

from simulator.utils.roll_modifiers import RollModifier, ROLL_MODIFIER_CRIT, ROLL_MODIFIER

logger = logging.getLogger("EncounTroll")

class ScorchingRayFactory(DirectThreatFactory):
    level = 2
    range = SpellStats.Range.FEET_120.value
    target = SpellStats.Target.THREE_CREATURES
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.HARMFUL
    dc = None
    dmg_type = DamageType.Fire

    def __init__(self, to_hit, action_type, caster):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.to_hit = to_hit
        self.action_type = action_type  # SCORCHING_RAY, QUICKENED_SCORCHING_RAY
        self.dmg_dice = '2d6'
        self.caster = caster

    def __str__(self):
        """
        Important for FSM building
        """
        return "ScorchingRayFactory"

    def get_quickened_kwargs(self):
        return {'to_hit': self.to_hit, 'caster': self.caster}

    def get_eligible_targets(self, battle_map):
        # Range is so big that it doesn't matter
        return combinations_with_replacement(battle_map.get_enemies(self.caster), 3)

    def create_all(self, battle_map):
        targets = self.get_eligible_targets(battle_map)
        return [ScorchingRay(t, self) for t in targets]

    def create(self, targets):
        return ScorchingRay(targets, self)

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        if battle_map.get_cartesian_distance(self.caster, target) <= ScorchingRayFactory.range:
            # Cannot target the same combatant twice
            return 3 * mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(ScorchingRayFactory.dmg_type))
        else:
            return 0


    def calculate_threat_to_target_delta_single_target(self, target, modified_stats):
        """
        Helper function
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
        to_hit_total += ROLL_MODIFIER[roll_modifier][max(0, min(target.ac - to_hit_total, 20))]
        total_crit = ROLL_MODIFIER_CRIT[roll_modifier]

        # We assume the maximum threat in case where all three rays are aimed at the target
        return 3*(mean_dmg(to_hit_total, self.dmg_dice, 0, target.ac, total_crit, target.is_resistant_to(ScorchingRayFactory.dmg_type)) - \
            mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(ScorchingRayFactory.dmg_type)))

    def calculate_threat_to_target_delta(self, battle_map, target, modified_stats, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications.
        This is useful calculating the potential reduction of threat_in caused by abilities of enemies, e.g. advantage on saving throw
        against fireball or bane on attack rolls etc.
        """
        # We assume the maximum threat in case where all three rays are aimed at the target
        return 3 * self.calculate_threat_to_target_delta_single_target(target, modified_stats)


class ScorchingRay(Actoid, DirectThreat):

    def __init__(self, targets, factory, **kwargs):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_ATTACK_LIKE | ActoidFlags.IS_DIRECT_THREAT)
        self.targets = targets
        self.factory = factory
        self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.roll_modifier = RollModifier.STRAIGHT

    def __str__(self):
        return f"Scorching Ray on {self.targets[0]}, {self.targets[1]} and {self.targets[2]}"

    def clear_cache(self):
        self.calculate_threat.cache_clear()

    @cache
    def calculate_threat(self, combatant, battle_map, combatant_coords: CombatantCoords = None, *args, **kwargs):
        roll_modifier = RollModifier.STRAIGHT if not battle_map.is_enemy_adjacent(self.factory.caster) else RollModifier.DISADVANTAGE
        to_hit_total = self.factory.to_hit + ROLL_MODIFIER[roll_modifier][max(0, min(self.targets[0].ac - self.factory.to_hit, 20))]
        dmg_acc = mean_dmg(to_hit_total, self.factory.dmg_dice, 0, self.targets[0].ac, 1, self.targets[0].is_resistant_to(ScorchingRayFactory.dmg_type))
        to_hit_total = self.factory.to_hit + ROLL_MODIFIER[roll_modifier][max(0, min(self.targets[1].ac - self.factory.to_hit, 20))]
        dmg_acc += mean_dmg(to_hit_total, self.factory.dmg_dice, 0, self.targets[1].ac, 1, self.targets[1].is_resistant_to(ScorchingRayFactory.dmg_type))
        to_hit_total = self.factory.to_hit + ROLL_MODIFIER[roll_modifier][max(0, min(self.targets[2].ac - self.factory.to_hit, 20))]
        dmg_acc += mean_dmg(to_hit_total, self.factory.dmg_dice, 0, self.targets[2].ac, 1, self.targets[2].is_resistant_to(ScorchingRayFactory.dmg_type))
        return dmg_acc

    def calculate_threat_delta(self, battle_map, modified_stats, *args, **kwargs):
        ret = self.factory.calculate_threat_to_target_delta_single_target(self.targets[0], modified_stats)
        ret += self.factory.calculate_threat_to_target_delta_single_target(self.targets[1], modified_stats)
        ret += self.factory.calculate_threat_to_target_delta_single_target(self.targets[2], modified_stats)
        return ret

    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        coords_for_first = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[0]),
                                                                        distances,
                                                                        inflate_to_size=self.factory.caster.size,
                                                                        rng=ScorchingRayFactory.range,
                                                                        combatant=self.factory.caster)
        coords_for_second = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[1]),
                                                                          distances,
                                                                          inflate_to_size=self.factory.caster.size,
                                                                          rng=ScorchingRayFactory.range,
                                                                          combatant=self.factory.caster)
        coords_for_third = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[2]),
                                                                          distances,
                                                                          inflate_to_size=self.factory.caster.size,
                                                                          rng=ScorchingRayFactory.range,
                                                                          combatant=self.factory.caster)
        return coords_for_third.intersection(coords_for_first.intersection(coords_for_second))

    def is_current_coord_eligible(self, battle_map):
        return battle_map.get_cartesian_distance(self.factory.caster, self.targets[0]) <= ScorchingRayFactory.range \
            and battle_map.get_cartesian_distance(self.factory.caster, self.targets[1]) <= ScorchingRayFactory.range \
            and battle_map.get_cartesian_distance(self.factory.caster, self.targets[2]) <= ScorchingRayFactory.range