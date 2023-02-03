from simulator.misc import DamageType
from simulator.actions.actoid import Actoid
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.action_types import BonusAction
from simulator.misc import dmg_increment_for_dmg_flat, ROUND_HORIZON
from functools import reduce
import sys
from simulator.threat_calculator import ThreatModifier, FactoryThreat
import logging

logger = logging.getLogger(__name__)

class RageFactory(FactoryThreat):

    def __init__(self, combatant):
        self.combatant = combatant
        self.action_type = BonusAction.RAGE

    @staticmethod
    def get_rage_bonus(level):
        match level:
            case lvl if 1 <= lvl <= 8:
                return 2
            case lvl if 9 <= lvl <= 15:
                return 3
            case lvl if 16 <= lvl:
                return 4
            case _:
                logger.error("Incorrect combatant level of rage")
                return 2

    @staticmethod
    def get_rage_uses(level):
        match level:
            case lvl if 1 <= lvl <= 2:
                return 2
            case lvl if 3 <= lvl <= 5:
                return 3
            case lvl if 6 <= lvl <= 11:
                return 4
            case lvl if 12 <= lvl <= 16:
                return 5
            case lvl if 17 <= lvl <= 19:
                return 6
            case 20:
                return sys.maxsize
            case _:
                logger.error("Incorrect combatant level of rage")
                return 2

    def create_best(self, combatant, battle_map):
        return Rage(combatant)

    # @staticmethod
    # def calc_rage_threat(combatant, battle_map):
    #     """
    #     Finds the combatant's attack that benefits the most from the dmg increment. Then adds the estimated damage prevention equal to
    #     half of remaining HP
    #     """
    #     rage_bonus = RageFactory.get_rage_bonus(combatant.level)
    #     total_threat = 0
    #     max_threat = 0
    #     potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.speed)
    #     # This doesn't take different attack ranges into account
    #     # TODO This could be moved to the mod threat calculation of the attack factory which should be called here for all the attacks
    #     for attack in combatant.attacks:
    #         dmg_acc = reduce(lambda acc, pt: acc + dmg_increment_for_dmg_flat(attack.to_hit, attack.dmg_dice, attack.dmg_bonus,
    #                                                                    pt.ac, rage_bonus), potential_targets)
    #         dmg_acc /= len(potential_targets)
    #         max_threat = max(dmg_acc, max_threat)
    #
    #     total_threat += max_threat
    #     total_threat += (combatant.curr_hp / 2)
    #     # TODO consider improving this by looping over enemy direct dmg dealing abilities
    #     return total_threat * ROUND_HORIZON

    def calculate_threat_approx_mod(self, battle_map, modified_stats, *args, **kwargs):
        return 0 # no need

    # def calculate_threat_approx(self, battle_map, *args, **kwargs):
    #     return RageFactory.calc_rage_threat(self.combatant, battle_map)


class Rage(Actoid, CombatantEffect, LimitedDurationEffect, ThreatModifier):

    def __init__(self, combatant):
        Actoid.__init__(self, actoid_type=Actoid.Type.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, rounds=10)
        self.rage_bonus = RageFactory.get_rage_bonus(combatant.level)

    def activate(self):
        self.combatants[0].ability_dmg_bonus += self.rage_bonus
        self.combatants[0].resistances.update([DamageType.Slashing, DamageType.Bludgeoning, DamageType.Piercing])

    def deactivate(self):
        logger.debug(f"{self.combatants[0]}'s rage fades")
        self.combatants[0].ability_dmg_bonus -= self.rage_bonus
        self.combatants[0].resistances.remove(DamageType.Slashing)
        self.combatants[0].resistances.remove(DamageType.Bludgeoning)
        self.combatants[0].resistances.remove(DamageType.Piercing)


    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        """
        Finds the combatant's attack that benefits the most from the dmg increment. Then adds the estimated damage prevention equal to
        half of remaining HP
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
        total_threat += (combatant.curr_hp / 2)
        # TODO consider improving this by looping over enemy direct dmg dealing abilities
        return total_threat * ROUND_HORIZON