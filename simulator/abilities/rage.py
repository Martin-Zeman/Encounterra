from simulator.misc import DamageType
from simulator.actoid import Actoid


class Rage(Actoid):

    def __init__(self, combatant):
        Actoid.__init__(self, type=Actoid.Type.IS_TOGGLE_ABILITY)
        self.combatant = combatant
        self.rage_bonus = combatant.rage_bonus

    # def activate(self):
    #     if not self.is_active() and self.has_uses():
    #         self.active = True
    #         self.combatant.set_ability_dmg_bonus(self.combatant.ability_dmg_bonus + self.rage_bonus)
    #         self.combatant.resistances = [DamageType.Slashing, DamageType.Bludgeoning, DamageType.Piercing]
    #         return True
    #     return False
    #
    # def deactivate(self):
    #     if self.is_active():
    #         self.active = False
    #         self.combatant.set_ability_dmg_bonus(self.combatant.ability_dmg_bonus - self.rage_bonus)
    #         self.combatant.resistances.remove(DamageType.Slashing)
    #         self.combatant.resistances.remove(DamageType.Bludgeoning)
    #         self.combatant.resistances.remove(DamageType.Piercing)
    #
    # def reset(self):
    #     self.deactivate()
    #     self.curr_uses = self.max_uses
