#include "combatants/moon_druid_lvl_5.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  MoonDruidLvl5::MoonDruidLvl5(int num)
      : Combatant(CombatantType::DRUID, Druid::CIRCLE_OF_MOON, _classLevel, concatName(std::string(_className), num), 43, 13, 1, 7, 35, 15)
  {
    _instanceId = generateInstanceId();
  }

  MoonDruidLvl5::MoonDruidLvl5(const std::string &name)
      : Combatant(CombatantType::DRUID, Druid::CIRCLE_OF_MOON, _classLevel, name, 43, 13, 1, 7, 35, 15)
  {
    _instanceId = generateInstanceId();
  }

  ResourceState MoonDruidLvl5::exportResources()
  {
    // TODO
    return {};
  }
  void MoonDruidLvl5::importResources(const ResourceState &resources)
  {
    // TODO
  }
}