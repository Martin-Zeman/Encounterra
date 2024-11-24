#include "combatants/saber_toothed_tiger.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
    // TODO
  SaberToothedTiger::SaberToothedTiger(int num)
      : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, concatName(std::string(_className), num), 27, 16, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
  }
}
