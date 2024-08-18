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
    template <typename CombatantType> void addCombatant(Color teamColor, ResourceDepletionLevel resourceDepletionLevel);

  private:
    void generateUniqueShortCodes()
    {
      std::set<std::string> usedCodes;

      for(auto &combatant : _combatants)
        {
          char letter = 'A';
          int number = 1;

          while(true)
            {
              std::string shortCode = std::string(1, letter) + std::to_string(number);

              if(usedCodes.find(shortCode) == usedCodes.end())
                {
                  combatant->setShortCode(std::move(shortCode));
                  usedCodes.insert(shortCode);
                  break;
                }

              // Move to the next combination
              number++;
              if(number > 9)
                {
                  number = 1;
                  letter++;
                  if(letter > 'Z')
                    {
                      throw std::runtime_error("Ran out of unique shortcodes!");
                    }
                }
            }
        }
    }

    std::vector<std::unique_ptr<Combatant>> _combatants;
    Teams &_teams;

    // Map to store factory functions for each combatant type
    std::unordered_map<int, std::function<std::unique_ptr<Combatant>(int)>> _combatantFactories;

    // Helper function to register combatant types
    template <typename CombatantType> void registerCombatantType();
  };

}