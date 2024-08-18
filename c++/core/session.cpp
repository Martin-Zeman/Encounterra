#include "session.hpp"
#include "combatants/battlemaster_fighter_lvl_5.hpp"
#include "combatants/stone_giant.hpp"
#include "combatants/bugbear.hpp"
#include "combatants/goblin.hpp"
#include "combatants/draconic_sorcerer_lvl_1.hpp"
#include "combatants/giant_toad.hpp"
#include "combatants/ogre.hpp"
#include "combatants/wild_heart_barbarian_lvl_3.hpp"

namespace enc
{

  Session::Session() : _teams(Teams::getInstance())
  {
    // Register all combatant types
    registerCombatantType<BattlemasterFighterLvl5>();
    registerCombatantType<StoneGiant>();
    // Register other combatant types...
  }

  template <typename CombatantType> void Session::addCombatant(Color teamColor, float resourceDepletionLevel)
  {
    int classId = CombatantType::getClassId();
    auto factoryIt = _combatantFactories.find(classId);
    if(factoryIt == _combatantFactories.end())
      {
        throw std::runtime_error("Unsupported combatant type");
      }

    auto combatant = factoryIt->second(_combatants.size() + 1);
    combatant->setResourceDepletionLevel(resourceDepletionLevel);
    _teams.addCombatantToTeam(*combatant, teamColor);
    _combatants.push_back(std::move(combatant));
    generateUniqueShortcodes();
  }

  void Session::generateUniqueShortCodes()
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

  template <typename CombatantType> void Session::registerCombatantType()
  {
    int classId = CombatantType::getClassId();
    _combatantFactories[classId] = [](int num) { return std::make_unique<CombatantType>(num); };
  }

  // Explicit template instantiations
  template void Session::addCombatant<BattlemasterFighterLvl5>(Color, float);
  template void Session::addCombatant<StoneGiant>(Color, float);
  // Add more explicit instantiations for other combatant types
}