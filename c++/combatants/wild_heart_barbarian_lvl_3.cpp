#include "combatants/wild_heart_barbarian_lvl_3.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  WildHeartBarbarianLvl3::WildHeartBarbarianLvl3(int num)
      : Combatant(CombatantType::BARBARIAN, Barbarian::PATH_OF_WILD_HEART, _classLevel, concatName(std::string(_className), num), 35, 14, 1, 0, 30,
                  13)
  {
    _instanceId = generateInstanceId();

    addMeleeAttack("Two-handed axe", this,
                   5,                         // toHit
                   std::vector<Die>{{1, 12}}, // dmgDice
                   3,                         // dmgBonus
                   DamageType::Slashing,
                   1 // attackRange
    );
    addReactionAttack("Two-handed axe", this,
                      5,                         // toHit
                      std::vector<Die>{{1, 12}}, // dmgDice
                      3,                         // dmgBonus
                      DamageType::Slashing,
                      1 // attackRange
    );
  }

  WildHeartBarbarianLvl3::WildHeartBarbarianLvl3(const std::string &name)
      : Combatant(CombatantType::BARBARIAN, Barbarian::PATH_OF_WILD_HEART, _classLevel, name, 35, 14, 1, 0, 30, 13)
  {
    _instanceId = generateInstanceId();

    addMeleeAttack("Two-handed axe", this,
                   5,                         // toHit
                   std::vector<Die>{{1, 12}}, // dmgDice
                   3,                         // dmgBonus
                   DamageType::Slashing,
                   1 // attackRange
    );
    addReactionAttack("Two-handed axe", this,
                      5,                         // toHit
                      std::vector<Die>{{1, 12}}, // dmgDice
                      3,                         // dmgBonus
                      DamageType::Slashing,
                      1 // attackRange
    );
  }
}