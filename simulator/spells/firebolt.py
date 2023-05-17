from simulator.action_types import BonusAction
from simulator.combatant_coords import CombatantCoords
from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, percent_of_curr_hp, RollModifier, avg_roll
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import reduce, cache

from simulator.threat import mean_dmg
from simulator.threat_calculator import DirectThreat, DirectThreatFactory
import logging

from simulator.utils.roll_modifiers import ROLL_MODIFIER_CRIT, ROLL_MODIFIER

logger = logging.getLogger("EncounTroll")

class FireboltFactory(DirectThreatFactory):
    level = 0
    range = SpellStats.Range.FEET_120.value
    target = SpellStats.Target.ONE_CREATURE
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
        self.dmg_dice = self.get_dmg_dice(caster.level)
        self.caster = caster

    def __str__(self):
        """
        Important for FSM building
        """
        return "FireboltFactory"


    def get_twinned_kwargs(self):
        return {'to_hit': self.to_hit, 'caster': self.caster}

    def get_quickened_kwargs(self):
        return {'to_hit': self.to_hit, 'caster': self.caster}

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
        # TODO Deprecated
        # TODO Should this include action type? Cause for a twinned version you would need multiple targets
        potential_targets = battle_map.get_enemies_within_radius(combatant, FireboltFactory.range)
        hp_percentages = [percent_of_curr_hp(pt, mean_dmg(self.to_hit, self.dmg_dice, 0, pt.ac, 1)) for pt in potential_targets]
        potential_targets = list(zip(potential_targets, hp_percentages))
        potential_targets.sort(key=lambda e: e[1], reverse=True)
        try:
            return potential_targets[0][0]
        except IndexError:
            return None

    def create_best(self, combatant, battle_map):
        best = self.find_best_args(combatant, battle_map)
        if best is None:
            return None
        return Firebolt(best, self)

    def get_eligible_targets(self, battle_map):
        return battle_map.get_enemies(self.caster)

    def create_all(self, battle_map):
        targets = self.get_eligible_targets(battle_map)
        return [Firebolt(t, self) for t in targets]

    def create(self, target_combatant):
        return Firebolt(target_combatant, self)


    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        if battle_map.get_cartesian_distance(self.caster, target) <= FireboltFactory.range:
            return mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(FireboltFactory.dmg_type))
        return 0

    def calculate_threat_to_target_mod(self, battle_map, target, modified_stats, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications.
        This is useful calculating the potential reduction of threat_in caused by abilities of enemies, e.g. advantage on saving throw
        against fireball or bane on attack rolls etc.
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
        try:
            target_ac = modified_stats['target_ac']
        except KeyError:
            target_ac = 0

        total_target_ac = target_ac + target.ac
        to_hit_total = self.to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
        to_hit_total += ROLL_MODIFIER[roll_modifier][max(0, min(total_target_ac - to_hit_total, 20))]
        total_crit = ROLL_MODIFIER_CRIT[roll_modifier]

        return mean_dmg(to_hit_total, self.dmg_dice, 0, total_target_ac, total_crit, target.is_resistant_to(FireboltFactory.dmg_type)) - mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(
                    FireboltFactory.dmg_type))


class Firebolt(Actoid, DirectThreat):
    def __init__(self, target, factory, **kwargs):
        super().__init__(actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_ATTACK_LIKE | ActoidFlags.IS_DIRECT_THREAT)
        self.target = target
        self.factory = factory
        self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.roll_modifier = RollModifier.STRAIGHT

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FIREBOLT else "") + f"Firebolt on {self.target}"

    def clear_cache(self):
        self.calculate_threat.cache_clear()


    @cache
    def calculate_threat(self, combatant, battle_map, combatant_coords: CombatantCoords = None, *args, **kwargs):
        roll_modifier = RollModifier.STRAIGHT if not battle_map.is_enemy_adjacent(self.factory.caster) else RollModifier.DISADVANTAGE
        to_hit_total = self.factory.to_hit + ROLL_MODIFIER[roll_modifier][max(0, min(self.target.ac - self.factory.to_hit, 20))]
        return mean_dmg(to_hit_total, self.factory.dmg_dice, 0, self.target.ac, 1, self.target.is_resistant_to(FireboltFactory.dmg_type))

    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        return battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.target),
                                                             distances,
                                                             inflate_to_size=self.factory.caster.size,
                                                             rng=FireboltFactory.range, combatant=self.factory.caster)

    def is_current_coord_eligible(self, battle_map):
        return battle_map.get_cartesian_distance(self.factory.caster, self.target) <= FireboltFactory.range