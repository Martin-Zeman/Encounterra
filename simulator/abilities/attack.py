from simulator.actoid import Actoid
from simulator.misc import mean_dmg
from itertools import accumulate
from simulator.misc import percent_of_curr_hp

class Attack(Actoid):
    class Stats:
        def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, eligible_action_types, crit_range=[20]):
            self.name = name
            self.combatant = combatant
            self.to_hit = to_hit
            self.dmg_dice = dmg_dice
            self.dmg_bonus = dmg_bonus
            self.dmg_type = dmg_type
            self.range = attack_range
            self.eligible_action_types = eligible_action_types  # ATTACK, BONUS_ATTACK, REACTION_ATTACK, HASTE_ATTACK...
            self.crit_range = crit_range

        def find_best_args(self, combatant, battle_map):
            # TODO consider prioritizing the ones you have a change to finish off
            potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.movement + self.range - 1)
            hp_percentages = [percent_of_curr_hp(pt, mean_dmg(self.to_hit, self.dmg_dice, self.dmg_bonus, pt.ac, len(self.crit_range))) for pt in potential_targets]
            potential_targets = list(zip(potential_targets, hp_percentages))
            potential_targets.sort(key=lambda e: e[1], reverse=True)
            return potential_targets[0][0]

    def __init__(self, target_combatant, stats):
        Actoid.__init__(self, actoid_type=Actoid.Type.IS_ATTACK_LIKE_ACTION)
        self.target_combatant = target_combatant
        self.stats = stats

    def set_target_combatant(self, target):
        self.target_combatant = target

    def get_target_combatant(self):
        return self.target_combatant

    def get_dmg_type(self):
        return self.dmg_type

    @staticmethod
    def calculate_threat_approx(combatant, battle_map, *args, **kwargs):
        max_threat = 0
        potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.speed)
        for attack in combatant.attacks:
            dmg_acc = accumulate(potential_targets, lambda pt: mean_dmg(combatant.spell_to_hit, attack.dmg_dice, attack.dmg_bonus, pt.ac, len(attack.crit_range), pt.is_resistant_to(attack.dmg_type)))
            dmg_acc /= len(potential_targets)
            max_threat = max(dmg_acc, max_threat)
        return max_threat

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        return mean_dmg(self.stats.to_hit, self.stats.dmg_dice, self.stats.dmg_bonus, self.target_combatant.ac, len(self.stats.crit_range), self.target_combatant.is_resistant_to(self.stats.dmg_type))
