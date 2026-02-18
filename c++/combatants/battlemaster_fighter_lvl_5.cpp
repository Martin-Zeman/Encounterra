#include "battlemaster_fighter_lvl_5.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  BattlemasterFighterLvl5::BattlemasterFighterLvl5(int num)
      : Combatant(CombatantType::FIGHTER, Fighter::BATTLE_MASTER, _classLevel, concatName(std::string(_className), num), 46, 17, 0, 0, 30, 15)
  {
    _instanceId = generateInstanceId();
  }

  BattlemasterFighterLvl5::BattlemasterFighterLvl5(const std::string &name)
      : Combatant(CombatantType::FIGHTER, Fighter::BATTLE_MASTER, _classLevel, name, 46, 17, 0, 0, 30, 15)
  {
    _instanceId = generateInstanceId();
  }
}