from simulator.misc import DamageType
from simulator.actions.actoid import Actoid
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.action_types import BonusAction
from simulator.misc import dmg_increment_for_dmg_flat
from functools import reduce
from simulator.misc import ROUND_HORIZON
from simulator.abilities.rage import RageFactory
from simulator.threat_calculator import ThreatModifier
import logging

logger = logging.getLogger(__name__)

class TotemRageFactory:

    def __init__(self, combatant):
        self.combatant = combatant
        self.action_type = BonusAction.TOTEM_RAGE

    def create_best(self, combatant, battle_map):
        return TotemRage(combatant)

class TotemRage(Actoid, CombatantEffect, LimitedDurationEffect, ThreatModifier):

    def __init__(self, combatant):
        Actoid.__init__(self, actoid_type=Actoid.Type.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, rounds=10)
        self.rage_bonus = RageFactory.get_rage_bonus(combatant.level)

    def activate(self):
        self.combatants[0].ability_dmg_bonus += self.rage_bonus
        self.combatants[0].resistances.update(
            [DamageType.Slashing, DamageType.Bludgeoning, DamageType.Fire, DamageType.Lightning, DamageType.Acid, DamageType.Cold,
             DamageType.Force, DamageType.Necrotic, DamageType.Poison, DamageType.Radiant, DamageType.Piercing])

    def deactivate(self):
        logger.debug(f"{self.combatants[0]}'s rage fades")
        self.combatants[0].ability_dmg_bonus -= self.rage_bonus
        self.combatants[0].resistances.remove(DamageType.Slashing)
        self.combatants[0].resistances.remove(DamageType.Bludgeoning)
        self.combatants[0].resistances.remove(DamageType.Fire)
        self.combatants[0].resistances.remove(DamageType.Lightning)
        self.combatants[0].resistances.remove(DamageType.Acid)
        self.combatants[0].resistances.remove(DamageType.Cold)
        self.combatants[0].resistances.remove(DamageType.Force)
        self.combatants[0].resistances.remove(DamageType.Necrotic)
        self.combatants[0].resistances.remove(DamageType.Piercing)
        self.combatants[0].resistances.remove(DamageType.Poison)
        self.combatants[0].resistances.remove(DamageType.Radiant)


    # @staticmethod
    # def calculate_threat_mod_approx(combatant, battle_map, actions, *args, **kwargs):
    #     # TODO Multiply the threat increment by 3 for 3 rounds
    #     max_threat = 0
    #     potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.speed)
    #     best_attack = None
    #     # This doesn't take different attack ranges into account
    #     for attack in combatant.attacks:
    #         dmg_acc = reduce(lambda acc, pt: acc + mean_dmg(attack.to_hit, attack.dmg_dice, attack.dmg_bonus, pt.ac,
    #                                                         len(attack.crit_range), pt.is_resistant_to(attack.dmg_type)), potential_targets)
    #         dmg_acc /= len(potential_targets)
    #         max_threat = max(dmg_acc, max_threat)
    #
    #     dmg_acc = reduce(lambda acc, pt: acc + dmg_increment_for_dmg_flat(best_attack.to_hit, best_attack.dmg_dice, best_attack.dmg_bonus, pt.ac, self.rage_bonus), potential_targets)
    #     dmg_acc /= len(potential_targets)
    #     # TODO add avg dmg prevention
    #     return max_threat

    def calculate_threat_mod(self, combatant, battle_map, *args, **kwargs):
        """
        Finds the combatant's attack that benefits the most from the dmg increment. Then adds the estimated damage prevention equal to
        all remaining HP (better than regular rage)
        """
        rage_bonus = RageFactory.get_rage_bonus(combatant.level)
        total_threat = 0
        max_threat = 0
        potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.speed)
        # This doesn't take different attack ranges into account
        # TODO This could be moved to the mod threat calculation of the attack factory which should be called here for all the attacks
        for attack in combatant.attacks:
            dmg_acc = reduce(lambda acc, pt: acc + dmg_increment_for_dmg_flat(attack.to_hit, attack.dmg_dice, attack.dmg_bonus,
                                                                       pt.ac, rage_bonus), potential_targets)
            dmg_acc /= len(potential_targets)
            max_threat = max(dmg_acc, max_threat)

        total_threat += max_threat
        total_threat += combatant.curr_hp
        # TODO consider improving this by looping over enemy direct dmg dealing abilities
        return total_threat * ROUND_HORIZON
