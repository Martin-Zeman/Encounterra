from simulator.ability import Ability
from simulator.misc import DamageType
from simulator.actoid import Actoid
from simulator.action import Action

class Rage(Ability, Actoid):

    def __init__(self, combatant, uses, rage_bonus):
        Ability.__init__(self, "Rage", combatant, uses, Action.ActionClasses.BONUS_ACTION)
        Actoid.__init__(self, type=Actoid.Type.IS_TOGGLE_ABILITY)
        self.rage_bonus = rage_bonus

    def activate(self):
        if not self.is_active() and self.has_uses():
            self.active = True
            self.combatant.set_ability_dmg_bonus(self.combatant.get_ability_dmg_bonus() + self.rage_bonus)
            self.combatant.resistances = [DamageType.Slashing, DamageType.Bludgeoning, DamageType.Piercing]
            self.curr_uses -= 1
            return True
        return False

    def deactivate(self):
        if self.is_active():
            self.active = False
            self.combatant.set_ability_dmg_bonus(self.combatant.get_ability_dmg_bonus() - self.rage_bonus)
            self.combatant.resistances.remove(DamageType.Slashing)
            self.combatant.resistances.remove(DamageType.Bludgeoning)
            self.combatant.resistances.remove(DamageType.Piercing)

    def reset(self):
        self.deactivate()
        self.curr_uses = self.max_uses