from simulator.battle_map import Map
from simulator.combatant_coords import CombatantCoords
from simulator.spells.firebolt import FireboltFactory
from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, avg_roll, Conditions
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import  cache

from simulator.threat_utils import mean_dmg
from simulator.threat_interfaces import DirectThreat, DirectThreatFactory
from itertools import combinations
import logging

from simulator.utils.roll_types import RollType, ROLL_TYPE_CRIT, ROLL_TYPE, ThreatModifierType

logger = logging.getLogger("EncounTroll")

class TwinnedFireboltFactory(DirectThreatFactory):
    level = 0
    range = SpellStats.Range.FEET_120.value
    target = SpellStats.Target.TWO_CREATURES
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.HARMFUL
    dc = None
    dmg_type = DamageType.Fire

    def __init__(self, to_hit, action_type, caster):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.to_hit = to_hit
        self.action_type = action_type  # FIREBOLT, TWINNED_FIREBOLT, QUICKENED_FIREBOLT TODO
        self.dmg_dice = FireboltFactory.get_dmg_dice(caster.level)
        self.combatant = caster

    def __str__(self):
        """
        Important for FSM building
        """
        return "TwinnedFireboltFactory"

    def get_eligible_targets(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            return [swallower, None]
        battle_map = Map.get()
        return combinations([e for e in battle_map.get_enemies(self.combatant) if not e.is_affected_by(Conditions.SWALLOWED)], 2)

    def create_all(self):
        targets = self.get_eligible_targets()
        return [TwinnedFirebolt(t, self) for t in targets]

    def create(self, targets):
        return TwinnedFirebolt(targets, self)

    def calculate_threat_to_target(self, target, *args, **kwargs):
        battle_map = Map.get()
        if battle_map.get_cartesian_distance(self.combatant, target) <= TwinnedFireboltFactory.range:
            roll_type = RollType.STRAIGHT if not battle_map.is_enemy_adjacent(self.combatant) else RollType.DISADVANTAGE
            to_hit_total = self.to_hit + ROLL_TYPE[roll_type][max(0, min(target.ac - self.to_hit, 20))]
            # Cannot target the same combatant twice
            return mean_dmg(to_hit_total, self.dmg_dice, 0, target.ac, ROLL_TYPE_CRIT[roll_type], target.is_resistant_to(TwinnedFireboltFactory.dmg_type))
        else:
            return 0

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications.
        This is useful calculating the potential reduction of threat_in caused by abilities of enemies, e.g. advantage on saving throw
        against fireball or bane on attack rolls etc.
        """
        mod_to_hit_flat = modifiers.get(ThreatModifierType.TO_HIT_FLAT, 0)
        mod_to_hit_die = modifiers.get(ThreatModifierType.TO_HIT_DIE, '0d0')
        roll_type = modifiers.get(ThreatModifierType.ROLL_TYPE, RollType.STRAIGHT)

        to_hit_total = self.to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
        to_hit_total += ROLL_TYPE[roll_type][max(0, min(target.ac - to_hit_total, 20))]
        total_crit = ROLL_TYPE_CRIT[roll_type]

        return mean_dmg(to_hit_total, self.dmg_dice, 0, target.ac, total_crit, target.is_resistant_to(TwinnedFireboltFactory.dmg_type)) - mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(
                    TwinnedFireboltFactory.dmg_type))

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        return max(targets, key=lambda t: self.calculate_threat_to_target(t[0]) + self.calculate_threat_to_target(t[1]))

class TwinnedFirebolt(Actoid, DirectThreat):

    def __init__(self, targets, factory, **kwargs):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_ATTACK_LIKE | ActoidFlags.IS_DIRECT_THREAT)
        self.targets = targets
        self.factory = factory
        self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.roll_type = RollType.STRAIGHT

    def __str__(self):
        return f"Twinned Firebolt on {self.targets[0]} and {self.targets[1]}"

    def shorthand_str(self):
        return "Twinned Firebolt"

    def calculate_threat(self, *args, **kwargs):
        battle_map = Map.get()
        roll_type = RollType.STRAIGHT if not battle_map.is_enemy_adjacent(self.factory.combatant) else RollType.DISADVANTAGE
        to_hit_total = self.factory.to_hit + ROLL_TYPE[roll_type][max(0, min(self.targets[0].ac - self.factory.to_hit, 20))]
        dmg_acc = mean_dmg(to_hit_total, self.factory.dmg_dice, 0, self.targets[0].ac, ROLL_TYPE_CRIT[roll_type], self.targets[0].is_resistant_to(TwinnedFireboltFactory.dmg_type))
        if self.targets[1] is not None:
            to_hit_total = self.factory.to_hit + ROLL_TYPE[roll_type][max(0, min(self.targets[1].ac - self.factory.to_hit, 20))]
            dmg_acc += mean_dmg(to_hit_total, self.factory.dmg_dice, 0, self.targets[1].ac, ROLL_TYPE_CRIT[roll_type], self.targets[1].is_resistant_to(TwinnedFireboltFactory.dmg_type))
        return dmg_acc

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        ret = self.factory.calculate_threat_to_target_delta(self.targets[0], modifiers)
        ret += self.factory.calculate_threat_to_target_delta(self.targets[1], modifiers)
        return ret

    def get_eligible_coords(self, distances, shortest_paths):
        if self.factory.combatant.get_swallower():
            return False
        battle_map = Map.get()
        coords_for_fist = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[0]),
                                                                        distances,
                                                                        inflate_to_size=self.factory.combatant.size,
                                                                        rng=TwinnedFireboltFactory.range,
                                                                        combatant=self.factory.combatant)
        coords_for_second = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[1]),
                                                                          distances,
                                                                          inflate_to_size=self.factory.combatant.size,
                                                                          rng=TwinnedFireboltFactory.range,
                                                                          combatant=self.factory.combatant)
        return coords_for_fist.intersection(coords_for_second)

    def is_current_coord_eligible(self):
        if self.factory.combatant.get_swallower():
            return False  # Technically possible but doesn't make sense to waste the sorcery points
        battle_map = Map.get()
        return battle_map.get_cartesian_distance(self.factory.combatant, self.targets[0]) <= TwinnedFireboltFactory.range \
            and battle_map.get_cartesian_distance(self.factory.combatant, self.targets[1]) <= TwinnedFireboltFactory.range
