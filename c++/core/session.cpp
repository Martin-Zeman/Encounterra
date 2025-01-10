#include "session.hpp"
#include "combatants/acolyte.hpp"
#include "combatants/battlemaster_fighter_lvl_5.hpp"
#include "combatants/brown_bear.hpp"
#include "combatants/bugbear.hpp"
#include "combatants/dire_wolf.hpp"
#include "combatants/draconic_sorcerer_lvl_1.hpp"
#include "combatants/draconic_sorcerer_lvl_5.hpp"
#include "combatants/giant_constrictor_snake.hpp"
#include "combatants/giant_spider.hpp"
#include "combatants/giant_toad.hpp"
#include "combatants/goblin.hpp"
#include "combatants/green_dragon_wyrmling.hpp"
#include "combatants/moon_druid_lvl_5.hpp"
#include "combatants/night_hag.hpp"
#include "combatants/ogre.hpp"
#include "combatants/saber_toothed_tiger.hpp"
#include "combatants/stone_giant.hpp"
#include "combatants/wild_heart_barbarian_lvl_3.hpp"

namespace enc
{

  Session::Session() : _teams(Teams::getInstance())
  {
    // Register all combatant types
    registerCombatantType<Acolyte>();
    registerCombatantType<BattlemasterFighterLvl5>();
    registerCombatantType<BrownBear>();
    registerCombatantType<Bugbear>();
    registerCombatantType<DireWolf>();
    registerCombatantType<DraconicSorcererLvl1>();
    registerCombatantType<DraconicSorcererLvl5>();
    registerCombatantType<GiantConstrictorSnake>();
    registerCombatantType<GiantSpider>();
    registerCombatantType<GiantToad>();
    registerCombatantType<Goblin>();
    registerCombatantType<GreenDragonWyrmling>();
    registerCombatantType<MoonDruidLvl5>();
    registerCombatantType<NightHag>();
    registerCombatantType<Ogre>();
    registerCombatantType<SaberToothedTiger>();
    registerCombatantType<StoneGiant>();
    registerCombatantType<WildHeartBarbarianLvl3>();
    // Register other combatant types...
  }

  void Session::addCombatant(std::shared_ptr<Combatant> combatant, Color teamColor, ResourceDepletionLevel resourceDepletionLevel)
  {
    combatant->setResourceDepletionLevel(resourceDepletionLevel);
    _teams.addCombatantToTeam(*combatant, teamColor);
    _combatants.push_back(std::move(combatant)); // Move from the shared_ptr argument
    generateUniqueShortCodes();
  }

  template <typename CombatantType>
  void Session::addCombatant(std::shared_ptr<CombatantType> combatant, Color teamColor, ResourceDepletionLevel resourceDepletionLevel)
  {
    int classId = CombatantType::getStaticClassId();
    auto factoryIt = _combatantFactories.find(classId);

    if(factoryIt == _combatantFactories.end())
      {
        throw std::runtime_error("Unsupported combatant type");
      }
    combatant->setResourceDepletionLevel(resourceDepletionLevel);
    _teams.addCombatantToTeam(*combatant, teamColor);
    _combatants.push_back(std::move(combatant));
    generateUniqueShortCodes();
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

  void Session::addCombatant(std::shared_ptr<Combatant> combatant, Color teamColor)
  {
    addCombatant(std::move(combatant), teamColor, ResourceDepletionLevel::FULLY_RESTED);
  }

  template <typename CombatantType> void Session::registerCombatantType()
  {
    int classId = CombatantType::getStaticClassId();
    _combatantFactories[classId] = [](int num) { return std::make_unique<CombatantType>(num); };
  }

  // Explicit template instantiations
  template void Session::addCombatant<Acolyte>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<BattlemasterFighterLvl5>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<BrownBear>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<Bugbear>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<DireWolf>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<DraconicSorcererLvl1>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<DraconicSorcererLvl5>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<GiantConstrictorSnake>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<GiantSpider>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<GiantToad>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<Goblin>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<GreenDragonWyrmling>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<MoonDruidLvl5>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<NightHag>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<Ogre>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<SaberToothedTiger>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<StoneGiant>(Color, ResourceDepletionLevel);
  template void Session::addCombatant<WildHeartBarbarianLvl3>(Color, ResourceDepletionLevel);

  template void Session::addCombatant<Acolyte>(std::shared_ptr<Acolyte>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<BattlemasterFighterLvl5>(std::shared_ptr<BattlemasterFighterLvl5>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<BrownBear>(std::shared_ptr<BrownBear>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<Bugbear>(std::shared_ptr<Bugbear>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<DireWolf>(std::shared_ptr<DireWolf>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<DraconicSorcererLvl1>(std::shared_ptr<DraconicSorcererLvl1>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<DraconicSorcererLvl5>(std::shared_ptr<DraconicSorcererLvl5>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<GiantConstrictorSnake>(std::shared_ptr<GiantConstrictorSnake>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<GiantSpider>(std::shared_ptr<GiantSpider>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<GiantToad>(std::shared_ptr<GiantToad>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<Goblin>(std::shared_ptr<Goblin>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<GreenDragonWyrmling>(std::shared_ptr<GreenDragonWyrmling>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<MoonDruidLvl5>(std::shared_ptr<MoonDruidLvl5>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<NightHag>(std::shared_ptr<NightHag>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<Ogre>(std::shared_ptr<Ogre>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<SaberToothedTiger>(std::shared_ptr<SaberToothedTiger>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<StoneGiant>(std::shared_ptr<StoneGiant>, Color, ResourceDepletionLevel);
  template void Session::addCombatant<WildHeartBarbarianLvl3>(std::shared_ptr<WildHeartBarbarianLvl3>, Color, ResourceDepletionLevel);

  // Add more explicit instantiations for other combatant types
}