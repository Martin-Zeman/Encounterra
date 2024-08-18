#include "wild_heart_barbarian_lvl_3.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  WildHeartBarbarianLvl3::WildHeartBarbarianLvl3(int num)
      : Combatant(CombatantType::BARBARIAN, Barbarian::PATH_OF_WILD_HEART, _classLevel, concatName(std::string(_className), num), 35, 14, 1, 0, 30,
                  13)
  {
    _instanceId = generateInstanceId();
  }
}