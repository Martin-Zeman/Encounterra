#pragma once

#include "core/combatant.hpp"
#include <string_view>

namespace enc
{
  class PaladinLvl2 : public Combatant
  {
  public:
    PaladinLvl2(int num);
    PaladinLvl2(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Paladin LVL 2";
    static constexpr int _classLevel = 2;
    static constexpr int _classId = Combatant::generateClassId(_className, Paladin::BEFORE_SUBCLASS, _classLevel);
  };
}
