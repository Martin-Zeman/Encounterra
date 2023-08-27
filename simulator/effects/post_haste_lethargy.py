from ..effects.combatant_effect import CombatantEffect
from ..effects.effect import EffectType
from ..effects.limited_duration_effect import LimitedDurationEffect

class PostHasteLethargy(CombatantEffect, LimitedDurationEffect):
    def __init__(self, combatant):
        CombatantEffect.__init__(self, combatants=[combatant])
        LimitedDurationEffect.__init__(self, turns=1)

    def get_effect_type(self):
        return EffectType.POST_HASTE_LETHARGY

    def activate(self):
        pass

    def deactivate(self):
        pass