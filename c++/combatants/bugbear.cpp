#include "bugbear.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  Bugbear::Bugbear(int num)
      : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, concatName(std::string(_className), num), 27, 16, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
  }
}