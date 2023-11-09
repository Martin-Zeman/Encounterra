from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..battle_map import Map
from ..effects.effect import EffectType
from ..misc import DamageType, get_attacks, Conditions
from ..actions.actoid import Actoid, FactoryFlags
from ..effects.combatant_effect import CombatantEffect
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..actions.action_types import BonusAction
from ..misc import ROUND_HORIZON
from ..abilities.rage import RageFactory
from ..threat_interfaces import ThreatModifierFactory, AttackThreatModifier
import logging
from ..utils.roll_types import ThreatModifierType

logger = logging.getLogger("Encounterra")

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


    def get_ability_name(self):
        return "Totem Rage"


    def create(self, target):
        # Doesn't make much sense here
        return TotemRage(target, self)

    def create_all(self):
        return [TotemRage(self.combatant, self)]

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


class TotemRage(Actoid, CombatantEffect, LimitedDurationEffect, AttackThreatModifier):

    def __init__(self, combatant, factory):
        CombatantEffect.__init__(self, combatant, combatants=[combatant])
        LimitedDurationEffect.__init__(self, combatant, turns=10)
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

    def calculate_threat(self, **kwargs):
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
            ret = attack.calculate_threat_delta({ThreatModifierType.DMG_BONUS_FLAT: rage_bonus})
            return ret
        return 0

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if not self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)
        return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]

