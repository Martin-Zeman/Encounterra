from simulator.actoid import Actoid
from simulator.action_types import Action
from simulator.misc import mean_dmg


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
            potential_targets = battle_map.get_enemies_within_hop_distance(combatant.movement + self.range - 1)
            potential_targets.sort(key=lambda e: e.curr_hp / e.max_hp)
            return potential_targets[0]

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
        # stats = kwargs['stats']
        # target_combatant = kwargs['target_combatant']
        # return mean_dmg(stats.to_hit, stats.dmg_dice, stats.dmg_bonus, target_combatant.ac, len(stats.crit_range))
        return 0 # TODO

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        stats = kwargs['stats']
        target_combatant = kwargs['target_combatant']
        return mean_dmg(self.stats.to_hit, self.stats.dmg_dice, self.stats.dmg_bonus, target_combatant.ac, len(stats.crit_range))
