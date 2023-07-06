from simulator.actions.action_types import HasteAction
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import reduce, cache

from simulator.battle_map import Map
from simulator.misc import avg_roll, Conditions
from simulator.threat_utils import mean_dmg, calc_p_hit
from simulator.threat_interfaces import DirectThreat, DirectThreatFactory
from enum import Enum, auto
import math
import logging

from simulator.utils.roll_types import RollType, ROLL_TYPE_CRIT, ROLL_TYPE, ThreatModifierType

logger = logging.getLogger("EncounTroll")

class AttackFactory(DirectThreatFactory):

    class Type(Enum):
        MELEE = auto()
        RANGED = auto()

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=math.inf, on_hit=None, extra_dmg=[]):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.flags |= FactoryFlags.IS_HASTE_ELIGIBLE_ATTACK
        self.flags |= FactoryFlags.HAS_AMMO
        self.name = name
        self.combatant = combatant
        self.to_hit = to_hit
        self.dmg_dice = dmg_dice
        self.dmg_bonus = dmg_bonus
        self.dmg_type = dmg_type
        self.extra_dmg = extra_dmg  # List of tuples of type (dmg_dice, dmg_type)
        self.range = attack_range
        self.short_range = attack_range // 4
        self.action_type = action_type  # MELEE_ATTACK, RANGED_ATTACK, BONUS_MELEE_ATTACK, BONUS_RANGED_ATTACK REACTION_ATTACK, HASTE_MELEE...
        self.crit_range = crit_range
        self.ammo = ammo
        self.on_hit = on_hit
        # Here I'm keeping them as class instance variables to be able to call them in calculate_threat_approx
        self.mod_range = 0
        self.mod_to_hit_die = '0d0'
        self.mod_to_hit_flat = 0
        self.mod_dmg_flat = 0
        self.mod_dmg_die = '0d0'
        self.mod_crit_range = 0

    def __str__(self):
        return self.name + " AttackFactory"

    def get_kwargs(self):
        return {'name': self.name, 'combatant': self.combatant, 'to_hit': self.to_hit, 'dmg_dice': self.dmg_dice,
                'dmg_bonus': self.dmg_bonus, 'dmg_type': self.dmg_type, 'attack_range': self.range, 'action_type': self.action_type,
                'crit_range': self.crit_range, 'ammo': self.ammo, 'on_hit': self.on_hit}

    def get_eligible_targets(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            return [swallower]
        return [e for e in Map.get().get_enemies(self.combatant) if not e.is_affected_by(Conditions.SWALLOWED)]

    def create(self, target_combatant):
        return Attack(target_combatant, self)

    # def calculate_threat_approx(self, combatant, roll_type=RollType.STRAIGHT):
    #     """
    #     Helper function which calculates the average potential threat over all potential targets including all possible mods
    #     """
    #     potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.speed + 1 + self.mod_range)
    #     if not potential_targets:
    #         return 0
    #     def mean_dmg_mod(acc, pt):
    #         to_hit_total = self.to_hit + self.mod_to_hit_flat + avg_roll(self.mod_to_hit_die)
    #         to_hit_total += ROLL_TYPE[roll_type][max(0, min(pt.ac - to_hit_total, 20))]
    #         total_crit = self.crit_range + self.mod_crit_range
    #         total_crit *= ROLL_TYPE_CRIT[roll_type]
    #         acc += mean_dmg(to_hit_total, "+".join([self.dmg_dice, self.mod_dmg_die]) if self.mod_dmg_die else self.dmg_dice,
    #                               self.dmg_bonus + self.mod_dmg_flat, pt.ac, total_crit, pt.is_resistant_to(self.dmg_type))
    #         for extra in self.extra_dmg:
    #             acc += mean_dmg(to_hit_total, extra[0], 0, pt.ac, total_crit, pt.is_resistant_to(extra[1]))
    #         return acc
    #
    #     dmg_acc = reduce(mean_dmg_mod, potential_targets)
    #     dmg_acc /= len(potential_targets)
    #     return dmg_acc


    def calculate_threat_to_target(self, target, *args, **kwargs):
        try:
            consider_dist = kwargs["consider_dist"]
        except KeyError:
            consider_dist = False
        try:
            roll_type = kwargs['roll_type']
        except KeyError:
            roll_type = RollType.STRAIGHT

        to_hit_total = self.to_hit
        to_hit_total += ROLL_TYPE[roll_type][max(0, min(target.ac - to_hit_total, 20))]

        # TODO: Should I include roll types here? There may be a use-case in the future
        if not consider_dist or Map.get().get_hop_distance(self.combatant, target) <= self.range:
            acc = mean_dmg(to_hit_total, self.dmg_dice, self.dmg_bonus, target.ac, self.crit_range, target.is_resistant_to(self.dmg_type))
            for extra in self.extra_dmg:
                acc += mean_dmg(to_hit_total, extra[0], 0, target.ac, self.crit_range, target.is_resistant_to(extra[1]))
            if self.on_hit:
                acc += calc_p_hit(to_hit_total, target.ac) * self.on_hit.calculate_threat(self.combatant, target)
            return acc
        return 0

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        baseline = mean_dmg(self.to_hit, self.dmg_dice, self.dmg_bonus, target.ac, self.crit_range, target.is_resistant_to(self.dmg_type))
        for extra in self.extra_dmg:
            baseline += mean_dmg(self.to_hit, extra[0], 0, target.ac, self.crit_range, target.is_resistant_to(extra[1]))
        if self.on_hit:
            baseline += calc_p_hit(self.to_hit, target.ac) * self.on_hit.calculate_threat(self.combatant, target)
        mod_dmg_flat = modifiers.get(ThreatModifierType.DMG_BONUS_FLAT, 0)
        mod_dmg_die = modifiers.get(ThreatModifierType.DMG_BONUS_DIE, '0d0')
        mod_to_hit_flat = modifiers.get(ThreatModifierType.TO_HIT_FLAT, 0)
        mod_to_hit_die = modifiers.get(ThreatModifierType.TO_HIT_DIE, '0d0')
        mod_crit_range = modifiers.get(ThreatModifierType.CRIT_RANGE, 0)
        auto_crit = modifiers.get(ThreatModifierType.AUTO_CRIT, False)
        target_ac = modifiers.get(ThreatModifierType.TARGET_AC, 0)
        roll_type = modifiers.get(ThreatModifierType.ROLL_TYPE, RollType.STRAIGHT)

        total_target_ac = target.ac + target_ac
        to_hit_total = self.to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
        try:
            to_hit_total += ROLL_TYPE[roll_type][max(0, min(total_target_ac - to_hit_total, 20))]
        except KeyError:  # Can happen for extreme differences between the AC and the to_hit
            pass  # The effect is negligible in that case
        total_crit = self.crit_range + mod_crit_range
        total_crit *= ROLL_TYPE_CRIT[roll_type]
        total_crit = 20 if auto_crit else total_crit
        try:
            modified = mean_dmg(to_hit_total, "+".join([self.dmg_dice, mod_dmg_die]) if mod_dmg_die else self.dmg_dice, self.dmg_bonus + mod_dmg_flat, total_target_ac, total_crit, target.is_resistant_to(self.dmg_type))
            for extra in self.extra_dmg:
                modified += mean_dmg(to_hit_total, extra[0], 0, total_target_ac, total_crit, target.is_resistant_to(extra[1]))
            if self.on_hit:
                modified += calc_p_hit(to_hit_total, target.ac) * self.on_hit.calculate_threat(self.combatant, target)
        except:
            logger.error("Error in mean_dmg of calculate_threat_to_target_delta of AttackFactory")
            modified = baseline
        return modified - baseline

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        return max([self.calculate_threat_to_target(t) for t in targets])


class Attack(Actoid, DirectThreat):

    def __init__(self, target_combatant, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_ATTACK_LIKE | ActoidFlags.IS_DIRECT_THREAT)
        self.target_combatant = target_combatant
        self.factory = factory
        self.roll_type = RollType.STRAIGHT

    def __str__(self):
        form_prefix = str(self.factory.combatant.get_current_form()).split()[-1] + " " if self.factory.combatant.get_original_form() is not self.factory.combatant else ""
        return form_prefix + ("Hasted " if isinstance(self.factory.action_type, HasteAction) else "") + self.factory.name + f" on {self.target_combatant}"

    def shorthand_str(self):
        return ("Hasted " if isinstance(self.factory.action_type, HasteAction) else "") + self.factory.name

    def get_dmg_type(self):
        return self.factory.dmg_type


    def calculate_threat(self, *args, **kwargs):
        return self.factory.calculate_threat_to_target(self.target_combatant, **kwargs)

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return self.factory.calculate_threat_to_target_delta(self.target_combatant, modifiers, *args, **kwargs)
