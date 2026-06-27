#pragma once

#include "core/combatant.hpp"
#include <string_view>

namespace enc
{
  class PaladinLvl1 : public Combatant
  {
  public:
    PaladinLvl1(int num);
    PaladinLvl1(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Paladin LVL 1";
    static constexpr int _classLevel = 1;
    static constexpr int _classId = Combatant::generateClassId(_className, Paladin::BEFORE_SUBCLASS, _classLevel);
  };
}
