#include "acolyte.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"
#include "actions/action_types.hpp"

namespace enc
{

  Acolyte::Acolyte(int num)
      : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, concatName(std::string(_className), num), 9, 10, 0, 4, 30, 12)
  {
    _instanceId = generateInstanceId();

    addAbility(AbilityType::MELEE_ATTACK, "Club", this,
               2,                        // toHit
               std::vector<Die>{{1, 4}}, // dmgDice
               0,                        // dmgBonus
               DamageType::Bludgeoning,
               1 // attackRange
    );
    addAbility(AbilityType::SPELLSLOTS, CombatantType::CLERIC, 2);
  }
}