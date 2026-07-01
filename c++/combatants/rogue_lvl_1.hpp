#pragma once

#include "core/combatant.hpp"

namespace enc
{
  class RogueLvl1 : public Combatant
  {
  public:
    RogueLvl1(int num);
    RogueLvl1(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Rogue 1st LVL";
    static constexpr int _classLevel = 1;
    static constexpr int _classId = Combatant::generateClassId(_className, Rogue::BEFORE_SUBCLASS, _classLevel);
  };
}
