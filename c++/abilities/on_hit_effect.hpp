#pragma once

#include "core/interfaces.hpp"
#include "core/misc.hpp"

namespace enc
{

  class Combatant;

  class OnHit
  {
  public:
    virtual std::vector<std::pair<int, DamageType>>
    hit(Combatant *attacker, Actoid *attack, Combatant *target, double multiplier, double dmgSoFar) = 0;
    virtual double calculateThreat(Combatant *attacker, Combatant *target) = 0;
    virtual std::unique_ptr<OnHit> clone() const = 0;
  };
}