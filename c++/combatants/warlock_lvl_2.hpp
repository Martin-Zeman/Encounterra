#pragma once

#include "core/combatant.hpp"

namespace enc
{

  // Level 2 Warlock. Still pre-subclass (Fiend placeholder patron). Picks up a second 1st-level Pact slot and
  // two Eldritch Invocations: Agonizing Blast (adds CHA to each Eldritch Blast beam) and Devil's Sight (never
  // Blinded by Darkness). Adds Armor of Agathys to its bonus-action repertoire.
  class WarlockLvl2 : public Combatant
  {
  public:
    WarlockLvl2(int num);
    WarlockLvl2(const std::string &name);

    int getClassId() const override { return _classId; }

    static constexpr int getStaticClassId() { return _classId; }
    static constexpr std::string_view getClassName() { return _className; }

  private:
    static constexpr std::string_view _className = "Warlock LVL 2";
    static constexpr int _classLevel = 2;
    static constexpr int _classId = Combatant::generateClassId(_className, Warlock::FIEND_PATRON, _classLevel);
  };

}
