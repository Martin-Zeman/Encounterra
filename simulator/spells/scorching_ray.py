from simulator.combatant_coords import CombatantCoords
from simulator.spells.firebolt import FireboltFactory
from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, percent_of_curr_hp, avg_roll
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import reduce, cache

from simulator.threat import mean_dmg
from simulator.threat_calculator import DirectThreat, DirectThreatFactory
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
            return mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(ScorchingRayFactory.dmg_type))
        else:
            return 0


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