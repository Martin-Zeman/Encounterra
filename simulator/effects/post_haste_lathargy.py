from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect

class PostHasteLethargy(CombatantEffect, LimitedDurationEffect):
    def __init__(self, combatant):
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, rounds=1)

    def activate(self):
        pass

    def deactivate(self):
        pass