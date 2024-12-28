#include "combatants/dire_wolf.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  // TODO
  DireWolf::DireWolf(int num)
      : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, concatName(std::string(_className), num), 27, 16, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
  }
  DireWolf::DireWolf(const std::string &name) : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, name, 27, 16, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
  }

  ResourceState DireWolf::exportResources()
  {
    // TODO
    return {};
  }
  void DireWolf::importResources(const ResourceState &resources)
  {
    // TODO
  }
}
