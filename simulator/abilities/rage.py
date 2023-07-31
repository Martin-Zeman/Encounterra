from functools import cache
from simulator.battle_map import Map
from simulator.effects.effect import EffectType
from simulator.misc import DamageType, get_attacks
from simulator.actions.actoid import Actoid, FactoryFlags
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.actions.action_types import BonusAction
from simulator.misc import ROUND_HORIZON
import sys
from simulator.threat_interfaces import ThreatModifierFactory, AttackThreatModifier
import logging
from simulator.utils.roll_types import ThreatModifierType

logger = logging.getLogger("Encounterra")

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

    def get_eligible_targets(self):
        pass # No need due to the TARGETS_SELF flag

    def create_all(self):
        return [Rage(self.combatant, self)]

    def create(self, target):
        # Doesn't make much sense here
        return Rage(target, self)

    def calculate_threat_to_target(self, target, **kwargs):
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
            dmg_inc = attack.calculate_threat_to_target_delta(self, {ThreatModifierType.DMG_BONUS_FLAT: rage_bonus})
            max_threat = max(dmg_inc, max_threat)

        total_threat += max_threat
        # Haste factories wouldn't change the result here, so we're omitting them
        max_incoming_threat = 0
        for f in target.action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags:
                max_incoming_threat = max(max_incoming_threat, f[1].calculate_threat_to_target(self.combatant))
        total_threat += max_incoming_threat / 3  # Heuristic to account for the fact it doesn't give resistance to all dmg types

        max_incoming_threat = 0
        for f in target.bonus_action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags:
                max_incoming_threat = max(max_incoming_threat, f[1].calculate_threat_to_target(self.combatant))
        total_threat += max_incoming_threat / 3  # Heuristic to account for the fact it doesn't give resistance to all dmg types
        return total_threat * ROUND_HORIZON


class Rage(Actoid, CombatantEffect, LimitedDurationEffect, AttackThreatModifier):

    def __init__(self, combatant, factory):
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, turns=10)
        self.rage_bonus = RageFactory.get_rage_bonus(combatant.level)
        self.factory = factory

    def __str__(self):
        return f"Rage of {self.factory.combatant}"

    def shorthand_str(self):
        return "Rage"

    def get_effect_type(self):
        return EffectType.RAGE

    def activate(self):
        logger.info(f"{self.combatants[0]} enters into a rage")
        Map.get().effect_tracker.add(self)
        self.combatants[0].ability_dmg_bonus += self.rage_bonus
        self.combatants[0].resistances.update([DamageType.Slashing, DamageType.Bludgeoning, DamageType.Piercing])

    def deactivate(self):
        logger.info(f"{self.combatants[0]}'s rage fades")
        self.combatants[0].ability_dmg_bonus -= self.rage_bonus
        self.combatants[0].resistances.remove(DamageType.Slashing)
        self.combatants[0].resistances.remove(DamageType.Bludgeoning)
        self.combatants[0].resistances.remove(DamageType.Piercing)

    def calculate_threat(self, **kwargs):
        """
        Finds the combatant's attack that benefits the most from the dmg increment. Then adds the estimated damage prevention equal to
        all remaining HP (better than regular rage)
        """
        return self.factory.combatant.curr_hp / 2

    def calculate_threat_for_attack(self, combatant, attack, *args, **kwargs):
        """
        Threat estimation generated by the instantiated ability.
        """
        rage_bonus = RageFactory.get_rage_bonus(combatant.level)
        if FactoryFlags.IS_MELEE in attack.factory.flags:
            return attack.calculate_threat_delta({ThreatModifierType.DMG_BONUS_FLAT: rage_bonus})
        return 0

    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        return battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)

    def is_current_coord_eligible(self):
        return True