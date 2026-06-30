#pragma once

#include "core/combatant.hpp"

namespace enc
{

  // Level 3 Warlock of the Archfey. Pact slots become 2nd level (every spell upcasts to that level). Gains the
  // Archfey subclass features: Steps of the Fey (free Misty Step several times per day) and the always-prepared
  // Faerie Fire / Sleep / Misty Step spells. Picks Darkness as its chosen leveled spell.
  class WarlockLvl3 : public Combatant
  {
  public:
    WarlockLvl3(int num);
    WarlockLvl3(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Warlock LVL 3";
    static constexpr int _classLevel = 3;
    static constexpr int _classId = Combatant::generateClassId(_className, Warlock::ARCHFEY_PATRON, _classLevel);
  };

}
