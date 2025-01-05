#include "combatants/brown_bear.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  // TODO
  BrownBear::BrownBear(int num) : BrownBear(concatName(std::string(_className), num)) {}

  BrownBear::BrownBear(const std::string &name) : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, name, 27, 16, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
  }

  ResourceState BrownBear::exportResources()
  {
    // TODO
    return {};
  }
  void BrownBear::importResources(const ResourceState &resources)
  {
    // TODO
  }
}
