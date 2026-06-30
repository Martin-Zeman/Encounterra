// Standalone "random matchup" test executable.
//
// This is intentionally NOT part of the test_encounterra suite (it is built as its own binary and is
// not registered with ctest). It pits two randomly selected teams against each other: each team gets a
// random size of 2-4 combatants (rolled independently per team), and every combatant is chosen at random
// from the full pool of available combatant types. Run ./bin/random_matchup; set ENC_SEED to reproduce.

#include "core/battle_map.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "core/round_manager.hpp"
#include "core/types.hpp"
#include "core/misc.hpp"
#include "core/logger.hpp"

#include "combatants/acolyte.hpp"
#include "combatants/bard_college_of_lore_lvl_3.hpp"
#include "combatants/battlemaster_fighter_lvl_3.hpp"
#include "combatants/battlemaster_fighter_lvl_4.hpp"
#include "combatants/battlemaster_fighter_lvl_5.hpp"
#include "combatants/brown_bear.hpp"
#include "combatants/bugbear_warrior.hpp"
#include "combatants/cleric_lvl_1.hpp"
#include "combatants/dire_wolf.hpp"
#include "combatants/sorcerer_lvl_1.hpp"
#include "combatants/draconic_sorcerer_lvl_3.hpp"
#include "combatants/draconic_sorcerer_lvl_5.hpp"
#include "combatants/fighter_lvl_1.hpp"
#include "combatants/fighter_lvl_2.hpp"
#include "combatants/giant_constrictor_snake.hpp"
#include "combatants/giant_spider.hpp"
#include "combatants/giant_toad.hpp"
#include "combatants/goblin.hpp"
#include "combatants/green_dragon_wyrmling.hpp"
#include "combatants/lion.hpp"
#include "combatants/moon_druid_lvl_3.hpp"
#include "combatants/moon_druid_lvl_5.hpp"
#include "combatants/night_hag.hpp"
#include "combatants/oath_of_vengeance_paladin_lvl_3.hpp"
#include "combatants/oath_of_vengeance_paladin_lvl_4.hpp"
#include "combatants/oath_of_vengeance_paladin_lvl_5.hpp"
#include "combatants/ogre.hpp"
#include "combatants/paladin_lvl_1.hpp"
#include "combatants/paladin_lvl_2.hpp"
#include "combatants/saber_toothed_tiger.hpp"
#include "combatants/stone_giant.hpp"
#include "combatants/tiger.hpp"
#include "combatants/wild_heart_barbarian_lvl_3.hpp"
#include "combatants/wild_heart_barbarian_lvl_4.hpp"
#include "combatants/wild_heart_barbarian_lvl_5.hpp"
#include "combatants/wizard_lvl_1.hpp"

#include <cstdlib>
#include <functional>
#include <iostream>
#include <random>
#include <string_view>
#include <vector>

using namespace enc;

namespace
{
  using Maker = std::function<Combatant *(int)>;

  // Every combatant type that can be fielded. Each entry just constructs one with a unique id.
  std::vector<Maker> makerPool()
  {
    return {
      [](int id) { return new Acolyte(id); },
      [](int id) { return new BardCollegeOfLoreLvl3(id); },
      [](int id) { return new BattlemasterFighterLvl3(id); },
      [](int id) { return new BattlemasterFighterLvl4(id); },
      [](int id) { return new BattlemasterFighterLvl5(id); },
      [](int id) { return new BrownBear(id); },
      [](int id) { return new BugbearWarrior(id); },
      [](int id) { return new ClericLvl1(id); },
      [](int id) { return new DireWolf(id); },
      [](int id) { return new SorcererLvl1(id); },
      [](int id) { return new DraconicSorcererLvl3(id); },
      [](int id) { return new DraconicSorcererLvl5(id); },
      [](int id) { return new FighterLvl1(id); },
      [](int id) { return new FighterLvl2(id); },
      [](int id) { return new GiantConstrictorSnake(id); },
      [](int id) { return new GiantSpider(id); },
      [](int id) { return new GiantToad(id); },
      [](int id) { return new Goblin(id); },
      [](int id) { return new GreenDragonWyrmling(id); },
      [](int id) { return new Lion(id); },
      [](int id) { return new MoonDruidLvl3(id); },
      [](int id) { return new MoonDruidLvl5(id); },
      [](int id) { return new NightHag(id); },
      [](int id) { return new OathOfVengeancePaladinLvl3(id); },
      [](int id) { return new OathOfVengeancePaladinLvl4(id); },
      [](int id) { return new OathOfVengeancePaladinLvl5(id); },
      [](int id) { return new Ogre(id); },
      [](int id) { return new PaladinLvl1(id); },
      [](int id) { return new PaladinLvl2(id); },
      [](int id) { return new SaberToothedTiger(id); },
      [](int id) { return new StoneGiant(id); },
      [](int id) { return new Tiger(id); },
      [](int id) { return new WildHeartBarbarianLvl3(id); },
      [](int id) { return new WildHeartBarbarianLvl4(id); },
      [](int id) { return new WildHeartBarbarianLvl5(id); },
      [](int id) { return new WizardLvl1(id); },
    };
  }

  std::string_view statName(Statistics stat)
  {
    switch(stat)
      {
      case Statistics::VICTORIES: return "victories";
      case Statistics::AT_LEAST_ONE_DIED: return "at_least_one_died";
      case Statistics::AT_LEAST_TWO_DIED: return "at_least_two_died";
      case Statistics::AT_LEAST_THREE_DIED: return "at_least_three_died";
      }
    return "unknown";
  }
}

int main()
{
  // Reproducible with ENC_SEED, otherwise pull a fresh random seed.
  std::mt19937::result_type seed;
  if(const char *seedEnv = std::getenv("ENC_SEED"))
    {
      seed = static_cast<std::mt19937::result_type>(std::strtoul(seedEnv, nullptr, 10));
    }
  else
    {
      seed = std::random_device{}();
    }
  std::mt19937 rng{seed};
  seedThreadRNG(seed);

  BattleMap::resetInstance();
  Teams::resetInstance();
  auto &battleMap = BattleMap::getInstance();
  Session session;

  const auto pool = makerPool();
  std::uniform_int_distribution<int> sizeDist(2, 4); // each team rolls its size independently
  std::uniform_int_distribution<int> pickDist(0, static_cast<int>(pool.size()) - 1);

  const int blueSize = sizeDist(rng);
  const int redSize = sizeDist(rng);

  std::vector<Combatant *> combatants;
  int idCounter = 1;

  auto fieldTeam = [&](Color color, int n, int column) {
    for(int i = 0; i < n; ++i)
      {
        Combatant *c = pool[pickDist(rng)](idCounter++);
        session.addCombatant(static_cast<Combatant *>(c), color);
        combatants.push_back(c);
        std::cout << COLOR_NAMES.at(color) << ": " << c->_name << "\n";
      }
  };

  std::cout << "--- Random matchup (seed " << seed << "): " << blueSize << " BLUE vs " << redSize << " RED ---\n";
  fieldTeam(Color::BLUE, blueSize, 1);
  fieldTeam(Color::RED, redSize, 13);

  battleMap.buildBaseAdjacencyMatrix();
  for(size_t i = 0; i < combatants.size(); ++i)
    {
      const bool blue = static_cast<int>(i) < blueSize;
      const int column = blue ? 1 : 13;
      const int slot = blue ? static_cast<int>(i) : static_cast<int>(i) - blueSize;
      battleMap.setCombatantCoordinates(*combatants[i], Coord{column, 2 + slot * 3});
    }

  RoundManager roundManager(combatants, 50);
  auto tally = roundManager.simulateN(1);

  std::cout << "--------------RESULTS--------------\n";
  for(Color color : {Color::BLUE, Color::RED})
    {
      std::cout << COLOR_NAMES.at(color) << ":\n";
      for(Statistics stat : getAllStatistics())
        {
          std::cout << "  " << statName(stat) << ": " << tally[color][stat] << "\n";
        }
    }

  return 0;
}
