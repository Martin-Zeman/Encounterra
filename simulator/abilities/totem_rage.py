from simulator.misc import DamageType
from simulator.actoid import Actoid


class TotemRage(Actoid):

    def __init__(self, combatant):
        # Ability.__init__(self, "Rage", combatant, uses, Ability.ActionClasses.BONUS_ACTION)
        Actoid.__init__(self, type=Actoid.Type.IS_TOGGLE_ABILITY)
        self.combatant = combatant
        self.rage_bonus = combatant.rage_bonus

    # def activate(self):
    #     if not self.is_active() and self.has_uses():
    #         self.active = True
    #         self.actor.ability_dmg_bonus = self.actor.ability_dmg_bonus + self.rage_bonus)
    #         self.actor.resistances = [DamageType.Slashing, DamageType.Bludgeoning, DamageType.Fire, DamageType.Lightning,
    #                                       DamageType.Acid, DamageType.Cold, DamageType.Force, DamageType.Necrotic, DamageType.Piercing,
    #                                       DamageType.Poison, DamageType.Radiant]
    #         self.curr_uses -= 1
    #         return True
    #     return False
    #
    # def deactivate(self):
    #     if self.is_active():
    #         self.active = False
    #         self.actor.set_ability_dmg_bonus(self.actor.ability_dmg_bonus - self.rage_bonus)
    #         self.actor.resistances.remove(DamageType.Slashing)
    #         self.actor.resistances.remove(DamageType.Bludgeoning)
    #         self.actor.resistances.remove(DamageType.Fire)
    #         self.actor.resistances.remove(DamageType.Lightning)
    #         self.actor.resistances.remove(DamageType.Acid)
    #         self.actor.resistances.remove(DamageType.Cold)
    #         self.actor.resistances.remove(DamageType.Force)
    #         self.actor.resistances.remove(DamageType.Necrotic)
    #         self.actor.resistances.remove(DamageType.Piercing)
    #         self.actor.resistances.remove(DamageType.Poison)
    #         self.actor.resistances.remove(DamageType.Radiant)
    #
    # def reset(self):
    #     self.deactivate()
    #     self.curr_uses = self.max_uses
