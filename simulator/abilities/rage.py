from simulator.combatant_coords import CombatantCoords
from simulator.misc import DamageType, get_attacks
from simulator.actions.actoid import Actoid, ActoidFlags, FactoryFlags
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.action_types import BonusAction
from simulator.misc import ROUND_HORIZON
from functools import reduce
import sys

from simulator.threat import dmg_increment_for_dmg_flat
from simulator.threat_calculator import ThreatModifier, ThreatModifierFactory
import logging

logger = logging.getLogger("EncounTroll")

class RageFactory(ThreatModifierFactory):

    def __init__(self, combatant):
        self.flags |= FactoryFlags.IS_ATTACK_MODIFIER
        self.flags |= FactoryFlags.TARGETS_SELF
        self.combatant = combatant
        self.action_type = BonusAction.RAGE

    def __str__(self):
        """
        Important for FSM building
        """
        return "RageFactory"

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

    def get_eligible_targets(self, battle_map):
        pass # No need due to the TARGETS_SELF flag

    def create_best(self, combatant, battle_map):
        return Rage(self.combatant, self)

    # def create_mock(self):
    #     return Rage(None)

    def create_all(self, battle_map):
        return [Rage(self.combatant, self)]

    def create(self, target_combatant):
        # Doesn't make much sense here
        return Rage(target_combatant, self)

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        Calculates the threat the factory is capable of dealing to a specific target.
        This is useful for calculating threat_in from the abilities of enemies
        """
        rage_bonus = RageFactory.get_rage_bonus(self.combatant.level)
        total_threat = 0
        max_threat = 0
        # This doesn't take different attack ranges into account
        # TODO This could be moved to the mod threat calculation of the attack factory which should be called here for all the attacks
        attacks = get_attacks(self.combatant)
        for attack in attacks:
            dmg_inc = attack.calculate_threat_to_target_mod(battle_map, self, {"dmg_bonus_flat": rage_bonus})
            max_threat = max(dmg_inc, max_threat)

        total_threat += max_threat
        # Haste factories wouldn't change the result here, so we're omitting them
        max_incoming_threat = 0
        for f in target.action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags:
                max_incoming_threat = max(max_incoming_threat, f[1].calculate_threat_to_target(battle_map, self.combatant))
        total_threat += max_incoming_threat / 3  # Heuristic to account for the fact it doesn't give resistance to all dmg types

        max_incoming_threat = 0
        for f in target.bonus_action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags:
                max_incoming_threat = max(max_incoming_threat, f[1].calculate_threat_to_target(battle_map, self.combatant))
        total_threat += max_incoming_threat / 3  # Heuristic to account for the fact it doesn't give resistance to all dmg types
        return total_threat * ROUND_HORIZON


class Rage(Actoid, CombatantEffect, LimitedDurationEffect, ThreatModifier):

    def __init__(self, combatant, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, turns=10)
        self.actoid_flags |= ActoidFlags.IS_POSITIONING_INDEPENDENT
        self.rage_bonus = RageFactory.get_rage_bonus(combatant.level)
        self.factory = factory

    def __str__(self):
        return f"Rage of {self.factory.combatant}"

    def activate(self):
        logger.info(f"{self.combatants[0]} enters into a rage")
        self.combatants[0].ability_dmg_bonus += self.rage_bonus
        self.combatants[0].resistances.update([DamageType.Slashing, DamageType.Bludgeoning, DamageType.Piercing])

    def deactivate(self):
        logger.info(f"{self.combatants[0]}'s rage fades")
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
        if not potential_targets:
            return 0
        # This doesn't take different attack ranges into account
        # TODO This could be moved to the mod threat calculation of the attack factory which should be called here for all the attacks
        attacks = get_attacks(combatant)
        for attack in attacks:
            dmg_acc = reduce(lambda acc, pt: acc + attack.calculate_threat_to_target_mod(battle_map, pt, {"dmg_bonus_flat": rage_bonus}), potential_targets)
            dmg_acc /= len(potential_targets)
            max_threat = max(dmg_acc, max_threat)

        total_threat += max_threat
        total_threat += (combatant.curr_hp / 2)
        # TODO consider improving this by looping over enemy direct dmg dealing abilities
        return total_threat * ROUND_HORIZON

    def get_eligible_coords(self, battle_map, shortest_paths):
        pass  # Due to IS_POSITIONING_INDEPENDENT

    def is_current_coord_eligible(self, battle_map):
        return True