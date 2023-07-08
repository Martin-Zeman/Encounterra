import logging
import math

from simulator.battle_map import Map
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.effect import EffectType
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from simulator.misc import reconcile_roll_types, Conditions
from functools import reduce
from simulator.misc import avg_roll
from simulator.threat_utils import mean_dmg, calculate_threat_in_delta
from simulator.threat_interfaces import DirectThreat, DirectThreatFactory
from enum import Enum, auto

from simulator.utils.roll_types import RollType, ROLL_TYPE, ROLL_TYPE_CRIT, ThreatModifierType


logger = logging.getLogger("EncounTroll")

class RecklessAttackFactory(DirectThreatFactory):

    class Type(Enum):
        MELEE = auto()
        RANGED = auto()

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=math.inf, on_hit=None, extra_dmg=[]):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.flags |= FactoryFlags.IS_HASTE_ELIGIBLE_ATTACK
        self.flags |= FactoryFlags.HAS_AMMO
        self.flags |= FactoryFlags.IS_MELEE
        self.flags |= FactoryFlags.USES_CALCULATE_THREAT_IN_DELTA
        self.name = name
        self.combatant = combatant
        self.to_hit = to_hit
        self.dmg_dice = dmg_dice
        self.dmg_bonus = dmg_bonus
        self.dmg_type = dmg_type
        self.extra_dmg = extra_dmg  # List of tuples of type (dmg_dice, dmg_type)
        self.range = attack_range
        self.action_type = action_type  # ATTACK, BONUS_ATTACK, REACTION_ATTACK, HASTE_ATTACK...
        self.ammo = math.inf
        self.crit_range = crit_range
        self.on_hit = on_hit

        # Here I'm keeping them as class instance variables to be able to call them in calculate_threat_approx
        self.mod_range = 0
        self.mod_to_hit_die = '0d0'
        self.mod_to_hit_flat = 0
        self.mod_dmg_flat = 0
        self.mod_dmg_die = '0d0'
        self.mod_crit_range = 0


    def __str__(self):
        """
        Important for FSM building
        """
        return "RecklessAttackFactory" + self.name


    def get_eligible_targets(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            return [swallower]
        battle_map = Map.get()
        return [e for e in battle_map.get_enemies(self.combatant) if not e.is_affected_by(Conditions.SWALLOWED)]

    def create_all(self):
        targets = self.get_eligible_targets()
        return [RecklessAttack(t, self) for t in targets]

    def calculate_threat_out_approx(self, combatant, roll_type=RollType.ADVANTAGE):
        """
        Helper function which calculates the average potential threat_out over all potential targets including all possible mods
        """
        battle_map = Map.get()
        potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.speed + 1 + self.mod_range)
        if not potential_targets:
            return 0
        def mean_dmg_delta(acc, pt):
            to_hit_total = self.to_hit + self.mod_to_hit_flat + avg_roll(self.mod_to_hit_die)
            to_hit_total += ROLL_TYPE[roll_type][max(0, min(pt.ac - to_hit_total, 20))]
            total_crit = self.crit_range + self.mod_crit_range
            total_crit *= ROLL_TYPE_CRIT[roll_type]
            return acc + mean_dmg(to_hit_total, "+".join([self.dmg_dice, self.mod_dmg_die]) if self.mod_dmg_die else self.dmg_dice,
                                  self.dmg_bonus + self.mod_dmg_flat, pt.ac, total_crit, pt.is_resistant_to(self.dmg_type))

        dmg_acc = reduce(mean_dmg_delta, potential_targets)
        dmg_acc /= len(potential_targets)
        return dmg_acc

    def calculate_threat_to_target(self, target, **kwargs):
        try:
            consider_dist = kwargs["consider_dist"]
        except KeyError:
            consider_dist = True
        dmg = 0
        battle_map = Map.get()
        if battle_map.get_hop_distance(self.combatant, target) <= self.range or not consider_dist:
            dmg = mean_dmg(self.to_hit + ROLL_TYPE[RollType.ADVANTAGE][max(0, min(target.ac - self.to_hit, 20))], self.dmg_dice, self.dmg_bonus, target.ac, self.crit_range * ROLL_TYPE_CRIT[RollType.ADVANTAGE], target.is_resistant_to(self.dmg_type))
        logger.info(f"MY DEBUG {self} dmg = {dmg}")
        # even the single target calculation the combatant is still more vulnerable to all potential attackers
        incoming_threat_delta_acc = calculate_threat_in_delta(self.combatant, 6, {ThreatModifierType.ROLL_TYPE: RollType.ADVANTAGE}, FactoryFlags.IS_ATTACK_LIKE)[1] / 2  # Heuristic
        logger.info(f"MY DEBUG {self} incoming_threat_delta_acc = {incoming_threat_delta_acc}")
        return dmg - incoming_threat_delta_acc

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications.
        This is useful calculating the potential reduction of threat_in caused by abilities of enemies, e.g. advantage on saving throw
        against fireball or bane on attack rolls etc.
        """
        try:
            consider_dist = kwargs["consider_dist"]
        except KeyError:
            consider_dist = True

        baseline = 0
        battle_map = Map.get()
        if battle_map.are_in_hop_range(self.combatant, target, self.range) or not consider_dist:
            baseline = mean_dmg(self.to_hit + ROLL_TYPE[RollType.ADVANTAGE][max(0, min(target.ac - self.to_hit, 20))], self.dmg_dice, self.dmg_bonus,
                                    target.ac, self.crit_range * ROLL_TYPE_CRIT[RollType.ADVANTAGE], target.is_resistant_to(self.dmg_type))
        logger.info(f"MY DEBUG {self} baseline threat = {baseline}")
        mod_range = modifiers.get(ThreatModifierType.RANGE, 0)
        mod_dmg_flat = modifiers.get(ThreatModifierType.DMG_BONUS_FLAT, 0)
        # mod_dmg_die = modifiers.get(ThreatModifierType.DMG_BONUS_DIE, '0d0')
        mod_to_hit_flat = modifiers.get(ThreatModifierType.TO_HIT_FLAT, 0)
        mod_to_hit_die = modifiers.get(ThreatModifierType.TO_HIT_DIE, '0d0')
        mod_crit_range = modifiers.get(ThreatModifierType.CRIT_RANGE, 0)
        auto_crit = modifiers.get(ThreatModifierType.AUTO_CRIT, False)
        roll_type = reconcile_roll_types({RollType.ADVANTAGE, modifiers.get(ThreatModifierType.ROLL_TYPE, RollType.ADVANTAGE)})

        modified = baseline
        with battle_map.as_if_dist_delta_from_combatant(self.combatant, target, -mod_range):
            if battle_map.are_in_hop_range(self.combatant, target, self.range) or not consider_dist:
                to_hit_total = self.to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
                to_hit_total += ROLL_TYPE[roll_type][max(0, min(target.ac - to_hit_total, 20))]
                total_crit = self.crit_range + mod_crit_range
                total_crit *= ROLL_TYPE_CRIT[roll_type]
                total_crit = 20 if auto_crit else total_crit
                modified = mean_dmg(to_hit_total, "+".join([self.dmg_dice, self.mod_dmg_die]), self.dmg_bonus + mod_dmg_flat, target.ac, total_crit, target.is_resistant_to(self.dmg_type))

        logger.info(f"MY DEBUG {self} modified threat = {modified}")

        incoming_threat_delta_acc = calculate_threat_in_delta(self.combatant, 6, {ThreatModifierType.ROLL_TYPE: RollType.ADVANTAGE}, FactoryFlags.IS_ATTACK_LIKE)[1] / 2  # Heuristic
        logger.info(f"MY DEBUG {self} incoming_threat_delta_acc = {incoming_threat_delta_acc}")
        return modified - baseline - incoming_threat_delta_acc

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        return max([self.calculate_threat_to_target(t) for t in targets])


class RecklessAttack(Actoid, DirectThreat, CombatantEffect, LimitedDurationEffect):

    def __init__(self, target, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_ATTACK_LIKE | ActoidFlags.IS_DIRECT_THREAT | ActoidFlags.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[factory.combatant])
        LimitedDurationEffect.__init__(self, turns=1)
        self.target = target
        self.factory = factory
        self.roll_type = RollType.ADVANTAGE

    def __str__(self):
        return f"Reckless Attack at {self.target}"

    def get_effect_type(self):
        return EffectType.RECKLESS_ATTACK

    def shorthand_str(self):
        return "Reckless Attack"

    def activate(self):
        Map.get().effect_tracker.add(self)

    def deactivate(self):
        pass

    def get_dmg_type(self):
        return self.factory.dmg_type


    def calculate_threat(self, **kwargs):
        return self.factory.calculate_threat_to_target(self.target, **kwargs)

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        """
        The delta in threat when modifiers are applied on this ability.
        """
        ret = self.factory.calculate_threat_to_target_delta(self.target, modifiers, *args, **kwargs)
        logger.info(f"MY DEBUG {self} threat = {ret}")
        return ret

    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        return battle_map.get_free_coords_in_hop_range(battle_map.get_combatant_position(self.target),
                                                       distances,
                                                       inflate_to_size=self.factory.combatant.size,
                                                       rng=self.factory.range,
                                                       combatant=self.factory.combatant)

    def is_current_coord_eligible(self):
        if self.factory.combatant.get_swallower() is self.target:
            return True
        return Map.get().are_in_hop_range(self.factory.combatant, self.target, self.factory.range)