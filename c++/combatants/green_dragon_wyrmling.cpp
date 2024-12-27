#include "green_dragon_wyrmling.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  GreenDragonWyrmling::GreenDragonWyrmling(int num)
      : Combatant(CombatantType::MONSTER, Monster::DRAGON, _classLevel, concatName(std::string(_className), num), 38, 17, 1, 0, 60, 0)
  {
    _instanceId = generateInstanceId();
  }

  GreenDragonWyrmling::GreenDragonWyrmling(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::DRAGON, _classLevel, name, 38, 17, 1, 0, 60, 0)
  {
    _instanceId = generateInstanceId();
  }
}