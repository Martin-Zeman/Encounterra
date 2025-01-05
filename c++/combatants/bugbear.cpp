#include "bugbear.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  Bugbear::Bugbear(int num) : Bugbear(concatName(std::string(_className), num)) {}

  Bugbear::Bugbear(const std::string &name) : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, name, 27, 16, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
  }

  ResourceState Bugbear::exportResources()
  {
    // TODO
    return {};
  }
  void Bugbear::importResources(const ResourceState &resources)
  {
    // TODO
  }
}