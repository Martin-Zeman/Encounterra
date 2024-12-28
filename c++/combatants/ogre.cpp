#include "combatants/ogre.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  Ogre::Ogre(int num) : Combatant(CombatantType::MONSTER, Monster::GIANT, _classLevel, concatName(std::string(_className), num), 59, 11, -1, 0, 40, 0)
  {
    _instanceId = generateInstanceId();
    _size = Size::LARGE;
  }

  Ogre::Ogre(const std::string &name) : Combatant(CombatantType::MONSTER, Monster::GIANT, _classLevel, name, 59, 11, -1, 0, 40, 0)
  {
    _instanceId = generateInstanceId();
    _size = Size::LARGE;
  }
}