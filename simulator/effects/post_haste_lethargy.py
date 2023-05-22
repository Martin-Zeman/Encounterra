from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.limited_duration_effect import LimitedDurationEffect

class PostHasteLethargy(CombatantEffect, LimitedDurationEffect):
    def __init__(self, combatant):
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, turns=1)

    def activate(self, battle_map):
        pass

    def deactivate(self, battle_map):
        pass