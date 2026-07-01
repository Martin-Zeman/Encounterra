#pragma once

#include "core/combatant.hpp"

namespace enc
{
  class AssassinRogueLvl5 : public Combatant
  {
  public:
    AssassinRogueLvl5(int num);
    AssassinRogueLvl5(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Assassin Rogue 5th LVL";
    static constexpr int _classLevel = 5;
    static constexpr int _classId = Combatant::generateClassId(_className, Rogue::ASSASSIN, _classLevel);
  };
}
