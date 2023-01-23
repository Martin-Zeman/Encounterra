from simulator.misc import DamageType
from simulator.actions.actoid import Actoid
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.action_types import BonusAction
from simulator.misc import mean_dmg, dmg_increment_for_dmg_flat
from itertools import accumulate
import sys
from simulator.threat_calculator import ThreatModifier
import logging

logger = logging.getLogger(__name__)

class TotemRageFactory:

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
        return TotemRage(combatant)

class TotemRage(Actoid, CombatantEffect, LimitedDurationEffect, ThreatModifier):

    def __init__(self, combatant):
        Actoid.__init__(self, actoid_type=Actoid.Type.IS_TOGGLE_ABILITY, action_type=BonusAction.RAGE)
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, rounds=10)
        self.rage_bonus = TotemRageFactory.get_rage_bonus(combatant.level)

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


    @staticmethod
    def calculate_threat_mod_approx(combatant, battle_map, actions, *args, **kwargs):
        # TODO Multiply the threat increment by 3 for 3 rounds
        max_threat = 0
        potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.speed)
        best_attack = None
        # This doesn't take different attack ranges into account
        for attack in combatant.attacks:
            dmg_acc = accumulate(potential_targets, lambda pt: mean_dmg(attack.to_hit, attack.dmg_dice, attack.dmg_bonus, pt.ac,
                                                                        len(attack.crit_range), pt.is_resistant_to(attack.dmg_type)))
            dmg_acc /= len(potential_targets)
            max_threat = max(dmg_acc, max_threat)


        dmg_acc = accumulate(potential_targets, lambda pt: dmg_increment_for_dmg_flat(best_attack.to_hit, best_attack.dmg_dice, best_attack.dmg_bonus, pt.ac, self.rage_bonus)
        dmg_acc /= len(potential_targets)
        # TODO add avg dmg prevention
        return max_threat

    def calculate_threat_mod(self, combatant, battle_map, actions, *args, **kwargs):
        # TODO Multiply the threat increment by 3 for 3 rounds
        # TODO
        return 0