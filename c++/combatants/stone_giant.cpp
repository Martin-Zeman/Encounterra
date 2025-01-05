#include "combatants/stone_giant.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  StoneGiant::StoneGiant(int num) : StoneGiant(concatName(std::string(_className), num)) {}

  StoneGiant::StoneGiant(const std::string &name) : Combatant(CombatantType::MONSTER, Monster::GIANT, _classLevel, name, 126, 17, 2, 0, 40, 17)
  {
    _instanceId = generateInstanceId();
    _size = Size::HUGE;
  }

  ResourceState StoneGiant::exportResources()
  {
    // TODO
    return {};
  }
  void StoneGiant::importResources(const ResourceState &resources)
  {
    // TODO
  }
}