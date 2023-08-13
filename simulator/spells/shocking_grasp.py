from cachetools import cached
from cachetools.keys import hashkey

from simulator.actions.action_types import BonusAction
from simulator.battle_map import Map, map_position_toggled_cache, map_position_toggled_cache_with_key
from simulator.spells.spell import SpellStats
from simulator.misc import DamageType, RollType, avg_roll, Conditions
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import cache
from simulator.threat_utils import mean_dmg
from simulator.threat_interfaces import DirectThreat, DirectThreatFactory
import logging
from simulator.utils.roll_types import ROLL_TYPE_CRIT_DELTA, ROLL_TYPE_DELTA, ThreatModifierType

logger = logging.getLogger("Encounterra")

class ShockingGraspFactory(DirectThreatFactory):
    level = 0
    range = SpellStats.Range.TOUCH.value
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.HARMFUL
    dc = None
    dmg_type = DamageType.Lightning

    def __init__(self, to_hit, action_type, caster, crit_range=1):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.flags |= FactoryFlags.IS_MELEE
        self.to_hit = to_hit
        self.action_type = action_type  # SHOCKING_GRASP, QUICKENED_SHOCKING_GRASP
        self.dmg_dice = '1d8'
        self.combatant = caster
        self.crit_range = crit_range

    def __str__(self):
        """
        Important for FSM building
        """
        return "FireboltFactory"


    def get_twinned_kwargs(self):
        return {'to_hit': self.to_hit, 'caster': self.combatant}

    def get_quickened_kwargs(self):
        return {'to_hit': self.to_hit, 'caster': self.combatant}

    def get_eligible_targets(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            return [swallower]
        return [e for e in Map.get().get_enemies(self.combatant) if not e.is_affected_by(Conditions.SWALLOWED)]

    def create_all(self):
        targets = self.get_eligible_targets()
        return [ShockingGrasp(t, self) for t in targets]

    def create(self, target):
        return ShockingGrasp(target, self)


    def calculate_threat_to_target(self, target, **kwargs):
        battle_map = Map.get()
        if battle_map.get_cartesian_distance_combatants(self.combatant, target) <= ShockingGraspFactory.range:
            return mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(ShockingGraspFactory.dmg_type))
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
        target_ac = modifiers.get(ThreatModifierType.TARGET_AC, 0)

        total_target_ac = target_ac + target.ac
        to_hit_total = self.to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
        to_hit_total += ROLL_TYPE_DELTA[roll_type][max(0, min(total_target_ac - to_hit_total, 20))]
        total_crit = ROLL_TYPE_CRIT_DELTA[roll_type]

        ret = mean_dmg(to_hit_total, self.dmg_dice, 0, total_target_ac, total_crit, target.is_resistant_to(ShockingGraspFactory.dmg_type)) - mean_dmg(self.to_hit, self.dmg_dice, 0, target.ac, 1, target.is_resistant_to(
                    ShockingGraspFactory.dmg_type))
        # logger.warning(f"MY DEBUG {self} calculate_threat_to_target_delta = {ret}")
        return ret

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        ret = max([self.calculate_threat_to_target(t) for t in targets])
        # logger.warning(f"MY DEBUG {self} calculate_max_threat = {ret}")
        return ret


class ShockingGrasp(Actoid, DirectThreat):
    def __init__(self, target, factory, **kwargs):
        super().__init__(actoid_flags=ActoidFlags.IS_SPELL | ActoidFlags.IS_ATTACK_LIKE | ActoidFlags.IS_DIRECT_THREAT)
        self.target = target
        self.factory = factory
        self.empowered = kwargs.get("empowered", False)
        self.roll_type = RollType.STRAIGHT

    def __str__(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_SHOCKING_GRASP else "") + f"Shocking Grasp on {self.target}"

    def shorthand_str(self):
        return ("Quickened " if self.factory.action_type is BonusAction.QUICKENED_SHOCKING_GRASP else "") + "Shocking Grasp"

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        return self.factory.calculate_threat_to_target(self.target)

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        self.calculate_threat_delta.cache_clear()
        self.get_eligible_coords.cache_clear()

    @map_position_toggled_cache_with_key(key=lambda self, modifiers, *args, **kwargs: hashkey(tuple(modifiers.items()), tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return self.factory.calculate_threat_to_target_delta(self.target, modifiers, *args, **kwargs)

    @cached(cache={}, key=lambda self, distances, shortest_paths: hashkey(self.factory.combatant.name))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        swallower = self.factory.combatant.get_swallower()
        if swallower:
            if swallower is self.target:
                return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
            return None
        if self.factory.combatant.movement > 0 and not self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.target),
                                                                 distances,
                                                                 inflate_to_size=self.factory.combatant.size,
                                                                 rng=ShockingGraspFactory.range, combatant=self.factory.combatant)
        elif battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.target) <= ShockingGraspFactory.range:
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
        return None
