#pragma once

#include "core/combatant.hpp"
#include <string_view>

namespace enc
{
  class FighterLvl1 : public Combatant
  {
  public:
    FighterLvl1(int num);
    FighterLvl1(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Fighter LVL 1";
    static constexpr int _classLevel = 1;
    static constexpr int _classId = Combatant::generateClassId(_className, Fighter::BEFORE_SUBCLASS, _classLevel);
  };
}
