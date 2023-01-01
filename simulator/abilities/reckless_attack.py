from simulator.actoid import Actoid
from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect

class RecklessAttack(Actoid, CombatantEffect, LimitedDurationEffect):
    def __init__(self, combatant):
        Actoid.__init__(self, type=Actoid.Type.IS_TOGGLE_ABILITY)
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, rounds=1)

    def activate(self):
        self.combatants[0].reckless_attack_active = True

    def deactivate(self):
        self.combatants[0].reckless_attack_active = False
