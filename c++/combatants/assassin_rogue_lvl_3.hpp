#pragma once

#include "core/combatant.hpp"

namespace enc
{
  class AssassinRogueLvl3 : public Combatant
  {
  public:
    AssassinRogueLvl3(int num);
    AssassinRogueLvl3(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Assassin Rogue 3rd LVL";
    static constexpr int _classLevel = 3;
    static constexpr int _classId = Combatant::generateClassId(_className, Rogue::ASSASSIN, _classLevel);
  };
}
