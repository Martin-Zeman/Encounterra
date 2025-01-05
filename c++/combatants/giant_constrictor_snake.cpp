#include "combatants/giant_constrictor_snake.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  // TODO
  GiantConstrictorSnake::GiantConstrictorSnake(int num) : GiantConstrictorSnake(concatName(std::string(_className), num)) {}

  GiantConstrictorSnake::GiantConstrictorSnake(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, name, 27, 16, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
  }

  ResourceState GiantConstrictorSnake::exportResources()
  {
    // TODO
    return {};
  }
  void GiantConstrictorSnake::importResources(const ResourceState &resources)
  {
    // TODO
  }
}
