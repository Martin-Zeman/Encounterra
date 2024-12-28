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

  GiantSpider::GiantSpider(const std::string &name) : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, name, 27, 16, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
  }

  ResourceState GiantSpider::exportResources()
  {
    // TODO
    return {};
  }
  void GiantSpider::importResources(const ResourceState &resources)
  {
    // TODO
  }
}
