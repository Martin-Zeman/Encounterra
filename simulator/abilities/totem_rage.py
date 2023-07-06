from simulator.battle_map import Map
from simulator.effects.effect import EffectType
from simulator.misc import DamageType, get_attacks
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.actions.action_types import BonusAction
from simulator.misc import ROUND_HORIZON
from simulator.abilities.rage import RageFactory
from simulator.threat_interfaces import ThreatModifier, ThreatModifierFactory, AttackThreatModifier
import logging

from simulator.utils.roll_types import ThreatModifierType

logger = logging.getLogger("EncounTroll")

class TotemRageFactory(ThreatModifierFactory):

    def __init__(self, combatant):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_MODIFIER
        self.flags |= FactoryFlags.TARGETS_SELF
        self.combatant = combatant
        self.action_type = BonusAction.TOTEM_RAGE

    def __str__(self):
        """
        Important for FSM building
        """
        return "TotemRageFactory"

    def create(self, target_combatant):
        # Doesn't make much sense here
        return TotemRage(target_combatant, self)

    def create_all(self):
        return [TotemRage(self.combatant, self)]

    def calculate_threat_to_target(self, target, *args, **kwargs):
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
        # Haste factories wouldn't change the result here so we're omitting them
        max_incoming_threat = 0
        for f in target.action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags:
                max_incoming_threat = max(max_incoming_threat, f[1].calculate_threat_to_target(self.combatant))
        total_threat += max_incoming_threat / 2

        max_incoming_threat = 0
        for f in target.bonus_action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags:
                max_incoming_threat = max(max_incoming_threat, f[1].calculate_threat_to_target(self.combatant))
        total_threat += max_incoming_threat / 2
        return total_threat * ROUND_HORIZON


class TotemRage(Actoid, CombatantEffect, LimitedDurationEffect, ThreatModifier, AttackThreatModifier):

    def __init__(self, combatant, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, turns=10)
        self.actoid_flags |= ActoidFlags.IS_POSITIONING_INDEPENDENT
        self.rage_bonus = RageFactory.get_rage_bonus(combatant.level)
        self.factory = factory

    def __str__(self):
        return f"Totem Rage of {self.factory.combatant}"

    def shorthand_str(self):
        return "Totem Rage"

    def get_effect_type(self):
        return EffectType.TOTEM_RAGE

    def activate(self):
        logger.info(f"{self.combatants[0]} enters into a totem rage")
        Map.get().effect_tracker.add(self)
        self.combatants[0].ability_dmg_bonus += self.rage_bonus
        self.combatants[0].resistances.update(
            [DamageType.Slashing, DamageType.Bludgeoning, DamageType.Fire, DamageType.Lightning, DamageType.Acid, DamageType.Cold,
             DamageType.Force, DamageType.Necrotic, DamageType.Poison, DamageType.Radiant, DamageType.Piercing])

    def deactivate(self):
        logger.info(f"{self.combatants[0]}'s rage fades")
        self.combatants[0].ability_dmg_bonus -= self.rage_bonus
        try:
            self.combatants[0].resistances.remove(DamageType.Slashing)
        except KeyError:
            print("FIXME")
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




    def calculate_threat(self, *args, **kwargs):
        """
        Finds the combatant's attack that benefits the most from the dmg increment. Then adds the estimated damage prevention equal to
        all remaining HP (better than regular rage)
        """
        return self.factory.combatant.curr_hp

    def calculate_threat_for_attack(self, combatant, attack, *args, **kwargs):
        """
        Threat estimation generated by the instantiated ability.
        """
        rage_bonus = RageFactory.get_rage_bonus(combatant.level)
        if FactoryFlags.IS_MELEE in attack.factory.flags:
            return attack.calculate_threat_delta({ThreatModifierType.DMG_BONUS_FLAT: rage_bonus})
        return 0


    def get_eligible_coords(self, distances, shortest_paths):
        return Map.get().get_all_accessible_coords(shortest_paths, self.factory.combatant)

    def is_current_coord_eligible(self):
        return True
