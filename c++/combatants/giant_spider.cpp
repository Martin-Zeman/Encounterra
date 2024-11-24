#include "combatants/giant_spider.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
    // TODO
  GiantSpider::GiantSpider(int num)
      : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, concatName(std::string(_className), num), 27, 16, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
  }
}
