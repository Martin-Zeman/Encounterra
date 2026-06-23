#pragma once

#include "core/combatant.hpp"
#include <string_view>

namespace enc
{
  class MoonDruidLvl3 : public Combatant
  {
  public:
    MoonDruidLvl3(int num);
    MoonDruidLvl3(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Circle of the Moon Druid LVL 3";
    static constexpr int _classLevel = 3;
    static constexpr int _classId = Combatant::generateClassId(_className, Druid::CIRCLE_OF_MOON, _classLevel);
  };
}
