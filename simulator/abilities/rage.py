from simulator.ability import Ability
from simulator.misc import DamageType

class Rage(Ability):

    def __init__(self, combatant, uses, rage_bonus):
        super().__init__("Rage", combatant, uses, "bonus_action")
        self.rage_bonus = rage_bonus

    def activate(self):
        if not self.is_active() and self.has_uses():
            self.active = True
            self.combatant.set_ability_dmg_bonus(self.combatant.get_ability_dmg_bonus() + self.rage_bonus)
            self.combatant.resistances = [DamageType.Slashing, DamageType.Bludgeoning]
            self.curr_uses -= 1
            return True
        return False

    def deactivate(self):
        if self.is_active():
            self.active = False
            self.combatant.set_ability_dmg_bonus(self.combatant.get_ability_dmg_bonus() - self.rage_bonus)
            self.combatant.resistances.remove(DamageType.Slashing)
            self.combatant.resistances.remove(DamageType.Bludgeoning)

    def reset(self):
        self.deactivate()
        self.curr_uses = self.max_uses