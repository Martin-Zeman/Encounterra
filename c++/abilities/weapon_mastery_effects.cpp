#include "abilities/weapon_mastery_effects.hpp"

#include <algorithm>

#include "core/combatant.hpp"

namespace enc
{
  void SlowedEffect::activate(const Kwargs &kwargs)
  {
    if(_applied || _combatants.empty())
      {
        return;
      }
    Combatant *target = _combatants[0];
    int newSpeed = std::max(0, target->getSpeed() - SPEED_REDUCTION);
    target->setSpeed(newSpeed);
    if(target->getMovement() > newSpeed)
      {
        target->setMovement(newSpeed);
      }
    _applied = true;
  }

  void SlowedEffect::deactivate()
  {
    if(!_applied || _combatants.empty())
      {
        return;
      }
    Combatant *target = _combatants[0];
    target->setSpeed(target->getSpeed() + SPEED_REDUCTION);
    _applied = false;
  }
}
