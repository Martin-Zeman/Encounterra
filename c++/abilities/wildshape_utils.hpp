#pragma once

#include "abilities/wildshape.hpp"
#include "actions/action_types.hpp"
#include <vector>
#include <memory>
#include <functional>

namespace enc
{
  using CombatantFactory = std::function<Combatant *(const std::string &)>;

  std::vector<CombatantFactory> getAvailableWildshapeForms(int level, AbilityType actionType);

  std::vector<Wildshape *> preallocateWildshapeForms(Combatant *combatant, AbilityType actionType, WildshapeFactory &factory);

} // namespace enc
