#pragma once

#include "core/interfaces.hpp"

namespace enc
{
  class Combatant;
  bool checkFeasibility(Combatant *combatant, Actoid &actoid);

  bool checkFeasibilityLight(Combatant *combatant, ActoidFactory &actoidFactory);

  std::vector<std::shared_ptr<ActoidFactory>>
  getFeasibleFactories(const std::vector<std::shared_ptr<ActoidFactory>> &factories, Combatant *combatant);
}
