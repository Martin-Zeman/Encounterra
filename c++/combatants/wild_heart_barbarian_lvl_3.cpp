#include "combatants/wild_heart_barbarian_lvl_3.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  WildHeartBarbarianLvl3::WildHeartBarbarianLvl3(int num) : WildHeartBarbarianLvl3(concatName(std::string(_className), num)) {}

  WildHeartBarbarianLvl3::WildHeartBarbarianLvl3(const std::string &name)
      : Combatant(CombatantType::BARBARIAN, Barbarian::PATH_OF_WILD_HEART, _classLevel, name, 35, 14, 1, 0, 30, 13)
  {
    _instanceId = generateInstanceId();
  }

  ResourceState WildHeartBarbarianLvl3::exportResources()
  {
    // TODO
    return {};
  }
  void WildHeartBarbarianLvl3::importResources(const ResourceState &resources)
  {
    // TODO
  }
}