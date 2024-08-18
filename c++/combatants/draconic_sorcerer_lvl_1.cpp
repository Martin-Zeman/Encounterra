#include "draconic_sorcerer_lvl_1.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  DraconicSorcererLvl1::DraconicSorcererLvl1(int num)
      : Combatant(CombatantType::SORCERER, Sorcerer::BEFORE_SUBCLASS, _classLevel, concatName(std::string(_className), num), 7, 15, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
  }
}