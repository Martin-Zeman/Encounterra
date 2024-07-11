import copy

from cachetools.keys import hashkey

from ..actions.action_types import HasteAction
from ..actions.actoid import Actoid, FactoryFlags, ActoidFlags
from functools import cache
from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key
from ..conditions import get_swallower
from ..misc import avg_roll
from ..resources import Uses, ResourceRefreshType
from ..threat_utils import mean_dmg, calc_p_hit
from ..threat_interfaces import DirectThreat
from ..factory_interfaces import DirectThreatFactory
from enum import Enum, auto
import math
import logging
from ..utils.roll_types import RollType, ROLL_TYPE_CRIT_DELTA, ROLL_TYPE_DELTA, ThreatModifierType

logger = logging.getLogger("Encounterra")


class AttackFactory(DirectThreatFactory):

    class Type(Enum):
        MELEE = auto()
        RANGED = auto()

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=Uses(math.inf, ResourceRefreshType.NEVER), on_hit=None, extra_dmg=None, uses_dex=False, two_handed=False, to_hit_bonus_die=None):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_LIKE
        self.flags |= FactoryFlags.IS_HASTE_ELIGIBLE_ATTACK
        self.name = name
        self.combatant = combatant
        self.to_hit = to_hit
        self.dmg_dice = dmg_dice
        self.dmg_bonus = dmg_bonus
        self.dmg_type = dmg_type
        self.extra_dmg = extra_dmg if extra_dmg is not None else []  # Create a new list if `on_hit` is None to prevent sharing among different instances
        self.range = attack_range
        self.short_range = attack_range // 4
        self.action_type = action_type  # MELEE_ATTACK, RANGED_ATTACK, BONUS_MELEE_ATTACK, BONUS_RANGED_ATTACK REACTION_ATTACK, HASTE_MELEE...
        self.crit_range = crit_range
        self.ammo = ammo
        self.on_hit = on_hit if on_hit is not None else []  # Create a new list if `on_hit` is None to prevent sharing among different instances
        self.to_hit_bonus_die = to_hit_bonus_die  # This is not really applied, only used to simplify threat calculation of derived classes
        # Here I'm keeping them as class instance variables to be able to call them in calculate_threat_approx
        self.mod_range = 0
        self.mod_to_hit_die = (0, 0)
        self.mod_to_hit_flat = 0
        self.mod_dmg_flat = 0
        self.mod_dmg_die = ((0, 0),)
        self.mod_crit_range = 0
        if uses_dex:
            self.flags |= FactoryFlags.USES_DEX
        if two_handed:
            self.flags |= FactoryFlags.TWO_HANDED

    def __str__(self):
        return self.name + " AttackFactory"

    def get_kwargs(self):
        return {'name': self.name, 'combatant': self.combatant, 'to_hit': self.to_hit, 'dmg_dice': self.dmg_dice,
                'dmg_bonus': self.dmg_bonus, 'dmg_type': self.dmg_type, 'attack_range': self.range, 'action_type': self.action_type,
                'crit_range': self.crit_range, 'ammo': self.ammo, 'on_hit': copy.deepcopy(self.on_hit), 'extra_dmg': copy.deepcopy(self.extra_dmg),
                'uses_dex': FactoryFlags.USES_DEX in self.flags, 'two_handed': FactoryFlags.TWO_HANDED in self.flags,
                'to_hit_bonus_die': self.to_hit_bonus_die}

    def get_eligible_targets(self):
        swallower = get_swallower(self.combatant)
        if swallower:
            return [swallower]
        return [e for e in Map.get().get_non_swallowed_enemies(self.combatant)]

    def create(self, target):
        return Attack(target, self)

    def calculate_threat_to_target(self, target, **kwargs):
        consider_dist = kwargs.get("consider_dist", False)
        roll_type = kwargs.get("roll_type", RollType.STRAIGHT)

        to_hit_total = self.to_hit
        to_hit_total += ROLL_TYPE_DELTA[roll_type][max(0, min(target.ac - to_hit_total, 20))]
        if self.to_hit_bonus_die is not None:
            to_hit_total += avg_roll(self.to_hit_bonus_die)

        # TODO: Should I include roll types here? There may be a use-case in the future
        if not consider_dist or Map.get().get_hop_distance_combatants(self.combatant, target) <= self.range:
            acc = mean_dmg(to_hit_total, self.dmg_dice, self.dmg_bonus, target.ac,
                           target.is_immune_to(self.dmg_type), target.is_resistant_to(self.dmg_type), self.crit_range)
            for extra in self.extra_dmg:
                acc += mean_dmg(to_hit_total, (extra[0],), 0, target.ac,
                                target.is_immune_to(extra[1]), target.is_resistant_to(extra[1]),
                                self.crit_range)
            for oh in self.on_hit:
                acc += calc_p_hit(to_hit_total, target.ac) * oh.calculate_threat(self.combatant, target)
            return acc
        return 0

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        avg_to_hit_bonus_die_roll = 0
        if self.to_hit_bonus_die is not None:
            avg_to_hit_bonus_die_roll = avg_roll(self.to_hit_bonus_die)
        baseline_to_hit = self.to_hit + avg_to_hit_bonus_die_roll
        baseline = mean_dmg(baseline_to_hit, self.dmg_dice, self.dmg_bonus, target.ac,
                            target.is_immune_to(self.dmg_type), target.is_resistant_to(self.dmg_type), self.crit_range)
        for extra in self.extra_dmg:
            baseline += mean_dmg(baseline_to_hit, (extra[0],), 0, target.ac,
                                 target.is_immune_to(extra[1]), target.is_resistant_to(extra[1]),
                                 self.crit_range)
        for oh in self.on_hit:
            baseline += calc_p_hit(baseline_to_hit, target.ac) * oh.calculate_threat(self.combatant, target)
        mod_dmg_flat = modifiers.get(ThreatModifierType.DMG_BONUS_FLAT, 0)
        mod_dmg_die = modifiers.get(ThreatModifierType.DMG_BONUS_DIE, ((0, 0),))
        mod_to_hit_flat = modifiers.get(ThreatModifierType.TO_HIT_FLAT, 0)
        mod_to_hit_die = modifiers.get(ThreatModifierType.TO_HIT_DIE, (0, 0))
        mod_crit_range = modifiers.get(ThreatModifierType.CRIT_RANGE, 0)
        auto_crit = modifiers.get(ThreatModifierType.AUTO_CRIT, False)
        target_ac = modifiers.get(ThreatModifierType.TARGET_AC, 0)
        roll_type = modifiers.get(ThreatModifierType.ROLL_TYPE, RollType.STRAIGHT)

        total_target_ac = target.ac + target_ac
        to_hit_total = baseline_to_hit + mod_to_hit_flat + avg_roll(mod_to_hit_die)
        try:
            to_hit_total += ROLL_TYPE_DELTA[roll_type][max(0, min(total_target_ac - to_hit_total, 20))]
        except KeyError:  # Can happen for extreme differences between the AC and the to_hit
            pass  # The effect is negligible in that case
        total_crit = self.crit_range + mod_crit_range
        total_crit *= ROLL_TYPE_CRIT_DELTA[roll_type]
        total_crit = 20 if auto_crit else total_crit
        try:
            modified = mean_dmg(to_hit_total, self.dmg_dice + mod_dmg_die, self.dmg_bonus + mod_dmg_flat,
                                total_target_ac, target.is_immune_to(self.dmg_type),
                                target.is_resistant_to(self.dmg_type), total_crit)
            for extra in self.extra_dmg:
                modified += mean_dmg(to_hit_total, (extra[0],), 0, total_target_ac,
                                     target.is_immune_to(extra[1]), target.is_resistant_to(extra[1]), total_crit)
            for oh in self.on_hit:
                modified += calc_p_hit(to_hit_total, total_target_ac) * oh.calculate_threat(self.combatant, target)
        except:
            logger.error("Error in mean_dmg of calculate_threat_to_target_delta of AttackFactory")
            modified = baseline
        return modified - baseline

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        if not targets:
            return 0
        return max([self.calculate_threat_to_target(t) for t in targets])


class Attack(Actoid, DirectThreat):

    def __init__(self, target, factory):
        Actoid.__init__(self, ActoidFlags.IS_ATTACK_LIKE)
        self.target = target
        self.factory = factory
        self.roll_type = RollType.STRAIGHT

    def __str__(self):
        form_prefix = str(self.factory.combatant.get_current_form()).split()[-1] + " " if self.factory.combatant.get_original_form() is not self.factory.combatant else ""
        return form_prefix + ("Hasted " if isinstance(self.factory.action_type, HasteAction) else "") + self.factory.name + f" on {self.target}"

    def shorthand_str(self):
        return ("Hasted " if isinstance(self.factory.action_type, HasteAction) else "") + self.factory.name

    def get_dmg_type(self):
        return self.factory.dmg_type

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        return self.factory.calculate_threat_to_target(self.target, **kwargs)

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        self.calculate_threat_delta.cache_clear()
        #self.get_eligible_coords.cache_clear()

    @map_toggled_cache_with_key(key=lambda self, modifiers, *args, **kwargs: hashkey(self.factory.name, tuple(modifiers.items()), tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return self.factory.calculate_threat_to_target_delta(self.target, modifiers, *args, **kwargs)
