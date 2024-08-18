#include "stone_giant.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  StoneGiant::StoneGiant(int num)
      : Combatant(CombatantType::MONSTER, Monster::GIANT, _classLevel, concatName(std::string(_className), num), 126, 17, 2, 0, 40, 17)
  {
    _instanceId = generateInstanceId();
    _size = Size::HUGE;
  }
}