#include "core/battle_map.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "core/round_manager.hpp"
#include "core/types.hpp"
#include "core/logger.hpp"
#include "combatants/goblin.hpp"
#include "combatants/bugbear_warrior.hpp"
#include "effects/effect_tracker.hpp"

#include <chrono>
#include <iostream>
#include <vector>

using namespace enc;

// Minimal end-to-end simulation: two goblins fighting each other.
// Exercises the full decision/resolution chain:
//   RoundManager::simulate -> getAction -> calculateActionPlan -> generateProtoDag
//   -> buildActionStateMachine -> findBestSequence -> translateSequenceToActions
//   -> ActionResolver::resolveAction -> resolveByActoidFlags.
int main()
{
    // Reset the singletons to a clean state (mirrors the test fixtures).
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

    session.addCombatant(bugbearWarrior, Color::BLUE);
    session.addCombatant(goblinRed1, Color::RED);
    session.addCombatant(goblinRed2, Color::RED);
    session.addCombatant(goblinRed3, Color::RED);

    // Place the two goblins on opposite sides of the map.
    battleMap.buildBaseAdjacencyMatrix();
    battleMap.setCombatantCoordinates(*bugbearWarrior, Coord{1, 7});
    battleMap.setCombatantCoordinates(*goblinRed1, Coord{13, 7});
    battleMap.setCombatantCoordinates(*goblinRed2, Coord{11, 6});
    battleMap.setCombatantCoordinates(*goblinRed3, Coord{9, 8});

    std::vector<Combatant *> combatants = {bugbearWarrior, goblinRed1, goblinRed2, goblinRed3};
    RoundManager roundManager(combatants, 50);

    // Benchmark: run 100 iterations with all combat narration suppressed.
    constexpr int iterations = 100;
    Logger::setLevel(LogLevel::NONE);
    const auto start = std::chrono::steady_clock::now();
    roundManager.simulateN(iterations);
    const auto end = std::chrono::steady_clock::now();
    Logger::setLevel(LogLevel::INFO); // restore output so we can print the result

    const double seconds = std::chrono::duration<double>(end - start).count();
    std::cout << "--- C++ simulation (" << iterations << " iterations) took "
              << seconds << " seconds ---\n";

    return 0;
}