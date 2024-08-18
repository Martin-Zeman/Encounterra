#include "goblin.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  Goblin::Goblin(int num) : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, concatName(std::string(_className), num), 7, 15, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    _size = Size::SMALL;
  }
}