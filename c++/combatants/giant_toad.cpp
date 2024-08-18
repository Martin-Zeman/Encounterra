#include "giant_toad.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  GiantToad::GiantToad(int num)
      : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, concatName(std::string(_className), num), 56, 11, -1, 0, 40, 0)
  {
    _instanceId = generateInstanceId();
  }
}