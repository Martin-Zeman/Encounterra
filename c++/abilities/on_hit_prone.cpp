#include "abilities/on_hit_prone.hpp"

#include <iostream>
#include "core/combatant.hpp"

namespace enc
{
  std::vector<std::pair<int, DamageType>>
  OnHitProne::hit(Combatant *attacker, Actoid * /*attack*/, Combatant *target, double /*multiplier*/, double /*dmgSoFar*/)
  {
    // Already prone: nothing to do.
    if(target->isAffectedBy(Conditions::PRONE))
      {
        return {};
      }

    if(!_requiresSave)
      {
        // Automatic prone (e.g. 2024 Dire Wolf Bite): no saving throw, but only if the target is small enough.
        if(target->getSize() > _maxSize)
          {
            return {};
          }
        std::cout << target->_name << " is knocked Prone (no save)" << std::endl;
        target->applyCondition(Condition(Conditions::PRONE, attacker, nullptr, target));
        return {};
      }

    bool saved = rollSavingThrow(target->getSavingThrow(_saveType), _dc, RollType::STRAIGHT);
    if(!saved)
      {
        std::cout << target->_name << " is knocked Prone (DC " << _dc << ")" << std::endl;
        target->applyCondition(Condition(Conditions::PRONE, attacker, nullptr, target));
      }
    return {};
  }
}
