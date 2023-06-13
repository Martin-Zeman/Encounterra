from simulator.effects.combatant_effect import CombatantEffect
from simulator.effects.effect import EffectType
from simulator.effects.limited_duration_effect import LimitedDurationEffect

class PostHasteLethargy(CombatantEffect, LimitedDurationEffect):
    def __init__(self, combatant):
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, turns=1)

    def get_effect_type(self):
        return EffectType.POST_HASTE_LETHARGY

    def activate(self, battle_map):
        pass

    def deactivate(self, battle_map):
        pass