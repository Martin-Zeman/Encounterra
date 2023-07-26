from simulator.actions.action_types import BonusAction
from simulator.battle_map import Map, map_position_toggled_cache
from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, avg_roll, Conditions, Visibility
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import cache
from simulator.threat_utils import mean_dmg
from simulator.threat_interfaces import DirectThreat, DirectThreatFactory
from itertools import combinations_with_replacement
import logging
from simulator.utils.roll_types import RollType, ROLL_TYPE_DELTA, ROLL_TYPE_CRIT_DELTA, ThreatModifierType

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
        self.combatant = caster

    def __str__(self):
        """
        Important for FSM building
        """
        return "ScorchingRayFactory"

    def get_quickened_kwargs(self):
        return {'to_hit': self.to_hit, 'caster': self.combatant}

    def get_eligible_targets(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            return [swallower, swallower, swallower]
        # Range is so big that it doesn't matter
        return combinations_with_replacement([e for e in Map.get().get_enemies(self.combatant) if not e.is_affected_by(Conditions.SWALLOWED)], 3)

    def create_all(self):
        targets = self.get_eligible_targets()
        return [ScorchingRay(t, self) for t in targets]

    def create(self, targets):
        return ScorchingRay(targets, self)

    def calculate_threat_to_target(self, target, **kwargs):
        battle_map = Map.get()
        if battle_map.get_cartesian_distance(self.combatant, target) <= ScorchingRayFactory.range:
            roll_type = RollType.STRAIGHT if not battle_map.is_enemy_adjacent(self.combatant) else RollType.DISADVANTAGE
            to_hit_total = self.to_hit + ROLL_TYPE_DELTA[roll_type][max(0, min(target.ac - self.to_hit, 20))]
            return 3 * mean_dmg(to_hit_total, self.dmg_dice, 0, target.ac, ROLL_TYPE_CRIT_DELTA[roll_type], target.is_resistant_to(ScorchingRayFactory.dmg_type))
        else:
            return 0

    def calculate_threat_to_target_delta_single_target(self, target, modifiers):
        """
        Helper function
        """
        mod_to_hit_flat = modifiers.get(ThreatModifierType.TO_HIT_FLAT, 0)
        mod_to_hit_die = modifiers.get(ThreatModifierType.TO_HIT_DIE, '0d0')
        roll_type = modifiers.get(ThreatModifierType.ROLL_TYPE, RollType.STRAIGHT)

        to_hit_total = self.to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
        to_hit_total += ROLL_TYPE_DELTA[roll_type][max(0, min(target.ac - to_hit_total, 20))]
        total_crit = ROLL_TYPE_CRIT_DELTA[roll_type]

        # We assume the maximum threat in case where all three rays are aimed at the target
        return 3*(mean_dmg(to_hit_total, self.dmg_dice, 0, target.ac, total_crit, target.is_resistant_to(ScorchingRayFactory.dmg_type)) - \
            mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(ScorchingRayFactory.dmg_type)))

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications.
        This is useful calculating the potential reduction of threat_in caused by abilities of enemies, e.g. advantage on saving throw
        against fireball or bane on attack rolls etc.
        """
        # We assume the maximum threat in case where all three rays are aimed at the target
        return 3 * self.calculate_threat_to_target_delta_single_target(target, modifiers)

    def calculate_max_threat(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            targets = [swallower]
        else:
            targets = [e for e in Map.get().get_enemies(self.combatant) if not e.is_affected_by(Conditions.SWALLOWED)]
        return max([self.calculate_threat_to_target(t) for t in targets])


class ScorchingRay(Actoid, DirectThreat):

    def __init__(self, targets, factory, **kwargs):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_ATTACK_LIKE | ActoidFlags.IS_DIRECT_THREAT)
        self.targets = targets
        self.factory = factory
        self.empowered = kwargs.get("empowered", False)
        self.roll_type = RollType.STRAIGHT

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_SCORCHING_RAY else "") + f"Scorching Ray on {self.targets[0]}, {self.targets[1]} and {self.targets[2]}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_SCORCHING_RAY else "") + "Scorching Ray"

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        battle_map = Map.get()
        roll_type = RollType.STRAIGHT if not battle_map.is_enemy_adjacent(self.factory.combatant) else RollType.DISADVANTAGE
        crit_multiplier = ROLL_TYPE_CRIT_DELTA[roll_type]
        to_hit_total = self.factory.to_hit + ROLL_TYPE_DELTA[roll_type][max(0, min(self.targets[0].ac - self.factory.to_hit, 20))]
        dmg_acc = mean_dmg(to_hit_total, self.factory.dmg_dice, 0, self.targets[0].ac, crit_multiplier, self.targets[0].is_resistant_to(ScorchingRayFactory.dmg_type))
        to_hit_total = self.factory.to_hit + ROLL_TYPE_DELTA[roll_type][max(0, min(self.targets[1].ac - self.factory.to_hit, 20))]
        dmg_acc += mean_dmg(to_hit_total, self.factory.dmg_dice, 0, self.targets[1].ac, crit_multiplier, self.targets[1].is_resistant_to(ScorchingRayFactory.dmg_type))
        to_hit_total = self.factory.to_hit + ROLL_TYPE_DELTA[roll_type][max(0, min(self.targets[2].ac - self.factory.to_hit, 20))]
        dmg_acc += mean_dmg(to_hit_total, self.factory.dmg_dice, 0, self.targets[2].ac, crit_multiplier, self.targets[2].is_resistant_to(ScorchingRayFactory.dmg_type))
        return dmg_acc

    def clear_cache(self):
        self.calculate_threat.cache_clear()

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        ret = self.factory.calculate_threat_to_target_delta_single_target(self.targets[0], modifiers)
        ret += self.factory.calculate_threat_to_target_delta_single_target(self.targets[1], modifiers)
        ret += self.factory.calculate_threat_to_target_delta_single_target(self.targets[2], modifiers)
        return ret

    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        coords_for_first = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[0]),
                                                                        distances,
                                                                        inflate_to_size=self.factory.combatant.size,
                                                                        rng=ScorchingRayFactory.range,
                                                                        combatant=self.factory.combatant)
        coords_for_second = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[1]),
                                                                          distances,
                                                                          inflate_to_size=self.factory.combatant.size,
                                                                          rng=ScorchingRayFactory.range,
                                                                          combatant=self.factory.combatant)
        coords_for_third = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[2]),
                                                                          distances,
                                                                          inflate_to_size=self.factory.combatant.size,
                                                                          rng=ScorchingRayFactory.range,
                                                                          combatant=self.factory.combatant)
        free_coords_in_range = coords_for_third.intersection(coords_for_first.intersection(coords_for_second))

        return {coord for coord in free_coords_in_range if
                battle_map.visibility_dict_for_all_coords[coord][self.targets[0]] is not Visibility.NONE
                and battle_map.visibility_dict_for_all_coords[coord][self.targets[1]] is not Visibility.NONE
                and battle_map.visibility_dict_for_all_coords[coord][self.targets[2]] is not Visibility.NONE}

    def is_current_coord_eligible(self):
        if all([t is self.factory.combatant.get_swallower() for t in self.targets]):
            return True
        battle_map = Map.get()
        return battle_map.get_cartesian_distance(self.factory.combatant, self.targets[0]) <= ScorchingRayFactory.range \
            and battle_map.get_cartesian_distance(self.factory.combatant, self.targets[1]) <= ScorchingRayFactory.range \
            and battle_map.get_cartesian_distance(self.factory.combatant, self.targets[2]) <= ScorchingRayFactory.range
