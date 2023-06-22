from simulator.actions.action_types import BonusAction
from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, RollType, avg_roll
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import cache

from simulator.threat_utils import mean_dmg
from simulator.threat_interfaces import DirectThreat, DirectThreatFactory
import logging

from simulator.utils.roll_types import ROLL_TYPE_CRIT, ROLL_TYPE, ThreatModifierType

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
        self.combatant = caster

    def __str__(self):
        """
        Important for FSM building
        """
        return "FireboltFactory"


    def get_twinned_kwargs(self):
        return {'to_hit': self.to_hit, 'caster': self.combatant}

    def get_quickened_kwargs(self):
        return {'to_hit': self.to_hit, 'caster': self.combatant}

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

    def get_eligible_targets(self, battle_map):
        return battle_map.get_enemies(self.combatant)

    def create_all(self, battle_map):
        targets = self.get_eligible_targets(battle_map)
        return [Firebolt(t, self) for t in targets]

    def create(self, target_combatant):
        return Firebolt(target_combatant, self)


    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        if battle_map.get_cartesian_distance(self.combatant, target) <= FireboltFactory.range:
            return mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(FireboltFactory.dmg_type))
        return 0

    def calculate_threat_to_target_delta(self, battle_map, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications.
        This is useful calculating the potential reduction of threat_in caused by abilities of enemies, e.g. advantage on saving throw
        against fireball or bane on attack rolls etc.
        """
        mod_to_hit_flat = modifiers.get(ThreatModifierType.TO_HIT_FLAT, 0)
        mod_to_hit_die = modifiers.get(ThreatModifierType.TO_HIT_DIE, '0d0')
        roll_type = modifiers.get(ThreatModifierType.ROLL_TYPE, RollType.STRAIGHT)
        target_ac = modifiers.get(ThreatModifierType.TARGET_AC, 0)

        total_target_ac = target_ac + target.ac
        to_hit_total = self.to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
        to_hit_total += ROLL_TYPE[roll_type][max(0, min(total_target_ac - to_hit_total, 20))]
        total_crit = ROLL_TYPE_CRIT[roll_type]

        return mean_dmg(to_hit_total, self.dmg_dice, 0, total_target_ac, total_crit, target.is_resistant_to(FireboltFactory.dmg_type)) - mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(
                    FireboltFactory.dmg_type))

    def calculate_max_threat(self, battle_map):
        targets = self.get_eligible_targets(battle_map)
        return max(targets, key=lambda t: self.calculate_threat_to_target(battle_map, t))


class Firebolt(Actoid, DirectThreat):
    def __init__(self, target, factory, **kwargs):
        super().__init__(actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_ATTACK_LIKE | ActoidFlags.IS_DIRECT_THREAT)
        self.target = target
        self.factory = factory
        self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.roll_type = RollType.STRAIGHT

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FIREBOLT else "") + f"Firebolt on {self.target}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_FIREBOLT else "") + "Firebolt"

    def clear_cache(self):
        self.calculate_threat.cache_clear()


    @cache
    def calculate_threat(self, battle_map, *args, **kwargs):
        roll_type = RollType.STRAIGHT if not battle_map.is_enemy_adjacent(self.factory.combatant) else RollType.DISADVANTAGE
        to_hit_total = self.factory.to_hit + ROLL_TYPE[roll_type][max(0, min(self.target.ac - self.factory.to_hit, 20))]
        return mean_dmg(to_hit_total, self.factory.dmg_dice, 0, self.target.ac, 1, self.target.is_resistant_to(FireboltFactory.dmg_type))

    def calculate_threat_delta(self, battle_map, modifiers, *args, **kwargs):
        return self.factory.calculate_threat_to_target_delta(battle_map, self.target, modifiers, *args, **kwargs)

    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        return battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.target),
                                                             distances,
                                                             inflate_to_size=self.factory.combatant.size,
                                                             rng=FireboltFactory.range, combatant=self.factory.combatant)

    def is_current_coord_eligible(self, battle_map):
        return battle_map.get_cartesian_distance(self.factory.combatant, self.target) <= FireboltFactory.range
