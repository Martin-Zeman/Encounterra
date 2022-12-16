from simulator.ability import Ability
from simulator.misc import DamageType

class Rage(Ability):

    def __init__(self, character, uses, rage_bonus):
        super().__init__("Rage", character, uses, "bonus_action")
        self.rage_bonus = rage_bonus

    def activate(self):
        if not self.is_active() and self.has_uses():
            self.active = True
            self.character.set_ability_dmg_bonus(self.character.get_ability_dmg_bonus() + self.rage_bonus)
            self.character.resistances = [DamageType.Slashing, DamageType.Bludgeoning]
            self.curr_uses -= 1
            return True
        return False

    def deactivate(self):
        if self.is_active():
            self.active = False
            self.character.set_ability_dmg_bonus(self.character.get_ability_dmg_bonus() - self.rage_bonus)
            self.character.resistances.remove(DamageType.Slashing)
            self.character.resistances.remove(DamageType.Bludgeoning)

    def reset(self):
        self.deactivate()
        self.curr_uses = self.max_uses