#pragma once

#include "core/combatant.hpp"

namespace enc
{
  class RogueLvl2 : public Combatant
  {
  public:
    RogueLvl2(int num);
    RogueLvl2(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Rogue 2nd LVL";
    static constexpr int _classLevel = 2;
    static constexpr int _classId = Combatant::generateClassId(_className, Rogue::BEFORE_SUBCLASS, _classLevel);
  };
}
