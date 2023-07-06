from simulator.actions.action_types import BonusAction
from simulator.battle_map import Map
from simulator.spells.spell import SpellStats
from simulator.misc import DamageType,  avg_roll, Conditions
from simulator.actions.actoid import Actoid, ActoidFlags

from simulator.threat_utils import mean_dmg, mean_dmg_auto_hit
from simulator.threat_interfaces import DirectThreat, DirectThreatFactory
from itertools import combinations_with_replacement
import logging

from simulator.utils.roll_types import RollType, ROLL_TYPE, ROLL_TYPE_CRIT, ThreatModifierType

logger = logging.getLogger("EncounTroll")

class MagicMissileFactory(DirectThreatFactory):
    level = 1
    range = SpellStats.Range.FEET_120.value
    target = SpellStats.Target.THREE_CREATURES
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.HARMFUL
    dc = None
    dmg_type = DamageType.Force

    def __init__(self, action_type, caster):
        super().__init__()
        self.action_type = action_type  # MAGIC_MISSILE, QUICKENED_MAGIC_MISSILE
        self.dmg_dice = '1d4'
        self.dmg_bonus = 1
        self.combatant = caster

    def __str__(self):
        """
        Important for FSM building
        """
        return "MagicMissileFactory"

    def get_quickened_kwargs(self):
        return {'caster': self.combatant}

    def get_eligible_targets(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            return [swallower, swallower, swallower]
        # Range is so big that it doesn't matter
        return combinations_with_replacement([e for e in Map.get().get_enemies(self.combatant) if not e.is_affected_by(Conditions.SWALLOWED)], 3)

    def create_all(self):
        targets = self.get_eligible_targets()
        return [MagicMissile(t, self) for t in targets]

    def create(self, targets):
        return MagicMissile(targets, self)

    def calculate_threat_to_target(self, target, *args, **kwargs):
        battle_map = Map.get()
        if battle_map.get_cartesian_distance(self.combatant, target) <= MagicMissileFactory.range:
            return 3 * (mean_dmg_auto_hit(self.dmg_dice, target.is_resistant_to(MagicMissileFactory.dmg_type)) + self.dmg_bonus)
        else:
            return 0

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications.
        This is useful calculating the potential reduction of threat_in caused by abilities of enemies, e.g. advantage on saving throw
        against fireball or bane on attack rolls etc.
        """
        return 0

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        return max([self.calculate_threat_to_target(t) for t in targets])


class MagicMissile(Actoid, DirectThreat):

    def __init__(self, targets, factory, **kwargs):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_DIRECT_THREAT)
        self.targets = targets
        self.factory = factory
        self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.roll_type = RollType.STRAIGHT

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_SCORCHING_RAY else "") + f"Magic Missile on {self.targets[0]}, {self.targets[1]} and {self.targets[2]}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_SCORCHING_RAY else "") + "Magic Missile"


    def calculate_threat(self, *args, **kwargs):
        dmg_acc = mean_dmg_auto_hit(self.factory.dmg_dice, self.targets[0].is_resistant_to(MagicMissileFactory.dmg_type)) + self.factory.dmg_bonus
        dmg_acc += mean_dmg_auto_hit(self.factory.dmg_dice, self.targets[1].is_resistant_to(MagicMissileFactory.dmg_type)) + self.factory.dmg_bonus
        dmg_acc += mean_dmg_auto_hit(self.factory.dmg_dice, self.targets[2].is_resistant_to(MagicMissileFactory.dmg_type)) + self.factory.dmg_bonus
        return dmg_acc

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0

    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        coords_for_first = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[0]),
                                                                        distances,
                                                                        inflate_to_size=self.factory.combatant.size,
                                                                        rng=MagicMissileFactory.range,
                                                                        combatant=self.factory.combatant)
        coords_for_second = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[1]),
                                                                          distances,
                                                                          inflate_to_size=self.factory.combatant.size,
                                                                          rng=MagicMissileFactory.range,
                                                                          combatant=self.factory.combatant)
        coords_for_third = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[2]),
                                                                          distances,
                                                                          inflate_to_size=self.factory.combatant.size,
                                                                          rng=MagicMissileFactory.range,
                                                                          combatant=self.factory.combatant)
        return coords_for_third.intersection(coords_for_first.intersection(coords_for_second))

    def is_current_coord_eligible(self):
        if all([t is self.factory.combatant.get_swallower() for t in self.targets]):
            return True
        battle_map = Map.get()
        return battle_map.get_cartesian_distance(self.factory.combatant, self.targets[0]) <= MagicMissileFactory.range \
            and battle_map.get_cartesian_distance(self.factory.combatant, self.targets[1]) <= MagicMissileFactory.range \
            and battle_map.get_cartesian_distance(self.factory.combatant, self.targets[2]) <= MagicMissileFactory.range
