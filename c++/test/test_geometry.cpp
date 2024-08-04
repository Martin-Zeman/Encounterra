#include <gtest/gtest.h>
#include "core/battle_map.hpp"
#include "core/misc.hpp"
#include "core/geometry.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "combatants/goblin.hpp"
#include "combatants/draconic_sorcerer_lvl_1.hpp"
#include <set>
#include <algorithm>
#include <memory>

using namespace enc;

class GeometryTest : public ::testing::Test
{
protected:
  BattleMap *battle_map;
  std::unique_ptr<Goblin> test_goblin;
  std::unique_ptr<DraconicSorcererLvl1> test_draconic_sorcerer_lvl_1;

  void SetUp() override
  {
    BattleMap::resetInstance(); // Reset the singleton instance before each test
    battle_map = &BattleMap::getInstance();
    test_goblin = std::make_unique<Goblin>(1);
    test_draconic_sorcerer_lvl_1 = std::make_unique<DraconicSorcererLvl1>(1);
  }
};

TEST_F(GeometryTest, HopDistanceDiagonalMedium) {
    battle_map->setCombatantCoordinates(*test_draconic_sorcerer_lvl_1, Coord{0, 0});
    battle_map->setCombatantCoordinates(*test_goblin, Coord{4, 4});

    auto draconic_sorcerer_coords = battle_map->getCombatantCoordinates(*test_draconic_sorcerer_lvl_1);
    auto goblin_coords = battle_map->getCombatantCoordinates(*test_goblin);

    // EXPECT_EQ(battle_map->getHopDistanceCombatants(*test_draconic_sorcerer_lvl_1, *test_goblin), 4) 
    //     << "Incorrect distance between two large combatants";
    EXPECT_EQ(getHopDistanceCoords(draconic_sorcerer_coords, goblin_coords), 4) 
        << "Incorrect distance between two large combatants";
}

TEST_F(GeometryTest, HopDistanceDiagonalLarge) {
    test_draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    test_goblin->setSize(Size::LARGE);
    battle_map->setCombatantCoordinates(*test_draconic_sorcerer_lvl_1, Coord{0, 0});
    battle_map->setCombatantCoordinates(*test_goblin, Coord{4, 4});

    auto draconic_sorcerer_coords = battle_map->getCombatantCoordinates(*test_draconic_sorcerer_lvl_1);
    auto goblin_coords = battle_map->getCombatantCoordinates(*test_goblin);

    // EXPECT_EQ(battle_map->getHopDistanceCombatants(*test_draconic_sorcerer_lvl_1, *test_goblin), 3) 
    //     << "Incorrect distance between two large combatants";
    EXPECT_EQ(getHopDistanceCoords(draconic_sorcerer_coords, goblin_coords), 3) 
        << "Incorrect distance between two large combatants";
}

TEST_F(GeometryTest, HopDistanceSameY) {
    test_draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    test_goblin->setSize(Size::LARGE);
    battle_map->setCombatantCoordinates(*test_draconic_sorcerer_lvl_1, Coord{0, 0});
    battle_map->setCombatantCoordinates(*test_goblin, Coord{6, 0});

    auto draconic_sorcerer_coords = battle_map->getCombatantCoordinates(*test_draconic_sorcerer_lvl_1);
    auto goblin_coords = battle_map->getCombatantCoordinates(*test_goblin);

    // EXPECT_EQ(battle_map->getHopDistanceCombatants(*test_draconic_sorcerer_lvl_1, *test_goblin), 5) 
    //     << "Incorrect distance between two large combatants";
    EXPECT_EQ(getHopDistanceCoords(draconic_sorcerer_coords, goblin_coords), 5) 
        << "Incorrect distance between two large combatants";
}

TEST_F(GeometryTest, HopDistanceSameX) {
    test_draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    test_goblin->setSize(Size::LARGE);
    battle_map->setCombatantCoordinates(*test_draconic_sorcerer_lvl_1, Coord{0, 0});
    battle_map->setCombatantCoordinates(*test_goblin, Coord{0, 4});

    auto draconic_sorcerer_coords = battle_map->getCombatantCoordinates(*test_draconic_sorcerer_lvl_1);
    auto goblin_coords = battle_map->getCombatantCoordinates(*test_goblin);

    // EXPECT_EQ(battle_map->getHopDistanceCombatants(*test_draconic_sorcerer_lvl_1, *gotest_goblinblin), 3) 
    //     << "Incorrect distance between two large combatants";
    EXPECT_EQ(getHopDistanceCoords(draconic_sorcerer_coords, goblin_coords), 3) 
        << "Incorrect distance between two large combatants";
}

TEST_F(GeometryTest, HopDistanceRandom) {
    test_draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    test_goblin->setSize(Size::LARGE);
    battle_map->setCombatantCoordinates(*test_draconic_sorcerer_lvl_1, Coord{0, 0});
    battle_map->setCombatantCoordinates(*test_goblin, Coord{3, 5});

    auto draconic_sorcerer_coords = battle_map->getCombatantCoordinates(*test_draconic_sorcerer_lvl_1);
    auto goblin_coords = battle_map->getCombatantCoordinates(*test_goblin);

    // EXPECT_EQ(battle_map->getHopDistanceCombatants(*test_draconic_sorcerer_lvl_1, *test_goblin), 4) 
    //     << "Incorrect distance between two large combatants";
    EXPECT_EQ(getHopDistanceCoords(draconic_sorcerer_coords, goblin_coords), 4) 
        << "Incorrect distance between two large combatants";
}
