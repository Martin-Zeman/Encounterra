#include "core/battle_map.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "core/round_manager.hpp"
#include "core/types.hpp"
#include "core/logger.hpp"
#include "combatants/goblin.hpp"
#include "combatants/bugbear_warrior.hpp"
#include "combatants/draconic_sorcerer_lvl_3.hpp"
#include "combatants/battlemaster_fighter_lvl_5.hpp"
#include "combatants/wild_heart_barbarian_lvl_5.hpp"
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

    // Place the two goblins on opposite sides of the map.
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

    // Benchmark: run 100 iterations with all combat narration suppressed.
    constexpr int iterations = 1;
    // Logger::setLevel(LogLevel::NONE);
    const auto start = std::chrono::steady_clock::now();
    roundManager.simulateN(iterations);
    const auto end = std::chrono::steady_clock::now();
    // Logger::setLevel(LogLevel::INFO); // restore output so we can print the result

    const double seconds = std::chrono::duration<double>(end - start).count();
    std::cout << "--- C++ simulation (" << iterations << " iterations) took "
              << seconds << " seconds ---\n";

    return 0;
}