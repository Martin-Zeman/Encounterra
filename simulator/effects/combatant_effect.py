from ..effects.effect import Effect


class CombatantEffect(Effect):

    def __init__(self, initiator, combatants):
        Effect.__init__(self, initiator)
        self.combatants = combatants

    def is_affecting(self, combatant):
        return combatant in self.combatants
