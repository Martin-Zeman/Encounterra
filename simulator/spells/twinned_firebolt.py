from cachetools import cached
from cachetools.keys import hashkey

from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key
from ..spells.firebolt import FireboltFactory
from ..spells.spell import SpellStats
from ..misc import DamageType, avg_roll, Conditions, Visibility
from ..actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import cache
from ..threat_utils import mean_dmg
from ..threat_interfaces import DirectThreat, DirectThreatFactory
from itertools import combinations
import logging
from ..utils.roll_types import RollType, ROLL_TYPE_CRIT_DELTA, ROLL_TYPE_DELTA, ThreatModifierType

logger = logging.getLogger("Encounterra")

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
            return []  # Let's not waste a twinned version on this
        enemies = Map.get().get_enemies(self.combatant)
        if len(enemies) < 2:
            return []  # Let's not waste a twinned version on this
        return combinations([e for e in enemies if not e.is_affected_by(Conditions.SWALLOWED)], 2)

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [TwinnedFirebolt(t, self) for t in targets]

    def create(self, targets):
        return TwinnedFirebolt(targets, self)

    def calculate_threat_to_target(self, target, **kwargs):
        battle_map = Map.get()
        if battle_map.get_cartesian_distance_combatants(self.combatant, target) <= TwinnedFireboltFactory.range:
            roll_type = RollType.STRAIGHT if not battle_map.is_enemy_adjacent(self.combatant) else RollType.DISADVANTAGE
            to_hit_total = self.to_hit + ROLL_TYPE_DELTA[roll_type][max(0, min(target.ac - self.to_hit, 20))]
            # Cannot target the same combatant twice
            return mean_dmg(to_hit_total, self.dmg_dice, 0, target.ac, ROLL_TYPE_CRIT_DELTA[roll_type], target.is_resistant_to(TwinnedFireboltFactory.dmg_type))
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
        to_hit_total += ROLL_TYPE_DELTA[roll_type][max(0, min(target.ac - to_hit_total, 20))]
        total_crit = ROLL_TYPE_CRIT_DELTA[roll_type]

        return mean_dmg(to_hit_total, self.dmg_dice, 0, target.ac, total_crit, target.is_resistant_to(TwinnedFireboltFactory.dmg_type)) - mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(
                    TwinnedFireboltFactory.dmg_type))

    def calculate_max_threat(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            return self.calculate_threat_to_target(swallower)
        targets = [e for e in Map.get().get_enemies(self.combatant) if not e.is_affected_by(Conditions.SWALLOWED)]
        threats = sorted([self.calculate_threat_to_target(t) for t in targets], reverse=True)
        return (threats[0] if threats else 0) + (threats[1] if len(threats) > 1 else 0)

class TwinnedFirebolt(Actoid, DirectThreat):

    def __init__(self, targets, factory, **kwargs):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_ATTACK_LIKE)
        self.targets = targets
        self.factory = factory
        self.empowered = kwargs.get("empowered", False)
        self.roll_type = RollType.STRAIGHT

    def __str__(self):
        return f"Twinned Firebolt on {self.targets[0]} and {self.targets[1]}"

    def shorthand_str(self):
        return "Twinned Firebolt"

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        roll_type = RollType.STRAIGHT if not Map.get().is_enemy_adjacent(self.factory.combatant) else RollType.DISADVANTAGE
        to_hit_total = self.factory.to_hit + ROLL_TYPE_DELTA[roll_type][max(0, min(self.targets[0].ac - self.factory.to_hit, 20))]
        dmg_acc = mean_dmg(to_hit_total, self.factory.dmg_dice, 0, self.targets[0].ac, ROLL_TYPE_CRIT_DELTA[roll_type], self.targets[0].is_resistant_to(TwinnedFireboltFactory.dmg_type))
        if self.targets[1] is not None:
            to_hit_total = self.factory.to_hit + ROLL_TYPE_DELTA[roll_type][max(0, min(self.targets[1].ac - self.factory.to_hit, 20))]
            dmg_acc += mean_dmg(to_hit_total, self.factory.dmg_dice, 0, self.targets[1].ac, ROLL_TYPE_CRIT_DELTA[roll_type], self.targets[1].is_resistant_to(TwinnedFireboltFactory.dmg_type))
        return dmg_acc

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        self.calculate_threat_delta.cache_clear()
        #self.get_eligible_coords.cache_clear()

    @map_toggled_cache_with_key(key=lambda self, modifiers, *args, **kwargs: hashkey(tuple(modifiers.items()), tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        ret = self.factory.calculate_threat_to_target_delta(self.targets[0], modifiers)
        ret += self.factory.calculate_threat_to_target_delta(self.targets[1], modifiers)
        return ret

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        if self.factory.combatant.get_swallower():
            return None
        battle_map = Map.get()
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        if not self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            coords_for_fist = set(battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[0]),
                                                                            distances,
                                                                            inflate_to_size=self.factory.combatant.size,
                                                                            rng=TwinnedFireboltFactory.range,
                                                                            combatant=self.factory.combatant))
            coords_for_second = set(battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[1]),
                                                                              distances,
                                                                              inflate_to_size=self.factory.combatant.size,
                                                                              rng=TwinnedFireboltFactory.range,
                                                                              combatant=self.factory.combatant))
            free_coords_in_range = coords_for_fist.intersection(coords_for_second)

            return [coord for coord in free_coords_in_range if battle_map.visibility_dict_for_all_coords[coord][self.targets[0]] is not Visibility.NONE
                    and battle_map.visibility_dict_for_all_coords[coord][self.targets[1]] is not Visibility.NONE]
        elif battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.targets[0]) <= TwinnedFireboltFactory.range \
            and battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.targets[1]) <= TwinnedFireboltFactory.range \
                and battle_map.visibility_dict_for_all_coords[curr_coord][self.targets[0]] is not Visibility.NONE \
                and battle_map.visibility_dict_for_all_coords[curr_coord][self.targets[1]] is not Visibility.NONE:
            return [curr_coord]
        return None
