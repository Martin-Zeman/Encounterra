#include "session.hpp"
#include "combatants/battlemaster_fighter_lvl_5.hpp"
#include "combatants/stone_giant.hpp"
#include "combatants/bugbear_warrior.hpp"
#include "combatants/goblin.hpp"
#include "combatants/draconic_sorcerer_lvl_1.hpp"
#include "combatants/giant_toad.hpp"
#include "combatants/ogre.hpp"
#include "combatants/wild_heart_barbarian_lvl_3.hpp"
#include "combatants/green_dragon_wyrmling.hpp"

namespace enc
{

  Session::Session() : _teams(Teams::getInstance())
  {
    // Register all combatant types
    registerCombatantType<BattlemasterFighterLvl5>();
    registerCombatantType<BugbearWarrior>();
    registerCombatantType<DraconicSorcererLvl1>();
    registerCombatantType<GiantToad>();
    registerCombatantType<Goblin>();
    registerCombatantType<GreenDragonWyrmling>();
    registerCombatantType<Ogre>();
    registerCombatantType<StoneGiant>();
    registerCombatantType<WildHeartBarbarianLvl3>();
    // Register other combatant types...
  }

  template <typename CombatantType> void Session::addCombatant(Color teamColor, ResourceDepletionLevel resourceDepletionLevel)
  {
    int classId = CombatantType::getStaticClassId();
    auto factoryIt = _combatantFactories.find(classId);

    if(factoryIt == _combatantFactories.end())
      {
        throw std::runtime_error("Unsupported combatant type");
      }

    auto combatant = factoryIt->second(++_typeCounter[classId] + 1);
    combatant->setResourceDepletionLevel(resourceDepletionLevel);
    _teams.addCombatantToTeam(*combatant, teamColor);
    _combatants.push_back(std::move(combatant));
    generateUniqueShortCodes();
  }
  
  template <typename CombatantType> void Session::addCombatant(CombatantType* combatant, Color teamColor, ResourceDepletionLevel resourceDepletionLevel)
  {
    // For testing purposes
    combatant->setResourceDepletionLevel(resourceDepletionLevel);
    _teams.addCombatantToTeam(*combatant, teamColor);
    _combatants.emplace_back(std::move(std::unique_ptr<Combatant>(combatant)));
    generateUniqueShortCodes();
  }

  template <typename CombatantType> void Session::registerCombatantType()
  {
    int classId = CombatantType::getStaticClassId();
    _combatantFactories[classId] = [](int num) { return std::make_unique<CombatantType>(num); };
  }

  // Explicit template instantiations
  template void Session::addCombatant<BattlemasterFighterLvl5>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<BugbearWarrior>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<DraconicSorcererLvl1>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<GiantToad>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<Goblin>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<GreenDragonWyrmling>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<Ogre>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<StoneGiant>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<WildHeartBarbarianLvl3>(Color, ResourceDepletionLevel);

  template void Session::addCombatant<BattlemasterFighterLvl5>(BattlemasterFighterLvl5*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<BugbearWarrior>(BugbearWarrior*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<DraconicSorcererLvl1>(DraconicSorcererLvl1*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<GiantToad>(GiantToad*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<Goblin>(Goblin*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<GreenDragonWyrmling>(GreenDragonWyrmling*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<Ogre>(Ogre*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<StoneGiant>(StoneGiant*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<WildHeartBarbarianLvl3>(WildHeartBarbarianLvl3*, Color, ResourceDepletionLevel);
  template void Session::addCombatant<Combatant>(Combatant*, Color, ResourceDepletionLevel);

  // Add more explicit instantiations for other combatant types
}