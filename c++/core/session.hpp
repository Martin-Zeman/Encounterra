#pragma once

#include <vector>
#include <string>
#include <set>
#include <stdexcept>
#include "combatant.hpp"
#include "resources.hpp"
#include "types.hpp"
#include "teams.hpp"

namespace enc
{
  class Session
  {
  public:
    Session();
    template <typename CombatantType> void addCombatant(Color teamColor, float resourceDepletionLevel);

    void generateUniqueShortCodes();

  private:
    std::vector<std::unique_ptr<Combatant>> _combatants;
    Teams &_teams;

    // Map to store factory functions for each combatant type
    std::unordered_map<int, std::function<std::unique_ptr<Combatant>(int)>> _combatantFactories;

    // Helper function to register combatant types
    template <typename CombatantType> void registerCombatantType();
  };

}