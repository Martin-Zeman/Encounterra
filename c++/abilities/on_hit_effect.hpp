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
    hit(const std::shared_ptr<Combatant> &attacker, Actoid *attack, Combatant &target, double multiplier, double dmgSoFar) = 0;
    virtual double calculateThreat(const Combatant &attacker, const Combatant &target) = 0;
    virtual std::unique_ptr<OnHit> clone() const = 0;
  };
}