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

  void Session::addCombatant(Combatant *combatant, Color teamColor, ResourceDepletionLevel resourceDepletionLevel)
  {
    combatant->setResourceDepletionLevel(resourceDepletionLevel);
    _teams.addCombatantToTeam(combatant, teamColor);
    _combatants.push_back(std::move(combatant));
    generateUniqueShortCodes();
  }

  template <typename CombatantType>
  void Session::addCombatant(CombatantType *combatant, Color teamColor, ResourceDepletionLevel resourceDepletionLevel)
  {
    int classId = CombatantType::getStaticClassId();
    auto factoryIt = _combatantFactories.find(classId);

    if(factoryIt == _combatantFactories.end())
      {
        throw std::runtime_error("Unsupported combatant type");
      }
    combatant->setResourceDepletionLevel(resourceDepletionLevel);
    _teams.addCombatantToTeam(combatant, teamColor);
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
    _teams.addCombatantToTeam(combatant, teamColor);
    _combatants.push_back(std::move(combatant));
    generateUniqueShortCodes();
  }

  void Session::addCombatant(Combatant *combatant, Color teamColor)
  {
    addCombatant(std::move(combatant), teamColor, ResourceDepletionLevel::FULLY_RESTED);
  }

  template <typename CombatantType> void Session::registerCombatantType()
  {
    int classId = CombatantType::getStaticClassId();
    _combatantFactories[classId] = [](int num) { return std::make_unique<CombatantType>(num); };
  }

  // std::unordered_map<Team, int> Session::simulate(bool parallel)
  // {
  //   if(!parallel || _numSimulations < std::thread::hardware_concurrency())
  //     {
  //       return round_manager.simulateN(_numSimulations);
  //     }

  //   // Calculate simulations per thread
  //   const size_t numThreads = std::thread::hardware_concurrency();
  //   const size_t simsPerThread = _numSimulations / numThreads;
  //   const size_t remainder = _numSimulations % numThreads;

  //   // Create futures to store results
  //   std::vector<std::future<std::unordered_map<Team, int>>> futures;
  //   futures.reserve(numThreads + (remainder > 0 ? 1 : 0));

  //   // Launch simulation threads
  //   for(size_t i = 0; i < numThreads; ++i)
  //     {
  //       futures.push_back(std::async(std::launch::async, [this, simsPerThread]() {
  //         // Each thread gets its own instance of RoundManager
  //         RoundManager threadRm(combatants, teams, EffectTracker::getInstance());
  //         place_combatants_on_the_map(); // This will use thread-local BattleMap
  //         BattleMap::getInstance().buildBaseAdjacencyMatrix();
  //         return threadRm.simulateN(simsPerThread);
  //       }));
  //     }

  //   // Handle remainder simulations if any
  //   if(remainder > 0)
  //     {
  //       futures.push_back(std::async(std::launch::async, [this, remainder]() {
  //         RoundManager threadRm(combatants, teams, EffectTracker::getInstance());
  //         place_combatants_on_the_map();
  //         BattleMap::getInstance().buildBaseAdjacencyMatrix();
  //         return threadRm.simulateN(remainder);
  //       }));
  //     }

  //   // Accumulate results
  //   std::unordered_map<Team, int> accumulatedTally;
  //   for(auto &future : futures)
  //     {
  //       auto tally = future.get();
  //       for(const auto &[team, victories] : tally)
  //         {
  //           accumulatedTally[team] += victories;
  //         }
  //     }

  //   // Log results
  //   logger.warning("--------------STATISTICS--------------");
  //   for(const auto &[team, victories] : accumulatedTally)
  //     {
  //       logger.warning("Team " + team.name + " won total of " + std::to_string(victories) + " times", {{"team", team}});
  //     }

  //   return accumulatedTally;
  // }

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

  template void Session::addCombatant<Acolyte>(Acolyte *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<BattlemasterFighterLvl5>(BattlemasterFighterLvl5 *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<BrownBear>(BrownBear *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<Bugbear>(Bugbear *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<DireWolf>(DireWolf *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<DraconicSorcererLvl1>(DraconicSorcererLvl1 *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<DraconicSorcererLvl5>(DraconicSorcererLvl5 *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<GiantConstrictorSnake>(GiantConstrictorSnake *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<GiantSpider>(GiantSpider *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<GiantToad>(GiantToad *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<Goblin>(Goblin *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<GreenDragonWyrmling>(GreenDragonWyrmling *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<MoonDruidLvl5>(MoonDruidLvl5 *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<NightHag>(NightHag *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<Ogre>(Ogre *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<SaberToothedTiger>(SaberToothedTiger *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<StoneGiant>(StoneGiant *, Color, ResourceDepletionLevel);
  template void Session::addCombatant<WildHeartBarbarianLvl3>(WildHeartBarbarianLvl3 *, Color, ResourceDepletionLevel);

  // Add more explicit instantiations for other combatant types
}