#pragma once

#include "core/combatant.hpp"

namespace enc
{

  // Level 1 Warlock (Fiend Patron). A Charisma-based pact caster that opens with the Armor of Shadows
  // invocation (Mage Armor at will, assumed already cast going into the fight), hammers foes with Eldritch
  // Blast, and can curse a target with Hex to add 1d6 Necrotic to every hit. Rounds out its kit with the
  // Bane and Charm Person leveled spells and a backup dagger.
  class WarlockLvl1 : public Combatant
  {
  public:
    WarlockLvl1(int num);
    WarlockLvl1(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Warlock LVL 1";
    static constexpr int _classLevel = 1;
    static constexpr int _classId = Combatant::generateClassId(_className, Warlock::FIEND_PATRON, _classLevel);
  };

}
