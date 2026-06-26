#include "core/battle_map.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "core/round_manager.hpp"
#include "core/types.hpp"
#include "core/misc.hpp"
#include "core/logger.hpp"
#include "combatants/goblin.hpp"
#include "combatants/bugbear_warrior.hpp"
#include "combatants/draconic_sorcerer_lvl_3.hpp"
#include "combatants/battlemaster_fighter_lvl_5.hpp"
#include "combatants/wild_heart_barbarian_lvl_5.hpp"
#include "effects/effect_tracker.hpp"

#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <random>
#include <string>
#include <thread>
#include <vector>

using namespace enc;

namespace
{
  using TeamTally = std::unordered_map<Color, std::unordered_map<Statistics, int>>;

  // Runs `iterations` independent simulations in the *calling* thread and returns the per-team tally.
  //
  // Every piece of mutable global state the engine relies on (BattleMap / Teams / EffectTracker
  // singletons, the dice RNG, the dice caches and the combatant-id counter) is now thread_local, so
  // each worker builds and owns a completely independent copy of the world. That means the encounter
  // must be set up *inside* the worker, on the thread that will run it.
  //
  // `seed` reseeds this thread's dice RNG so the runs are statistically independent across threads
  // (and reproducible when ENC_SEED is set, see main()).
  TeamTally simulateChunk(int iterations, std::mt19937::result_type seed)
  {
    seedThreadRNG(seed);

    // Fresh, thread-local singletons for this worker.
    BattleMap::resetInstance();
    auto &battleMap = BattleMap::getInstance();
    Teams::resetInstance();
    EffectTracker::resetInstance();

    // Session owns the combatants (via unique_ptr); the RoundManager only borrows them.
    Session session;

    auto *bugbearWarrior = new BugbearWarrior(1);
    auto *goblinRed1 = new Goblin(1);
    auto *goblinRed2 = new Goblin(2);
    auto *goblinRed3 = new Goblin(3);
    auto *sorcererLvl3 = new DraconicSorcererLvl3(4);
    auto *fighterLvl5 = new BattlemasterFighterLvl5(5);
    auto *barbarianLvl5 = new WildHeartBarbarianLvl5(6);

    session.addCombatant(bugbearWarrior, Color::BLUE);
    session.addCombatant(goblinRed1, Color::RED);
    session.addCombatant(goblinRed2, Color::RED);
    session.addCombatant(goblinRed3, Color::BLUE);
    session.addCombatant(sorcererLvl3, Color::RED);
    session.addCombatant(fighterLvl5, Color::BLUE);
    session.addCombatant(barbarianLvl5, Color::RED);

    battleMap.buildBaseAdjacencyMatrix();
    battleMap.setCombatantCoordinates(*bugbearWarrior, Coord{1, 7});
    battleMap.setCombatantCoordinates(*goblinRed1, Coord{13, 7});
    battleMap.setCombatantCoordinates(*goblinRed2, Coord{11, 6});
    battleMap.setCombatantCoordinates(*goblinRed3, Coord{9, 8});
    battleMap.setCombatantCoordinates(*sorcererLvl3, Coord{7, 9});
    battleMap.setCombatantCoordinates(*fighterLvl5, Coord{5, 5});
    battleMap.setCombatantCoordinates(*barbarianLvl5, Coord{9, 9});

    std::vector<Combatant *> combatants = {bugbearWarrior, goblinRed1, goblinRed2, goblinRed3, sorcererLvl3, fighterLvl5, barbarianLvl5};
    RoundManager roundManager(combatants, 50);

    return roundManager.simulateN(iterations);
  }

  // Folds `src` into `dst` (dst += src) entry by entry.
  void mergeTally(TeamTally &dst, const TeamTally &src)
  {
    for(const auto &[color, stats] : src)
      {
        for(const auto &[stat, value] : stats)
          {
            dst[color][stat] += value;
          }
      }
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

  // Parses an integer that follows a flag, e.g. "--cores 8". Returns false on a missing/invalid value.
  bool parseIntArg(int argc, char **argv, int &i, int &out)
  {
    if(i + 1 >= argc)
      {
        return false;
      }
    char *endPtr = nullptr;
    long value = std::strtol(argv[++i], &endPtr, 10);
    if(endPtr == argv[i] || *endPtr != '\0' || value <= 0)
      {
        return false;
      }
    out = static_cast<int>(value);
    return true;
  }

  void printUsage(const char *prog)
  {
    std::cout << "Usage: " << prog << " [--cores N] [--iterations N] [--logs]\n"
              << "  -j, --cores N        number of CPU cores to distribute the simulations across "
                 "(default: 1)\n"
              << "  -n, --iterations N   total number of independent simulations to run (default: 100)\n"
              << "  -v, --logs           print full combat narration instead of suppressing it "
                 "(default: suppressed)\n";
  }
}

int main(int argc, char **argv)
{
  int cores = 1;
  int iterations = 100;
  bool showLogs = false;

  for(int i = 1; i < argc; ++i)
    {
      const char *arg = argv[i];
      if(std::strcmp(arg, "--cores") == 0 || std::strcmp(arg, "-j") == 0)
        {
          if(!parseIntArg(argc, argv, i, cores))
            {
              std::cerr << "Invalid value for " << arg << "\n";
              printUsage(argv[0]);
              return 1;
            }
        }
      else if(std::strcmp(arg, "--iterations") == 0 || std::strcmp(arg, "-n") == 0)
        {
          if(!parseIntArg(argc, argv, i, iterations))
            {
              std::cerr << "Invalid value for " << arg << "\n";
              printUsage(argv[0]);
              return 1;
            }
        }
      else if(std::strcmp(arg, "--logs") == 0 || std::strcmp(arg, "-v") == 0)
        {
          showLogs = true;
        }
      else if(std::strcmp(arg, "--help") == 0 || std::strcmp(arg, "-h") == 0)
        {
          printUsage(argv[0]);
          return 0;
        }
      else
        {
          std::cerr << "Unknown argument: " << arg << "\n";
          printUsage(argv[0]);
          return 1;
        }
    }

  // Clamp the requested core count to something sensible: at least one, never more than the number of
  // simulations (extra threads would have no work) nor more than the hardware can run concurrently.
  const unsigned hardware = std::max(1u, std::thread::hardware_concurrency());
  cores = std::clamp(cores, 1, std::min(iterations, static_cast<int>(hardware)));

  // Combat narration is written directly to std::cout/std::cerr, which interleaves unintelligibly across
  // threads. Only honour --logs when running single-threaded; otherwise force suppression and warn.
  if(showLogs && cores > 1)
    {
      std::cerr << "Warning: --logs is ignored when running on more than one core (output would interleave "
                   "across threads). Use --cores 1 to see the combat narration.\n";
      showLogs = false;
    }

  // Base seed for the whole run. When ENC_SEED is set the entire (multi-threaded) run is reproducible:
  // worker k uses base + k, so the threads stay independent of one another while remaining deterministic.
  std::mt19937::result_type baseSeed;
  if(const char *seedEnv = std::getenv("ENC_SEED"))
    {
      baseSeed = static_cast<std::mt19937::result_type>(std::strtoul(seedEnv, nullptr, 10));
    }
  else
    {
      baseSeed = std::random_device{}();
    }

  // Split the work as evenly as possible: the first `remainder` workers run one extra iteration.
  std::vector<int> perThread(cores, iterations / cores);
  for(int i = 0; i < iterations % cores; ++i)
    {
      perThread[i] += 1;
    }

  std::cout << "Running " << iterations << " simulations across " << cores << " core(s)...\n";

  // Per-iteration combat narration is suppressed by default (and always when multi-threaded, see above).
  // When --logs is given on a single-core run we leave the streams untouched so the full narration prints.
  // The streams are routed to a stateless null sink; we keep it off until every worker has joined so no
  // thread races on toggling it.
  if(!showLogs)
    {
      Logger::setLevel(LogLevel::NONE);
    }

  std::vector<TeamTally> partials(cores);
  std::vector<std::thread> workers;
  workers.reserve(cores);

  const auto start = std::chrono::steady_clock::now();

  for(int t = 1; t < cores; ++t)
    {
      workers.emplace_back([&, t] {
        partials[t] = simulateChunk(perThread[t], baseSeed + static_cast<std::mt19937::result_type>(t));
      });
    }
  // Run the first chunk on the main thread so a single-core run spawns no extra threads at all.
  partials[0] = simulateChunk(perThread[0], baseSeed);

  for(auto &worker : workers)
    {
      worker.join();
    }

  const auto end = std::chrono::steady_clock::now();

  // Aggregate every worker's tally into one.
  TeamTally totals;
  for(const auto &partial : partials)
    {
      mergeTally(totals, partial);
    }

  Logger::setLevel(LogLevel::INFO); // restore output so we can print the result

  const double seconds = std::chrono::duration<double>(end - start).count();
  std::cout << "--- C++ simulation (" << iterations << " iterations, " << cores << " core(s)) took " << seconds << " seconds ---\n";

  std::cout << "--------------RESULTS--------------\n";
  for(Color color : {Color::BLUE, Color::RED})
    {
      std::cout << COLOR_NAMES.at(color) << ":\n";
      for(Statistics stat : getAllStatistics())
        {
          std::cout << "  " << statName(stat) << ": " << totals[color][stat] << "\n";
        }
    }

  return 0;
}