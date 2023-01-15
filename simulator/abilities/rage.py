from simulator.misc import DamageType
from simulator.actoid import Actoid
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.action_types import BonusAction


class Rage(Actoid, CombatantEffect, LimitedDurationEffect):

    def __init__(self, combatant):
        Actoid.__init__(self, actoid_type=Actoid.Type.IS_TOGGLE_ABILITY, action_type=BonusAction.RAGE)
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, rounds=10)
        self.rage_bonus = combatant.rage_bonus

    def activate(self):
        self.combatants[0].ability_dmg_bonus += self.rage_bonus
        self.combatants[0].resistances.update([DamageType.Slashing, DamageType.Bludgeoning, DamageType.Piercing])

    def deactivate(self):
        self.combatants[0].ability_dmg_bonus -= self.rage_bonus
        self.combatants[0].resistances.remove(DamageType.Slashing)
        self.combatants[0].resistances.remove(DamageType.Bludgeoning)
        self.combatants[0].resistances.remove(DamageType.Piercing)
