#include "bugbear.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  Bugbear::Bugbear(int num)
      : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, concatName(std::string(_className), num), 27, 16, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();

    addMeleeAttack("Morningstar", this,
                   4,                        // toHit
                   std::vector<Die>{{2, 8}}, // dmgDice
                   2,                        // dmgBonus
                   DamageType::Piercing,
                   1 // attackRange
    );
    addReactionAttack("Morningstar", this,
                      4,                        // toHit
                      std::vector<Die>{{2, 8}}, // dmgDice
                      2,                        // dmgBonus
                      DamageType::Piercing,
                      1 // attackRange
    );
  }

  Bugbear::Bugbear(const std::string &name) : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, name, 27, 16, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();

    addMeleeAttack("Morningstar", this,
                   4,                        // toHit
                   std::vector<Die>{{2, 8}}, // dmgDice
                   2,                        // dmgBonus
                   DamageType::Piercing,
                   1 // attackRange
    );
    addReactionAttack("Morningstar", this,
                      4,                        // toHit
                      std::vector<Die>{{2, 8}}, // dmgDice
                      2,                        // dmgBonus
                      DamageType::Piercing,
                      1 // attackRange
    );
  }
}