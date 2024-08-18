#include "ogre.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  Ogre::Ogre(int num) : Combatant(CombatantType::MONSTER, Monster::GIANT, _classLevel, concatName(std::string(_className), num), 39, 11, 1, 0, 20, 0)
  {
    _instanceId = generateInstanceId();
    _size = Size::LARGE;
  }
}