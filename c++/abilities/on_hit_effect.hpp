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
    hit(const std::shared_ptr<Combatant>& attacker, Actoid *attack, const std::shared_ptr<Combatant>& target, double multiplier, double dmgSoFar) = 0;
    virtual double calculateThreat(const std::shared_ptr<Combatant>& attacker, const std::shared_ptr<Combatant>& target) = 0;
    virtual std::unique_ptr<OnHit> clone() const = 0;
  };
}