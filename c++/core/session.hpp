#pragma once

#include <vector>
#include <string>
#include <set>
#include <stdexcept>
#include <cctype>
#include <algorithm>
#include <regex>
#include "core/combatant.hpp"
#include "core/resources.hpp"
#include "core/types.hpp"
#include "core/teams.hpp"

namespace enc
{
  class Session
  {
  public:
    Session();
    ~Session();

    void addCombatant(Combatant *combatant, Color teamColor, ResourceDepletionLevel resourceDepletionLevel);

    template <typename CombatantType>
    void addCombatant(CombatantType *combatant, Color teamColor, ResourceDepletionLevel resourceDepletionLevel); // For testing purposes

    template <typename CombatantType> void addCombatant(Color teamColor, ResourceDepletionLevel resourceDepletionLevel);
    void addCombatant(Combatant *combatant, Color teamColor);

    // std::unordered_map<Team, int> simulate(bool parallel = false);

  private:
    void generateUniqueShortCodes()
    {
      std::set<std::string> usedCodes;

      for(Combatant *combatant : _combatants)
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

          // Extract first letters of words
          std::istringstream iss(nameWithoutNumber);
          std::string initials;
          std::string word;
          while(iss >> word)
            {
              if(!word.empty() && std::isalpha(word[0]))
                {
                  initials += std::toupper(word[0]);
                }
            }

          // If we don't have at least 2 initials, use additional letters from words
          if(initials.length() < 2)
            {
              iss.clear();
              iss.seekg(0);
              while(iss >> word && initials.length() < 2)
                {
                  for(size_t i = 1; i < word.length() && initials.length() < 2; ++i)
                    {
                      if(std::isalpha(word[i]))
                        {
                          initials += std::toupper(word[i]);
                        }
                    }
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

    std::vector<Combatant *> _combatants; // Session is the owner of Combatants
    std::unordered_map<int, int> _typeCounter;
    int _numSimulations;
    Teams &_teams;

    // Map to store factory functions for each combatant type
    std::unordered_map<int, std::function<Combatant *(int)>> _combatantFactories;

    // Helper function to register combatant types
    template <typename CombatantType> void registerCombatantType();
  };

}