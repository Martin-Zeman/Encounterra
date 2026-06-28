#pragma once

#include "core/combatant.hpp"

namespace enc
{
  class ClericLvl1 : public Combatant
  {
  public:
    ClericLvl1(int num);
    ClericLvl1(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Cleric LVL 1";
    static constexpr int _classLevel = 1;
    static constexpr int _classId = Combatant::generateClassId(_className, Cleric::BEFORE_SUBCLASS, _classLevel);
  };
}
