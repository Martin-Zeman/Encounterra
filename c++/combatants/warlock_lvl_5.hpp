#pragma once

#include "core/combatant.hpp"

namespace enc
{

  // Level 5 Warlock of the Archfey. Pact slots become 3rd level (every spell upcasts to that level) and
  // Eldritch Blast fires two beams. Adds the Repelling Blast and Eldritch Mind invocations and the level-3
  // spells Hypnotic Pattern and Blink. Proficiency bonus rises to +3.
  class WarlockLvl5 : public Combatant
  {
  public:
    WarlockLvl5(int num);
    WarlockLvl5(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Warlock LVL 5";
    static constexpr int _classLevel = 5;
    static constexpr int _classId = Combatant::generateClassId(_className, Warlock::ARCHFEY_PATRON, _classLevel);
  };

}
