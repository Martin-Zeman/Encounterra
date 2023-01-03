from simulator.misc import DamageType
from simulator.actoid import Actoid
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.actions import BonusAction
import logging

logger = logging.getLogger(__name__)


class TotemRage(Actoid, CombatantEffect, LimitedDurationEffect):

    def __init__(self, combatant):
        Actoid.__init__(self, actoid_type=Actoid.Type.IS_TOGGLE_ABILITY, action_type=BonusAction.TOTEM_RAGE)
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, rounds=10)
        self.rage_bonus = combatant.rage_bonus

    def activate(self):
        self.combatants[0].ability_dmg_bonus += self.rage_bonus
        self.combatants[0].resistances.update(
            [DamageType.Slashing, DamageType.Bludgeoning, DamageType.Fire, DamageType.Lightning, DamageType.Acid, DamageType.Cold,
             DamageType.Force, DamageType.Necrotic, DamageType.Poison, DamageType.Radiant, DamageType.Piercing])
        self.combatants[0].rage_active = True

    def deactivate(self):
        self.combatants[0].rage_active = False
        self.combatants[0].ability_dmg_bonus -= self.rage_bonus
        try:
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
        except KeyError:
            logger.error("FIXME Toten Rage Deactivate")
