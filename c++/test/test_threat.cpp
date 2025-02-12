#include <gtest/gtest.h>
#include "core/threat_utils.hpp"
#include "core/battle_map.hpp"
// #include "combat/actions/movement.hpp"
#include "spells/cloud_of_daggers.hpp"
// #include "spells/firebolt.hpp"
#include "spells/hunger_of_hadar.hpp"
#include "spells/misty_step.hpp"
#include "spells/spike_growth.hpp"
#include "combatants/goblin.hpp"
#include "combatants/draconic_sorcerer_lvl_1.hpp"
#include "combatants/draconic_sorcerer_lvl_5.hpp"
#include "combatants/bugbear.hpp"
#include "combatants/wild_heart_barbarian_lvl_3.hpp"
#include "combatants/wild_heart_barbarian_lvl_5.hpp"
#include "core/teams.hpp"
#include "core/types.hpp"
#include "core/session.hpp"
#include "actions/action_types.hpp"
#include "actions/movement.hpp"
#include "actions/action_selection.hpp"
#include "effects/effect_tracker.hpp"
#include "effects/aoe_effect.hpp"

using namespace enc;

namespace
{
    class ThreatUtilsTest : public ::testing::Test {
    protected:
      void SetUp() override
      {
        BattleMap::resetInstance(); // Reset the singleton instance before each test
        battleMap = &BattleMap::getInstance();
        Teams::resetInstance();
        teams = &Teams::getInstance();
        session = new Session();
        EffectTracker::resetInstance();
        effectTracker = &EffectTracker::getInstance();

        draconic_sorcerer_lvl_1 = new DraconicSorcererLvl1(1);
        draconic_sorcerer_lvl_5 = new DraconicSorcererLvl5(1);
        goblin = new Goblin(1);
        bugbear = new Bugbear(1);
        wild_heart_barbarian_lvl_3 = new WildHeartBarbarianLvl3(1);
        wild_heart_barbarian_lvl_5 = new WildHeartBarbarianLvl5(1);
      }

      void TearDown() override
      {
        // BattleMap::resetInstance();
        // Teams::resetInstance();
        // EffectTracker::resetInstance();
        delete session;
      }

    Combatant* draconic_sorcerer_lvl_1;
    Combatant* draconic_sorcerer_lvl_5;
    Combatant* goblin;
    Combatant* bugbear;
    Combatant* wild_heart_barbarian_lvl_3;
    Combatant* wild_heart_barbarian_lvl_5;
    
    BattleMap* battleMap;
    Teams* teams;
    EffectTracker* effectTracker;
    Session *session;
};

TEST_F(ThreatUtilsTest, MediumToMediumOneFullSpikeGrowth) {
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(goblin, Color::RED);

    auto sgFactory = SpikeGrowthFactory(AbilityType::SPIKE_GROWTH, goblin, &goblin->getSpellslots());
    Coord coord{7, 3};
    auto actoid = sgFactory.create(&coord);
    auto effect = dynamic_cast<Effect *>(actoid);
    effectTracker->add(effect);

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{13, 3});

    auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *goblin);
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for (AoeEffect * effect : EffectTracker::getInstance().getAoeEffects()) {
        effectToCoords[effect] = effect->getAffectedCoords();
    }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_1);
    draconic_sorcerer_lvl_1->setShortestPathsCache(shortestPaths);

    auto threat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords);
    EXPECT_NEAR(threat.back(), -9.0 * 5.0 - 2.925 * DZ_CONSTANT, 0.001);
}

TEST_F(ThreatUtilsTest, MediumToMediumOnePartialSpikeGrowth) {
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(goblin, Color::RED);

    auto sgFactory = SpikeGrowthFactory(AbilityType::SPIKE_GROWTH, goblin, &goblin->getSpellslots());
    Coord coord{7, 6};
    auto actoid = sgFactory.create(&coord);
    auto effect = dynamic_cast<Effect *>(actoid);
    effectTracker->add(effect);

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{13, 3});

    auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *goblin);
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for (AoeEffect * effect : EffectTracker::getInstance().getAoeEffects()) {
        ASSERT_TRUE(effect);
        effectToCoords[effect] = effect->getAffectedCoords();
    }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_1);
    draconic_sorcerer_lvl_1->setShortestPathsCache(shortestPaths);

    auto threat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords);
    EXPECT_NEAR(threat.back(), -5.0 * 5.0 - 2.925 * DZ_CONSTANT, 0.001);
}

TEST_F(ThreatUtilsTest, LargeToMediumOneAoe) {
    draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(goblin, Color::RED);

    auto cloudFactory = CloudOfDaggersFactory(AbilityType::CLOUD_OF_DAGGERS, goblin, &goblin->getSpellslots());
    Coord coord{4, 2};
    auto actoid = cloudFactory.create(&coord);
    auto effect = dynamic_cast<Effect *>(actoid);
    effectTracker->add(std::move(effect));

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{1, 1});
    battleMap->setCombatantCoordinates(*goblin, Coord{7, 1});

    auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *goblin);
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for (AoeEffect * effect : EffectTracker::getInstance().getAoeEffects()) {
        ASSERT_TRUE(effect);
        effectToCoords[effect] = effect->getAffectedCoords();
    }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_1);
    draconic_sorcerer_lvl_1->setShortestPathsCache(shortestPaths);

    auto threat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords);
    EXPECT_NEAR(threat.back(), -10.0 - 2.925 * DZ_CONSTANT, 0.001);
}

TEST_F(ThreatUtilsTest, LargeToMediumAvoidedAoe) {
    draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(goblin, Color::RED);

    auto hungerFactory = HungerOfHadarFactory(15, AbilityType::HUNGER_OF_HADAR, goblin, &goblin->getSpellslots());
    Coord coord{4, 7};
    auto actoid = hungerFactory.create(&coord);
    auto effect = dynamic_cast<Effect *>(actoid);
    effectTracker->add(std::move(effect));

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{1, 1});
    battleMap->setCombatantCoordinates(*goblin, Coord{7, 1});

    auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *goblin);
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for (AoeEffect * effect : EffectTracker::getInstance().getAoeEffects()) {
        ASSERT_TRUE(effect);
        effectToCoords[effect] = effect->getAffectedCoords();
    }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_1);
    draconic_sorcerer_lvl_1->setShortestPathsCache(shortestPaths);

    auto threat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords);
    EXPECT_NEAR(threat.back(), -2.925 * DZ_CONSTANT, 0.001); // Just danger zone
}

TEST_F(ThreatUtilsTest, MediumToMediumTwoOverlappingAoe) {
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(goblin, Color::RED);

    auto cloudFactory = CloudOfDaggersFactory(AbilityType::CLOUD_OF_DAGGERS, goblin, &goblin->getSpellslots());
    Coord coord{7, 3};
    auto actoid1 = cloudFactory.create(&coord);
    auto actoid2 = cloudFactory.create(&coord);
    auto effect1 = dynamic_cast<Effect *>(actoid1);
    auto effect2 = dynamic_cast<Effect *>(actoid2);
    effectTracker->add(std::move(effect1));
    effectTracker->add(std::move(effect2));

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{13, 3});

    auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *goblin);
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for (AoeEffect * effect : EffectTracker::getInstance().getAoeEffects()) {
        ASSERT_TRUE(effect);
        effectToCoords[effect] = effect->getAffectedCoords();
    }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_1);
    draconic_sorcerer_lvl_1->setShortestPathsCache(shortestPaths);

    auto threat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords);
    EXPECT_NEAR(threat.back(), -20.0 - 2.925 * DZ_CONSTANT, 0.0001);
}

TEST_F(ThreatUtilsTest, LargeToMediumTwoOverlappingAoe) {
    draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(goblin, Color::RED);

    auto cloudFactory = CloudOfDaggersFactory(AbilityType::CLOUD_OF_DAGGERS, goblin, &goblin->getSpellslots());
    
    // Create two overlapping effects that should hit due to combatant's size
    Coord coord1{7, 3};
    Coord coord2{7, 4};
    auto actoid1 = cloudFactory.create(&coord1);
    auto actoid2 = cloudFactory.create(&coord2);
    auto effect1 = dynamic_cast<Effect *>(actoid1);
    auto effect2 = dynamic_cast<Effect *>(actoid2);
    effectTracker->add(std::move(effect1));
    effectTracker->add(std::move(effect2));

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{0, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{13, 3});

    auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *goblin);
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for (AoeEffect * effect : EffectTracker::getInstance().getAoeEffects()) {
        ASSERT_TRUE(effect);
        effectToCoords[effect] = effect->getAffectedCoords();
    }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_1);
    draconic_sorcerer_lvl_1->setShortestPathsCache(shortestPaths);

    auto threat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords);
    EXPECT_NEAR(threat.back(), -20.0 - 2.925 * DZ_CONSTANT, 0.0001);
}

TEST_F(ThreatUtilsTest, LargeToMediumStartingInsideAoe) {
    draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(goblin, Color::RED);

    auto cloudFactory = CloudOfDaggersFactory(AbilityType::CLOUD_OF_DAGGERS, goblin, &goblin->getSpellslots());
    Coord coord{6, 3};
    auto actoid = cloudFactory.create(&coord);
    auto effect = dynamic_cast<Effect *>(actoid);
    effectTracker->add(std::move(effect));

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{5, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{13, 3});

    auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *goblin);
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for (AoeEffect * effect : EffectTracker::getInstance().getAoeEffects()) {
        ASSERT_TRUE(effect);
        effectToCoords[effect] = effect->getAffectedCoords();
    }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_1);
    draconic_sorcerer_lvl_1->setShortestPathsCache(shortestPaths);

    auto threat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords);
    EXPECT_NEAR(threat.back(), -2.925 * DZ_CONSTANT, 0.001);  // Just danger zone
}

TEST_F(ThreatUtilsTest, MediumToMediumPassByOneAoo) {
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    session->addCombatant(bugbear, Color::RED);

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{13, 3});
    battleMap->setCombatantCoordinates(*bugbear, Coord{6, 4});

    auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *goblin);
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for (AoeEffect * effect : EffectTracker::getInstance().getAoeEffects()) {
        ASSERT_TRUE(effect);
        effectToCoords[effect] = effect->getAffectedCoords();
    }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_1);
    draconic_sorcerer_lvl_1->setShortestPathsCache(shortestPaths);

    // battleMap->clearCaches();
    auto threat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords);
    EXPECT_NEAR(threat.back(), -5.95 - 5.95 * DZ_CONSTANT - 2.925 * DZ_CONSTANT, 0.01);

    auto disengagedThreat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords, true);
    EXPECT_NEAR(disengagedThreat.back(), -2.925 * DZ_CONSTANT - 5.95 * DZ_CONSTANT, 0.01);
}

TEST_F(ThreatUtilsTest, MediumToMediumPassByTwoAoo) {
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    session->addCombatant(bugbear, Color::RED);
    
    Combatant* bugbear2 = new Bugbear(2);
    session->addCombatant(bugbear2, Color::RED);

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{1, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{13, 3});
    battleMap->setCombatantCoordinates(*bugbear, Coord{6, 4});
    battleMap->setCombatantCoordinates(*bugbear2, Coord{7, 4});

    auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *goblin);
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for (AoeEffect * effect : EffectTracker::getInstance().getAoeEffects()) {
        ASSERT_TRUE(effect);
        effectToCoords[effect] = effect->getAffectedCoords();
    }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_1);
    draconic_sorcerer_lvl_1->setShortestPathsCache(shortestPaths);

    auto threat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords);
    EXPECT_NEAR(threat.back(), 2 * -5.95 - 2 * 5.95 * DZ_CONSTANT - 2.925 * DZ_CONSTANT, 0.001);

    auto disengagedThreat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords, true);
    EXPECT_NEAR(disengagedThreat.back(), -2.925 * DZ_CONSTANT - 2 * 5.95 * DZ_CONSTANT, 0.001);
}

TEST_F(ThreatUtilsTest, MediumSteppingAwayFromMediumAoo) {
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(goblin, Color::RED);

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{3, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{3, 2});

    auto path = battleMap->getPathToCoord(*draconic_sorcerer_lvl_1, Coord{3, 5});
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for (AoeEffect * effect : EffectTracker::getInstance().getAoeEffects()) {
        ASSERT_TRUE(effect);
        effectToCoords[effect] = effect->getAffectedCoords();
    }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_1);
    draconic_sorcerer_lvl_1->setShortestPathsCache(shortestPaths);

    auto threat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords);
    EXPECT_NEAR(threat.back(), -2.925 - 2.925 * DZ_CONSTANT, 0.001);

    auto disengagedThreat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords, true);
    EXPECT_NEAR(disengagedThreat.back(), -2.925 * DZ_CONSTANT, 0.001);
}

TEST_F(ThreatUtilsTest, LargeToMediumPassByTwoAoo) {
    draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    session->addCombatant(bugbear, Color::RED);
    
    Combatant* bugbear2 = new Bugbear(2);
    session->addCombatant(bugbear2, Color::RED);

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{1, 2});
    battleMap->setCombatantCoordinates(*goblin, Coord{13, 3});
    battleMap->setCombatantCoordinates(*bugbear, Coord{6, 4});
    battleMap->setCombatantCoordinates(*bugbear2, Coord{7, 4});

    auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *goblin);
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for (AoeEffect * effect : EffectTracker::getInstance().getAoeEffects()) {
        ASSERT_TRUE(effect);
        effectToCoords[effect] = effect->getAffectedCoords();
    }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_1);
    draconic_sorcerer_lvl_1->setShortestPathsCache(shortestPaths);

    auto threat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords);
    EXPECT_NEAR(threat.back(), 2 * -5.95 - 2 * 5.95 * DZ_CONSTANT - 2.925 * DZ_CONSTANT, 0.01);

    auto threatDisengaged = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords, true);
    EXPECT_NEAR(threatDisengaged.back(), -2.925 * DZ_CONSTANT - 2 * 5.95 * DZ_CONSTANT, 0.01);
}

TEST_F(ThreatUtilsTest, LargeSteppingAwayFromHugeAoo) {
    draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    goblin->setSize(Size::HUGE);
    
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(goblin, Color::RED);

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{1, 4});
    battleMap->setCombatantCoordinates(*goblin, Coord{1, 1});

    auto path = battleMap->getPathToCoord(*draconic_sorcerer_lvl_1, Coord{1, 5});
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for (AoeEffect * effect : EffectTracker::getInstance().getAoeEffects()) {
        ASSERT_TRUE(effect);
        effectToCoords[effect] = effect->getAffectedCoords();
    }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_1);
    draconic_sorcerer_lvl_1->setShortestPathsCache(shortestPaths);

    auto threat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords);
    EXPECT_NEAR(threat.back(), -2.925 - 2.925 * DZ_CONSTANT, 0.001);

    auto disengagedThreat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords, true);
    EXPECT_NEAR(disengagedThreat.back(), -2.925 * DZ_CONSTANT, 0.001);
}

TEST_F(ThreatUtilsTest, LargeSteppingAwayFromTwoMediumAoo) {
    draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    session->addCombatant(bugbear, Color::RED);

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{3, 3});
    battleMap->setCombatantCoordinates(*goblin, Coord{3, 2});
    battleMap->setCombatantCoordinates(*bugbear, Coord{4, 2});

    auto path = battleMap->getPathToCoord(*draconic_sorcerer_lvl_1, Coord{3, 5});
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for (AoeEffect * effect : EffectTracker::getInstance().getAoeEffects()) {
        ASSERT_TRUE(effect);
        effectToCoords[effect] = effect->getAffectedCoords();
    }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_1);
    draconic_sorcerer_lvl_1->setShortestPathsCache(shortestPaths);

    auto threat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords);
    EXPECT_NEAR(threat.back(), -2.925 - 2.925 * DZ_CONSTANT - 5.95 - 5.95 * DZ_CONSTANT, 0.001);

    auto disengagedThreat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords, true);
    EXPECT_NEAR(disengagedThreat.back(), -2.925 * DZ_CONSTANT - 5.95 * DZ_CONSTANT, 0.001);
}

TEST_F(ThreatUtilsTest, LargeToMediumPassBetweenTwoAooArriveByThird) {
    draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    session->addCombatant(bugbear, Color::RED);
    session->addCombatant(wild_heart_barbarian_lvl_5, Color::RED);

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{2, 1});
    battleMap->setCombatantCoordinates(*goblin, Coord{1, 4});
    battleMap->setCombatantCoordinates(*bugbear, Coord{4, 4});
    battleMap->setCombatantCoordinates(*wild_heart_barbarian_lvl_5, Coord{2, 8});

    auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *wild_heart_barbarian_lvl_5);
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for (AoeEffect * effect : EffectTracker::getInstance().getAoeEffects()) {
        ASSERT_TRUE(effect);
        effectToCoords[effect] = effect->getAffectedCoords();
    }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_1);
    draconic_sorcerer_lvl_1->setShortestPathsCache(shortestPaths);

    auto threat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords);
    EXPECT_NEAR(threat.back(), -2.925 - 2.925 * DZ_CONSTANT - 5.95 - 5.95 * DZ_CONSTANT - 7.149 * DZ_CONSTANT, 0.001);

    auto disengagedThreat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords, true);
    EXPECT_NEAR(disengagedThreat.back(), -2.925 * DZ_CONSTANT - 5.95 * DZ_CONSTANT - 7.149 * DZ_CONSTANT, 0.001);
}

TEST_F(ThreatUtilsTest, LargeToMediumPassBetweenTwoAooThroughAoeArriveByThird) {
    draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    session->addCombatant(bugbear, Color::RED);
    session->addCombatant(wild_heart_barbarian_lvl_5, Color::RED);

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{2, 1});
    battleMap->setCombatantCoordinates(*goblin, Coord{1, 4});
    battleMap->setCombatantCoordinates(*bugbear, Coord{4, 4});
    battleMap->setCombatantCoordinates(*wild_heart_barbarian_lvl_5, Coord{2, 8});

    auto cloudFactory = CloudOfDaggersFactory(AbilityType::CLOUD_OF_DAGGERS, goblin, &goblin->getSpellslots());
    Coord coord{2, 7};
    auto actoid = cloudFactory.create(&coord);
    auto effect = dynamic_cast<Effect *>(actoid);
    effectTracker->add(std::move(effect));

    auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *wild_heart_barbarian_lvl_5);
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for (AoeEffect * effect : EffectTracker::getInstance().getAoeEffects()) {
        ASSERT_TRUE(effect);
        effectToCoords[effect] = effect->getAffectedCoords();
    }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_1);
    draconic_sorcerer_lvl_1->setShortestPathsCache(shortestPaths);

    auto threat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords);
    EXPECT_NEAR(threat.back(), -2.925 - 2.925 * DZ_CONSTANT - 5.95 - 5.95 * DZ_CONSTANT - 20.0 - 7.149 * DZ_CONSTANT, 0.001);

    auto disengagedThreat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords, true);
    EXPECT_NEAR(disengagedThreat.back(), -20.0 - 2.925 * DZ_CONSTANT - 5.95 * DZ_CONSTANT - 7.149 * DZ_CONSTANT, 0.001);
}

TEST_F(ThreatUtilsTest, MediumGettingOutOfDangerZone) {
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(bugbear, Color::RED);

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{12, 1});
    battleMap->setCombatantCoordinates(*bugbear, Coord{14, 1});

    auto path = battleMap->getPathToCoord(*draconic_sorcerer_lvl_1, Coord{6, 1});
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for (AoeEffect * effect : EffectTracker::getInstance().getAoeEffects()) {
        ASSERT_TRUE(effect);
        effectToCoords[effect] = effect->getAffectedCoords();
    }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_1);
    draconic_sorcerer_lvl_1->setShortestPathsCache(shortestPaths);

    auto threat = accumulateThreatAlongPath(path.value(), *draconic_sorcerer_lvl_1, effectToCoords);
    EXPECT_NEAR(threat.back(), 0.0, 0.001);
}

TEST_F(ThreatUtilsTest, RangedSpellWithEnemyAdjacent) {
    battleMap->buildBaseAdjacencyMatrix();
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(bugbear, Color::RED);

    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{3, 14});
    battleMap->setCombatantCoordinates(*bugbear, Coord{4, 13});

    auto fireboltFactory = FireboltFactory(6, AbilityType::FIREBOLT, draconic_sorcerer_lvl_1, &draconic_sorcerer_lvl_1->getSpellslots());
    auto firebolt = fireboltFactory.create(bugbear);
    auto threatEnemyAdjacent = dynamic_cast<BasicThreat *>(firebolt)->calculateThreat({});

    battleMap->moveCombatant(*draconic_sorcerer_lvl_1, Coord{2, 14});
    // firebolt->clearCache();
    auto threatNoEnemyAdjacent = dynamic_cast<BasicThreat *>(firebolt)->calculateThreat({});

    EXPECT_GT(threatNoEnemyAdjacent, threatEnemyAdjacent);
}

TEST_F(ThreatUtilsTest, RangedAttackWithEnemyAdjacent) {
    battleMap->buildBaseAdjacencyMatrix();
    session->addCombatant(goblin, Color::BLUE);
    session->addCombatant(bugbear, Color::RED);

    battleMap->setCombatantCoordinates(*goblin, Coord{3, 14});
    battleMap->setCombatantCoordinates(*bugbear, Coord{4, 13});

    ActoidFactory *shortbowAttack = goblin->getActionFactory(AbilityType::RANGED_ATTACK);
    auto shortbowAtBugbear = shortbowAttack->create(bugbear);
    auto threatEnemyAdjacent = dynamic_cast<BasicThreat *>(shortbowAtBugbear)->calculateThreat({});

    battleMap->moveCombatant(*goblin, Coord{2, 14});
    auto threatNoEnemyAdjacent = dynamic_cast<BasicThreat *>(shortbowAtBugbear)->calculateThreat({});

    EXPECT_GT(threatNoEnemyAdjacent, threatEnemyAdjacent);
}

/**
 *  Simple scenario with two combatants starting adjacent. We test that Misty Step lets us avoid the AoO.
    It tests calc_threat_for_path_with_misty_step as well as decode_ms_path_to_actions.
 */
TEST_F(ThreatUtilsTest, CalcThreatForPathWithMistyStepScenario1) {
    session->addCombatant(draconic_sorcerer_lvl_5, Color::BLUE);
    session->addCombatant(bugbear, Color::RED);

    battleMap->buildBaseAdjacencyMatrix();
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_5, Coord{5, 5});
    battleMap->setCombatantCoordinates(*bugbear, Coord{5, 6});

    auto path = battleMap->getPathToCoord(*draconic_sorcerer_lvl_5, Coord{0, 14});
    ASSERT_TRUE(path.has_value());
    std::unordered_map<AoeEffect *, CoordVector> effectToCoords;
    for(AoeEffect *effect : effectTracker->getAoeEffects())
      {
        effectToCoords[effect] = effect->getAffectedCoords();
      }

    auto [distances, shortestPaths] = battleMap->calcDijkstra(*draconic_sorcerer_lvl_5);
    draconic_sorcerer_lvl_5->setShortestPathsCache(shortestPaths);

    auto [threat, maxThreatPath] = calcThreatForPathWithMistyStep(path.value(), *draconic_sorcerer_lvl_5, effectToCoords);
    EXPECT_DOUBLE_EQ(threat[0], 0.0);

    std::vector<Actoid *> actoids;
    std::shared_ptr<ActoidFactory> msFactory = std::make_shared<MistyStepFactory>(draconic_sorcerer_lvl_5, &draconic_sorcerer_lvl_5->getSpellslots());

    EXPECT_EQ(actoids.size(), 6);
    EXPECT_TRUE(dynamic_cast<MovementIncrement *>(actoids[0]) != nullptr);
    EXPECT_TRUE(dynamic_cast<MistyStep *>(actoids[1]) != nullptr);
    EXPECT_TRUE(dynamic_cast<MovementIncrement *>(actoids[2]) != nullptr);
    EXPECT_TRUE(dynamic_cast<MovementIncrement *>(actoids[3]) != nullptr);
    EXPECT_TRUE(dynamic_cast<MovementIncrement *>(actoids[4]) != nullptr);
    EXPECT_TRUE(dynamic_cast<MovementIncrement *>(actoids[5]) != nullptr);

    // Clean up actions
    actoids.clear();
}


}
