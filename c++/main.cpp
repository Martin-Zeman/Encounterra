#include "core/battle_map.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "core/round_manager.hpp"
#include "core/types.hpp"
#include "combatants/goblin.hpp"
#include "effects/effect_tracker.hpp"

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

    auto *goblinBlue = new Goblin(1);
    auto *goblinRed = new Goblin(2);

    session.addCombatant(goblinBlue, Color::BLUE);
    session.addCombatant(goblinRed, Color::RED);

    // Place the two goblins on opposite sides of the map.
    battleMap.buildBaseAdjacencyMatrix();
    battleMap.setCombatantCoordinates(*goblinBlue, Coord{1, 7});
    battleMap.setCombatantCoordinates(*goblinRed, Coord{13, 7});

    std::vector<Combatant *> combatants = {goblinBlue, goblinRed};
    RoundManager roundManager(combatants, 50);
    roundManager.simulateN(1);

    return 0;
}