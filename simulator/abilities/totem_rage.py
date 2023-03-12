from simulator.misc import DamageType, get_attacks
from simulator.actions.actoid import Actoid, FactoryFlags, ActoidFlags
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.action_types import BonusAction
from functools import reduce
from simulator.misc import ROUND_HORIZON
from simulator.abilities.rage import RageFactory
from simulator.threat import dmg_increment_for_dmg_flat
from simulator.threat_calculator import ThreatModifier, ThreatModifierFactory
import logging

logger = logging.getLogger(__name__)

class TotemRageFactory(ThreatModifierFactory):

    def __init__(self, combatant):
        super().__init__()
        self.flags |= FactoryFlags.IS_ATTACK_MODIFIER
        self.combatant = combatant
        self.action_type = BonusAction.TOTEM_RAGE

    def create_best(self, combatant, battle_map):
        return TotemRage(combatant, self)

    def create(self, target_combatant):
        return TotemRage(target_combatant, self)

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
        # Haste factories wouldn't change the result here so we're omitting them
        max_incoming_threat = 0
        for f in target.action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags:
                max_incoming_threat = max(max_incoming_threat, f[1].calculate_threat_to_target(battle_map, self.combatant))
        total_threat += max_incoming_threat / 2

        max_incoming_threat = 0
        for f in target.bonus_action_factories:
            if FactoryFlags.IS_DIRECT_THREAT in f[1].flags:
                max_incoming_threat = max(max_incoming_threat, f[1].calculate_threat_to_target(battle_map, self.combatant))
        total_threat += max_incoming_threat / 2
        return total_threat * ROUND_HORIZON

class TotemRage(Actoid, CombatantEffect, LimitedDurationEffect, ThreatModifier):

    def __init__(self, combatant, factory):
        Actoid.__init__(self, actoid_type=ActoidFlags.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, turns=10)
        self.rage_bonus = RageFactory.get_rage_bonus(combatant.level)
        self.factory = factory

    def __str__(self):
        return "TotemRage"

    def activate(self):
        logger.info(f"{self.combatants[0]} enters into a totem rage")
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


    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        """
        Finds the combatant's attack that benefits the most from the dmg increment. Then adds the estimated damage prevention equal to
        all remaining HP (better than regular rage)
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
            dmg_acc = reduce(lambda acc, pt: acc + attack.calculate_threat_to_target_mod(battle_map, pt, {"dmg_bonus_flat": rage_bonus}), potential_targets, 0)
            dmg_acc /= len(potential_targets)
            max_threat = max(dmg_acc, max_threat)

        total_threat += max_threat
        total_threat += combatant.curr_hp
        # TODO consider improving this by looping over enemy direct dmg dealing abilities
        return total_threat * ROUND_HORIZON
