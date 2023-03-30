from simulator.effects.effect import Effect


class CombatantEffect(Effect):

    def __init__(self, combatants):
        self.combatants = combatants

    def is_affecting(self, combatant, battle_map):
        return combatant in self.combatants
