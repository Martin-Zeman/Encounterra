#pragma once

#include <vector>
#include <string>
#include <set>
#include <stdexcept>
#include <cctype>
#include <algorithm>
#include <regex>
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
    template <typename CombatantType> void addCombatant(Color teamColor, ResourceDepletionLevel resourceDepletionLevel = ResourceDepletionLevel::FULLY_RESTED);
    template <typename CombatantType> void addCombatant(CombatantType* combatant, Color teamColor, ResourceDepletionLevel resourceDepletionLevel = ResourceDepletionLevel::FULLY_RESTED);  // For testing purposes

  private:
    void generateUniqueShortCodes()
    {
      std::set<std::string> usedCodes;

      for(auto &combatant : _combatants)
        {
          int classId = combatant->getClassId();
          std::string name = combatant->_name;

          // Extract the number from the end of the name (in parentheses)
          std::regex number_regex(R"(\((\d+)\)$)");
          std::smatch match;
          if(!std::regex_search(name, match, number_regex))
            {
              throw std::runtime_error("Invalid name format: " + name);
            }
          int number = std::stoi(match[1]);
          if(number < 0 || number > 9)
            {
              throw std::runtime_error("Invalid number in name: " + name);
            }

          // Remove the number and parentheses from the name
          std::string nameWithoutNumber = name.substr(0, name.find_last_of('(') - 1);

          // Extract first letters of words and additional letters if needed
          std::string initials;
          for(char c : nameWithoutNumber)
            {
              if(std::isalpha(c))
                {
                  initials += std::toupper(c);
                  if(initials.length() == 2)
                    break;
                }
            }

          // If we still don't have 2 letters, add 'A's
          while(initials.length() < 2)
            {
              initials += 'A';
            }

          // Generate shortcode
          std::string shortCode;
          char secondLetter = initials[1];
          do
            {
              shortCode = initials[0] + std::string(1, secondLetter) + std::to_string(number);
              secondLetter++;
              if(secondLetter > 'Z')
                secondLetter = 'A';
          } while(usedCodes.find(shortCode) != usedCodes.end() && secondLetter != initials[1]);

          // If we've exhausted all options for the second letter, start changing the first letter
          if(usedCodes.find(shortCode) != usedCodes.end())
            {
              char firstLetter = initials[0];
              do
                {
                  firstLetter++;
                  if(firstLetter > 'Z')
                    firstLetter = 'A';
                  shortCode = std::string(1, firstLetter) + initials[1] + std::to_string(number);
              } while(usedCodes.find(shortCode) != usedCodes.end() && firstLetter != initials[0]);
            }

          if(usedCodes.find(shortCode) != usedCodes.end())
            {
              throw std::runtime_error("Ran out of unique shortcodes!");
            }

          combatant->setShortCode(shortCode);
          usedCodes.insert(shortCode);
        }
    }

    std::vector<std::unique_ptr<Combatant>> _combatants;
    std::unordered_map<int, int> _typeCounter;
    Teams &_teams;

    // Map to store factory functions for each combatant type
    std::unordered_map<int, std::function<std::unique_ptr<Combatant>(int)>> _combatantFactories;

    // Helper function to register combatant types
    template <typename CombatantType> void registerCombatantType();
  };

}