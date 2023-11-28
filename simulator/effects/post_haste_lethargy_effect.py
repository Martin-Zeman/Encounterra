from ..effects.combatant_effect import CombatantEffect
from ..effects.effect import EffectType
from ..effects.limited_duration_effect import LimitedDurationEffect

class PostHasteLethargyEffect(CombatantEffect, LimitedDurationEffect):
    def __init__(self, initiator, combatant):
        CombatantEffect.__init__(self, initiator, combatants=[combatant])
        LimitedDurationEffect.__init__(self, initiator, turns=1)

    def get_effect_type(self):
        return EffectType.POST_HASTE_LETHARGY

    def activate(self):
        pass

    def deactivate(self):
        pass