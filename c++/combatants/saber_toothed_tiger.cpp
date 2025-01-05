#include "combatants/saber_toothed_tiger.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  // TODO
  SaberToothedTiger::SaberToothedTiger(int num) : SaberToothedTiger(concatName(std::string(_className), num)) {}

  SaberToothedTiger::SaberToothedTiger(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, name, 27, 16, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
  }

  ResourceState SaberToothedTiger::exportResources()
  {
    // TODO
    return {};
  }
  void SaberToothedTiger::importResources(const ResourceState &resources)
  {
    // TODO
  }
}
