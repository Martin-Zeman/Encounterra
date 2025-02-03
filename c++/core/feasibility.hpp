#pragma once

#include "core/interfaces.hpp"

namespace enc
{
  class Combatant;
  bool checkFeasibility(const Combatant &combatant, Actoid &actoid);

  bool checkFeasibilityLight(const Combatant &combatant, ActoidFactory &actoidFactory);

  std::vector<ActoidFactory *> getFeasibleFactories(const std::vector<ActoidFactory *> &factories, const Combatant &combatant);
}
