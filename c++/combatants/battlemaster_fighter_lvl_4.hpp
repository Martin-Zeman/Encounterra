#pragma once

#include "core/combatant.hpp"
#include <string_view>

namespace enc
{
  class BattlemasterFighterLvl4 : public Combatant
  {
  public:
    BattlemasterFighterLvl4(int num);
    BattlemasterFighterLvl4(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Battlemaster Fighter LVL 4";
    static constexpr int _classLevel = 4;
    static constexpr int _classId = Combatant::generateClassId(_className, Fighter::BATTLE_MASTER, _classLevel);
  };
}
