#pragma once

#include "core/combatant.hpp"

namespace enc
{
  class AssassinRogueLvl4 : public Combatant
  {
  public:
    AssassinRogueLvl4(int num);
    AssassinRogueLvl4(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Assassin Rogue 4th LVL";
    static constexpr int _classLevel = 4;
    static constexpr int _classId = Combatant::generateClassId(_className, Rogue::ASSASSIN, _classLevel);
  };
}
