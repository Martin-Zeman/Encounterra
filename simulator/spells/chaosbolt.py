from simulator.actions.action_types import BonusAction
from simulator.battle_map import Map, map_position_toggled_cache
from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, Conditions, Visibility
import logging
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from simulator.threat_utils import mean_dmg
from simulator.threat_interfaces import DirectThreat, DirectThreatFactory
from simulator.misc import percent_of_curr_hp
from functools import cache
from simulator.utils.roll_types import RollType, ROLL_TYPE_DELTA, ROLL_TYPE_CRIT_DELTA, ThreatModifierType

logger = logging.getLogger("EncounTroll")

class ChaosboltFactory(DirectThreatFactory):
    DMG_TYPE = (
        DamageType.Acid, DamageType.Cold, DamageType.Fire, DamageType.Force, DamageType.Lightning, DamageType.Poison, DamageType.Psychic,
        DamageType.Thunder)

    level = 1
    range = SpellStats.Range.FEET_120.value
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.HARMFUL
    dc = None
    dmg_type = None
    def __init__(self, to_hit, action_type, caster):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.to_hit = to_hit
        self.action_type = action_type  # CHAOSBOLT, QUICKENED_CHAOSBOLT
        self.dmg_dice = "2d8"
        self.additional_dmg_dice = "1d6"
        self.combatant = caster

    def __str__(self):
        """
        Important for FSM building
        """
        return "ChaosboltFactory"

    @staticmethod
    def get_sorted_chain(potential_targets, threat_calc_func):
        hp_percentages = [percent_of_curr_hp(pt, threat_calc_func(pt.ac)) for pt in potential_targets]
        potential_targets = list(zip(potential_targets, hp_percentages))
        potential_targets.sort(key=lambda e: e[1], reverse=True)
        for i in range(1, len(potential_targets)):
            if Map.get().get_cartesian_distance(potential_targets[i - 1][0], potential_targets[i][0]) > SpellStats.Range.FEET_30:
                break
        return list(zip(*potential_targets[:i]))[0]

    def create(self, target):
        return Chaosbolt([target], self)

    def get_eligible_targets(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            return [swallower]
        return [e for e in Map.get().get_enemies(self.combatant) if not e.is_affected_by(Conditions.SWALLOWED)]

    def create_all(self):
        targets = self.get_eligible_targets()
        return [Chaosbolt(t, self) for t in targets]


    def calculate_threat_to_target(self, target, **kwargs):
        """
        Calculates threat to a specific target
        """
        # TODO Consider including the potential of hitting others
        acc = 0
        battle_map = Map.get()
        if battle_map.get_cartesian_distance(self.combatant, target) <= ChaosboltFactory.range:
            roll_type = RollType.STRAIGHT if not battle_map.is_enemy_adjacent(self.combatant) else RollType.DISADVANTAGE
            to_hit_total = self.to_hit + ROLL_TYPE_DELTA[roll_type][max(0, min(target.ac - self.to_hit, 20))]
            other_potential_targets = battle_map.get_enemies_within_radius(self.combatant, ChaosboltFactory.range)   # Relaxes the 30ft distance condition
            other_potential_targets.remove(self.target)
            P_SAME = 4 / 43  # 8/86 = 4 / 43
            p_acc = P_SAME
            dmg_dice = "+".join([self.dmg_dice, self.additional_dmg_dice])
            acc = mean_dmg(to_hit_total, dmg_dice, 0, target.ac)
            for pt in other_potential_targets:
                acc += mean_dmg(self.to_hit, dmg_dice, 0, pt.ac, ROLL_TYPE_CRIT_DELTA[roll_type]) * p_acc
                p_acc *= P_SAME
        return acc

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        to_hit_bonus = modifiers.get(ThreatModifierType.TO_HIT_FLAT, 0)
        roll_type = modifiers.get(ThreatModifierType.ROLL_TYPE, RollType.STRAIGHT)

        if Map.get().get_cartesian_distance(self.combatant, target) <= ChaosboltFactory.range:
            to_hit_total = self.to_hit + to_hit_bonus
            to_hit_total += ROLL_TYPE_DELTA[roll_type][max(0, min(target.ac - to_hit_total, 20))]
            total_crit = ROLL_TYPE_CRIT_DELTA[roll_type]

            dmg_dice = "+".join([self.dmg_dice, self.additional_dmg_dice])
            return mean_dmg(to_hit_total, dmg_dice, 0, target.ac, total_crit) - mean_dmg(self.to_hit, dmg_dice, 0, target.ac)
        else:
            return 0

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        return max([self.calculate_threat_to_target(t) for t in targets])


class Chaosbolt(Actoid, DirectThreat):

    def __init__(self, target, factory, **kwargs):
        super().__init__(actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_ATTACK_LIKE | ActoidFlags.IS_DIRECT_THREAT)
        self.target = target
        self.factory = factory
        self.empowered = kwargs.get("empowered", False)
        self.roll_type = RollType.STRAIGHT

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_CHAOSBOLT else "") + f"Chaosbolt on {self.target[0]}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_CHAOSBOLT else "") + f"Chaosbolt"

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        battle_map = Map.get()
        roll_type = RollType.STRAIGHT if not battle_map.is_enemy_adjacent(self.factory.combatant) else RollType.DISADVANTAGE
        to_hit_total = self.factory.to_hit + ROLL_TYPE_DELTA[roll_type][max(0, min(self.target.ac - self.factory.to_hit, 20))]
        potential_targets = battle_map.get_enemies_within_radius(self.factory.combatant, ChaosboltFactory.range)   # Relaxes the 30ft distance condition
        potential_targets.remove(self.target)
        P_SAME = 4 / 43  # 8/86 = 4 / 43
        p_acc = P_SAME
        dmg_dice = "+".join([self.factory.dmg_dice, self.factory.additional_dmg_dice])
        acc = mean_dmg(to_hit_total, dmg_dice, 0, self.target.ac)
        for pt in potential_targets:
            to_hit_total = self.factory.to_hit + ROLL_TYPE_DELTA[roll_type][max(0, min(pt.ac - self.factory.to_hit, 20))]
            acc += mean_dmg(to_hit_total, dmg_dice, 0, pt.ac, ROLL_TYPE_CRIT_DELTA[roll_type]) * p_acc
            p_acc *= P_SAME
        return acc

    def clear_cache(self):
        self.calculate_threat.cache_clear()

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        """
        The delta in threat when modifiers are applied on this ability.
        """
        return self.factory.calculate_threat_to_target_delta(self.target, modifiers, *args, **kwargs)

    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        free_coords_in_range = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.target),
                                                             distances,
                                                             inflate_to_size=self.factory.combatant.size,
                                                             rng=ChaosboltFactory.range,
                                                             combatant=self.factory.combatant)
        return {coord for coord in free_coords_in_range if battle_map.visibility_dict_for_all_coords[coord][self.target] is not Visibility.NONE}


    def is_current_coord_eligible(self):
        if self.factory.combatant.get_swallower() is self.target:
            return True
        return Map.get().get_cartesian_distance(self.factory.combatant, self.target) <= ChaosboltFactory.range
