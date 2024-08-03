#include "core/combatant.hpp"

namespace enc
{

  class Goblin : public Combatant
  {
    Goblin(int num);
    // Goblin(std::string name);
  };

}
// class Goblin(Combatant):

//     name = "Goblin"
//     cls = Class.MONSTER.HUMANOID
//     level = 1
//     id = Combatant.generate_unique_id(name, cls, level)

//     def __init__(self, num_or_name=1):
//         super().__init__(num_or_name, hp=7, ac=15, init_bonus=2, spell_to_hit=0, speed=30, resistances=set(), dc=0)
//         self.scimitar = self.add_ability(Action.MELEE_ATTACK,  name="Scimitar", combatant=self, to_hit=4, dmg_dice=[(1, 6)], dmg_bonus=2,
//         dmg_type=DamageType.Slashing, attack_range=1, crit_range=1, uses_dex=True) self.shortbow = self.add_ability(Action.RANGED_ATTACK,
//         name="Shortbow", combatant=self, to_hit=4, dmg_dice=[(1, 6)], dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=64, crit_range=1)
//         self.nimble_disengage = self.add_ability(BonusAction.CUNNING_DISENGAGE)
//         self.add_ability(Reaction.REACTION_ATTACK,  name="Scimitar", combatant=self, to_hit=4, dmg_dice=[(1, 6)], dmg_bonus=2,
//         dmg_type=DamageType.Slashing, attack_range=1, crit_range=1) self.danger_zone_attack = self.shortbow self.build_attack_fms()
//         self.saving_throws[SavingThrow.STR] = -1
//         self.saving_throws[SavingThrow.DEX] = 2
//         self.saving_throws[SavingThrow.CON] = 0
//         self.saving_throws[SavingThrow.INT] = 0
//         self.saving_throws[SavingThrow.WIS] = -1
//         self.saving_throws[SavingThrow.CHA] = -1
//         self.athletics = -1
//         self.acrobatics = 2
//         self.passive_perception = 9