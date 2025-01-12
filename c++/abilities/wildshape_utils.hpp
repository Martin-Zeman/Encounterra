#pragma once

#include "abilities/wildshape.hpp"
#include "actions/action_types.hpp"
#include <vector>
#include <memory>
#include <functional>

namespace enc
{
  using CombatantFactory = std::function<std::unique_ptr<Combatant>(const std::string &)>;

  std::vector<CombatantFactory> getAvailableWildshapeForms(int level, AbilityType actionType);

  std::vector<std::shared_ptr<Wildshape>> preallocateWildshapeForms(const std::shared_ptr<Combatant>& combatant, AbilityType actionType, WildshapeFactory &factory);

} // namespace enc
