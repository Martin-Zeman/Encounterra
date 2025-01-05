#include "giant_toad.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  GiantToad::GiantToad(int num) : GiantToad(concatName(std::string(_className), num)) {}

  GiantToad::GiantToad(const std::string &name) : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, name, 56, 11, -1, 0, 40, 0)
  {
    _instanceId = generateInstanceId();
  }

  ResourceState GiantToad::exportResources()
  {
    // TODO
    return {};
  }
  void GiantToad::importResources(const ResourceState &resources)
  {
    // TODO
  }
}