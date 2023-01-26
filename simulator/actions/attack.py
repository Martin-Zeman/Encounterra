from simulator.actions.actoid import Actoid
from simulator.misc import mean_dmg
from itertools import accumulate
from simulator.misc import percent_of_curr_hp, avg_roll
from simulator.threat_calculator import DirectThreat, FactoryThreat
from enum import Enum, auto

class AttackFactory(FactoryThreat):

    class Type(Enum):
        MELEE = auto()
        RANGED = auto()

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, attack_type, crit_range=[20]):
        self.name = name
        self.combatant = combatant
        self.to_hit = to_hit
        self.dmg_dice = dmg_dice
        self.dmg_bonus = dmg_bonus
        self.dmg_type = dmg_type
        self.range = attack_range
        self.action_type = action_type  # ATTACK, BONUS_ATTACK, REACTION_ATTACK, HASTE_ATTACK...
        self.attack_type = attack_type  # MELEE or RANGED
        self.crit_range = crit_range
        self.mod_range = 0
        self.mod_to_hit_die = ''
        self.mod_to_hit_flat = 0
        self.mod_dmg_flat = 0
        self.mod_dmg_die = ''
        self.mod_crit_range = 0

    def find_best_args(self, combatant, battle_map):
        # TODO consider prioritizing the ones you have a change to finish off
        if self.attack_type is AttackFactory.Type.MELEE:
            potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.movement + self.range + 1)
        else:
            potential_targets = battle_map.get_enemies_within_radius(combatant, combatant.movement + self.range)
        hp_percentages = [percent_of_curr_hp(pt, mean_dmg(self.to_hit, self.dmg_dice, self.dmg_bonus, pt.ac, len(self.crit_range))) for pt
                          in potential_targets]
        potential_targets = list(zip(potential_targets, hp_percentages))
        potential_targets.sort(key=lambda e: e[1], reverse=True)
        return potential_targets[0][0]

    def create_best(self, combatant, battle_map):
        return Attack(self.find_best_args(combatant, battle_map), self)

    def calculate_threat_approx(self, combatant, battle_map, *args, **kwargs):
        potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.speed + 1 + self.mod_range)
        dmg_acc = accumulate(potential_targets, lambda pt: mean_dmg(self.to_hit + self.mod_to_hit_flat + avg_roll(self.mod_to_hit_die),
                                                                    "+".join(self.dmg_dice,
                                                                             self.mod_dmg_die) if self.mod_dmg_die else self.dmg_dice,
                                                                    self.dmg_bonus + self.mod_dmg_flat, pt.ac,
                                                                    len(self.crit_range) + self.mod_crit_range,
                                                                    pt.is_resistant_to(self.dmg_type)))
        dmg_acc /= len(potential_targets)
        return dmg_acc


    def calculate_threat_approx_mod(self, battle_map, modified_stats, *args, **kwargs):
        """
        Goes over all the modified stats and accumulates the threat delta for all of them
        """
        # TODO
        baseline = self.calculate_threat_approx(self.combatant, battle_map, *args, **kwargs)
        try:
            self.range_mod = modified_stats['range']
        except KeyError:
            self.range_mod = 0
        try:
            self.mod_dmg_flat = modified_stats['dmg_bonus_flat']
        except KeyError:
            self.mod_dmg_flat = 0
        try:
            self.mod_dmg_die = modified_stats['dmg_bonus_die']
        except KeyError:
            self.mod_dmg_die = ''
        try:
            self.mod_to_hit_flat = modified_stats['to_hit_flat']
        except KeyError:
            self.mod_to_hit_flat = 0
        try:
            self.mod_to_hit_die = modified_stats['to_hit_die']
        except KeyError:
            self.mod_to_hit_die = ''
        try:
            self.mod_crit_range = modified_stats['crit_range']
        except KeyError:
            self.mod_crit_range = 0

        try:
            modified = self.calculate_threat_approx(self.combatant, battle_map, *args, **kwargs)
        except:
            pass # just make sure the original stats are restored

        self.mod_range = 0
        self.mod_to_hit_die = ''
        self.mod_to_hit_flat = 0
        self.mod_dmg_flat = 0
        self.mod_dmg_die = ''
        self.mod_crit_range = 0
        return modified - baseline


class Attack(Actoid, DirectThreat):

    def __init__(self, target_combatant, factory):
        Actoid.__init__(self, actoid_type=Actoid.Type.IS_ATTACK_LIKE_ACTION, is_direct_dmg_dealing=True)
        self.target_combatant = target_combatant
        self.factory = factory

    def get_dmg_type(self):
        return self.factory.dmg_type


    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        return mean_dmg(self.factory.to_hit, self.factory.dmg_dice, self.factory.dmg_bonus, self.target_combatant.ac, len(self.factory.crit_range),
                        self.target_combatant.is_resistant_to(self.factory.dmg_type))
