from .action_types import Action
from ..actions.actoid import FactoryFlags, Actoid, ActoidFlags
from ..battle_map import Map
from ..misc import Conditions
import logging

from ..threat_interfaces import AttackThreatModifier
from ..factory_interfaces import DirectThreatFactory
from ..threat_utils import calc_p_hit
from ..utils.roll_types import RollType

logger = logging.getLogger("Encounterra")


class GrappleAttackFactory(DirectThreatFactory):

    def __init__(self, action_type, name, combatant, to_hit):
        super().__init__()
        self.action_type = action_type
        self.name = name
        self.combatant = combatant
        self.to_hit = to_hit
        self.flags |= FactoryFlags.IS_MELEE
        self.flags |= FactoryFlags.IS_ATTACK_LIKE

    def get_ability_name(self):
        return f"Grapple Attack with {self.name}"

    def get_kwargs(self):
        return {'name': self.name, 'combatant': self.combatant, 'to_hit': self.to_hit}

    def get_eligible_targets(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            return []
        return [e for e in Map.get().get_enemies(self.combatant) if not e.is_affected_by(Conditions.SWALLOWED)]

    def create(self, target):
        return GrappleAttack(target, self)

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [GrappleAttack(t, self) for t in targets]

    def calculate_threat_to_target(self, target, **kwargs):
        attack = kwargs["attack"]
        if attack.action_type is Action.VAMPIRIC_BITE:
            grappler_of_target = target.get_grappler()
            if grappler_of_target is self.combatant:
                return 0  # Already grappled by this combatant, won't bring any extra threat
            if target.is_affected_by_any(Conditions.INCAPACITATED, Conditions.RESTRAINED):
                return 0

            p_hit = calc_p_hit(attack.factory.to_hit, target.ac)
            return p_hit * attack.factory.calculate_threat_to_target(target, kwargs)
        else:
            return 0

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        baseline = mean_dmg(self.to_hit, self.dmg_dice, self.dmg_bonus, target.ac, self.crit_range,
                            target.is_resistant_to(self.dmg_type))
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
            to_hit_total += ROLL_TYPE_DELTA[roll_type][max(0, min(total_target_ac - to_hit_total, 20))]
        except KeyError:  # Can happen for extreme differences between the AC and the to_hit
            pass  # The effect is negligible in that case
        total_crit = self.crit_range + mod_crit_range
        total_crit *= ROLL_TYPE_CRIT_DELTA[roll_type]
        total_crit = 20 if auto_crit else total_crit
        try:
            modified = mean_dmg(to_hit_total, "+".join([self.dmg_dice, mod_dmg_die]) if mod_dmg_die else self.dmg_dice,
                                self.dmg_bonus + mod_dmg_flat, total_target_ac, total_crit,
                                target.is_resistant_to(self.dmg_type))
            for extra in self.extra_dmg:
                modified += mean_dmg(to_hit_total, extra[0], 0, total_target_ac, total_crit,
                                     target.is_resistant_to(extra[1]))
            if self.on_hit:
                modified += calc_p_hit(to_hit_total, target.ac) * self.on_hit.calculate_threat(self.combatant, target)
        except:
            logger.error("Error in mean_dmg of calculate_threat_to_target_delta of AttackFactory")
            modified = baseline
        return modified - baseline


class GrappleAttack(Actoid, AttackThreatModifier):

    def __init__(self, target, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_ATTACK_LIKE)
        self.target = target
        self.factory = factory
        self.roll_type = RollType.STRAIGHT

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        swallower = self.factory.combatant.get_swallower()
        if swallower:
            return None
        if not self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return battle_map.get_free_coords_in_hop_range(battle_map.get_combatant_position(self.target),
                                                           distances,
                                                           inflate_to_size=self.factory.combatant.size,
                                                           rng=self.factory.range,
                                                           combatant=self.factory.combatant)
        elif battle_map.are_in_hop_range(self.factory.combatant, self.target, self.factory.range):
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]

    def calculate_threat_for_attack(self, combatant, attack, *args, **kwargs):
        return self.factory.calculate_threat_to_target(attack.target, attack=attack)

    def calculate_threat(self, **kwargs):
        return 0
