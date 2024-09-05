#include "goblin.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"
#include "actions/action_types.hpp"

namespace enc
{

  Goblin::Goblin(int num)
      : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, concatName(std::string(_className), num), 7, 15, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    _size = Size::SMALL;

    addAbility(AbilityType::MELEE_ATTACK, "Scimitar",
               2,                        // toHit
               std::vector<Die>{{1, 4}}, // dmgDice
               0,                        // dmgBonus
               DamageType::Bludgeoning,
               1 // attackRange
    );

    auto javelinFactory = addAbility(AbilityType::RANGED_ATTACK, "Javelin",
                                     4,                        // toHit
                                     std::vector<Die>{{1, 6}}, // dmgDice
                                     2,                        // dmgBonus
                                     DamageType::Piercing,
                                     24,                                  // attackRange
                                     1,                                   // critRange
                                     Uses(1, ResourceRefreshType::NEVER), // ammo
                                     nullptr,                             // onHit
                                     std::vector<DmgDieWithType>{},       // extraDmg
                                     false                                // usesDex
    );
  }
}