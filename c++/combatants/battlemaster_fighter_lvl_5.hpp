#pragma once

#include "core/combatant.hpp"
#include <string_view>

namespace enc
{
  class BattlemasterFighterLvl5 : public Combatant
  {
  public:
    BattlemasterFighterLvl5(int num);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Battlemaster Fighter LVL 5";
    static constexpr int _classLevel = 5;
    static constexpr int _classId = Combatant::generateClassId(_className, Fighter::BATTLE_MASTER, _classLevel);
  };
}