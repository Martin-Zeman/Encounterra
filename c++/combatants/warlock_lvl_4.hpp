#pragma once

#include "core/combatant.hpp"

namespace enc
{

  // Level 4 Warlock of the Archfey. Takes the level-4 Ability Score Improvement into Charisma (16 -> 18),
  // raising spell attack/save DC by 1 and Agonizing Blast damage by 1. Spell list is otherwise the same as
  // level 3; pact slots remain 2nd level.
  class WarlockLvl4 : public Combatant
  {
  public:
    WarlockLvl4(int num);
    WarlockLvl4(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Warlock LVL 4";
    static constexpr int _classLevel = 4;
    static constexpr int _classId = Combatant::generateClassId(_className, Warlock::ARCHFEY_PATRON, _classLevel);
  };

}
