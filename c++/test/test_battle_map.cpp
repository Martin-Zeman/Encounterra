#include <gtest/gtest.h>
#include "core/battle_map.hpp"
#include "core/misc.hpp"
#include "core/geometry.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "combatants/goblin.hpp"
#include <set>
#include <algorithm>
#include <memory>

using namespace enc;

class BattleMapTest : public ::testing::Test
{
protected:
  BattleMap *battle_map;
  std::unique_ptr<Goblin> test_goblin;

  void SetUp() override
  {
    BattleMap::resetInstance(); // Reset the singleton instance before each test
    battle_map = &BattleMap::getInstance();
    test_goblin = std::make_unique<Goblin>(1);
  }
};

TEST_F(BattleMapTest, GetFreeCoordinatesInHopRangeMedium)
{
  battle_map->setCombatantCoordinates(*test_goblin, Coord({5, 7}));
  Coord coords{5, 7};

  auto adj = battle_map->getFreeCoordsInHopRange(Coords{{5, 7}}, blaze::DynamicVector<double>(), static_cast<int>(Size::MEDIUM), 1, -1);

  std::set<Coord> expected_adj = {{4, 7}, {6, 7}, {4, 8}, {5, 8}, {6, 8}, {4, 6}, {5, 6}, {6, 6}};
  std::set<Coord> actual_adj(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);

  // Test including the combatant's own coord
  adj = battle_map->getFreeCoordsInHopRange(Coords{{5, 7}}, blaze::DynamicVector<double>(), static_cast<int>(Size::MEDIUM), 1, test_goblin->_id);

  expected_adj = {{4, 7}, {5, 7}, {6, 7}, {4, 8}, {5, 8}, {6, 8}, {4, 6}, {5, 6}, {6, 6}};
  actual_adj = std::set<Coord>(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);
}

TEST_F(BattleMapTest, GetFreeCoordinatesInHopRangeLarge)
{
  test_goblin->setSize(Size::LARGE);
  battle_map->setCombatantCoordinates(*test_goblin, Coord({5, 7}));
  auto large_goblin_coords = battle_map->getCombatantCoordinates(*test_goblin);

  auto adj = battle_map->getFreeCoordsInHopRange(large_goblin_coords, blaze::DynamicVector<double>(), static_cast<int>(Size::MEDIUM), 1, -1);

  std::set<Coord> expected_adj = {{4, 6}, {4, 7}, {4, 8}, {4, 9}, {5, 6}, {5, 9}, {6, 6}, {6, 9}, {7, 6}, {7, 7}, {7, 8}, {7, 9}};
  std::set<Coord> actual_adj(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);

  // Test including the combatant's own coord
  adj = battle_map->getFreeCoordsInHopRange(large_goblin_coords, blaze::DynamicVector<double>(), static_cast<int>(Size::MEDIUM), 1, test_goblin->_id);

  expected_adj = {{4, 6}, {5, 7}, {6, 7}, {5, 8}, {6, 8}, {4, 7}, {4, 8}, {4, 9}, {5, 6}, {5, 9}, {6, 6}, {6, 9}, {7, 6}, {7, 7}, {7, 8}, {7, 9}};
  actual_adj = std::set<Coord>(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);
}

TEST_F(BattleMapTest, GetFreeCoordinatesInHopRangeLargeInACorner)
{
  test_goblin->setSize(Size::LARGE);
  battle_map->setCombatantCoordinates(*test_goblin, Coord({0, 1}));
  auto large_goblin_coords = battle_map->getCombatantCoordinates(*test_goblin);

  auto adj = battle_map->getFreeCoordsInHopRange(large_goblin_coords, blaze::DynamicVector<double>(), static_cast<int>(Size::MEDIUM), 1, -1);

  std::set<Coord> expected_adj = {{0, 0}, {1, 0}, {2, 0}, {2, 1}, {2, 2}, {0, 3}, {1, 3}, {2, 3}};
  std::set<Coord> actual_adj(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);
}

TEST_F(BattleMapTest, GetFreeCoordinatesInHopRangeHugeWithTerrain)
{
  test_goblin->setSize(Size::HUGE);
  battle_map->setCombatantCoordinates(*test_goblin, Coord({8, 2}));
  battle_map->placeTerrain(Coord{7, 3}, Terrain::IMPASSABLE_TERRAIN);
  auto huge_goblin_coords = battle_map->getCombatantCoordinates(*test_goblin);

  auto adj = battle_map->getFreeCoordsInHopRange(huge_goblin_coords, blaze::DynamicVector<double>(), static_cast<int>(Size::MEDIUM), 1, -1);

  std::set<Coord> expected_adj
    = {{7, 1}, {7, 2}, {7, 4}, {7, 5}, {8, 1}, {8, 5}, {9, 1}, {9, 5}, {10, 1}, {10, 5}, {11, 1}, {11, 2}, {11, 3}, {11, 4}, {11, 5}};
  std::set<Coord> actual_adj(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);

  // Test including the combatant's own coord
  adj = battle_map->getFreeCoordsInHopRange(huge_goblin_coords, blaze::DynamicVector<double>(), static_cast<int>(Size::MEDIUM), 1, test_goblin->_id);

  expected_adj = {{7, 1}, {7, 2},  {7, 4}, {7, 5}, {8, 1}, {8, 2},  {9, 2},  {10, 2}, {8, 3},  {9, 3},  {10, 3}, {8, 4},
                  {9, 4}, {10, 4}, {8, 5}, {9, 1}, {9, 5}, {10, 1}, {10, 5}, {11, 1}, {11, 2}, {11, 3}, {11, 4}, {11, 5}};
  actual_adj = std::set<Coord>(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);
}

TEST_F(BattleMapTest, GetFreeCoordsInCartesianRangeMedium) {
    battle_map->setCombatantCoordinates(*test_goblin, Coord({5, 7}));

    auto coords = battle_map->getCombatantCoordinates(*test_goblin);
    auto free_coords = battle_map->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), static_cast<int>(Size::MEDIUM), 1, -1);

    std::set<Coord> expected_free_coords = {{4, 7}, {6, 7}, {5, 8}, {5, 6}};
    std::set<Coord> actual_free_coords(free_coords.begin(), free_coords.end());
    EXPECT_EQ(actual_free_coords, expected_free_coords);

    free_coords = battle_map->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), static_cast<int>(Size::MEDIUM), 1, test_goblin->_id);
    expected_free_coords = {{4, 7}, {5, 7}, {6, 7}, {5, 8}, {5, 6}};
    actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
    EXPECT_EQ(actual_free_coords, expected_free_coords);

    // battle_map->moveCombatant(*test_goblin, Coord({8, 13}));
    // coords = battle_map->getCombatantCoordinates(*test_goblin);
    // free_coords = battle_map->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), static_cast<int>(Size::MEDIUM), 2, -1);
    // expected_free_coords = {{6, 13}, {7, 13}, {9, 13}, {10, 13}, {7, 14}, {8, 14}, {9, 14}, {7, 12}, {8, 12}, {9, 12}, {8, 11}};
    // actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
    // EXPECT_EQ(actual_free_coords, expected_free_coords);

    // free_coords = battle_map->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), static_cast<int>(Size::MEDIUM), 2, test_goblin->_id);
    // expected_free_coords = {{6, 13}, {7, 13}, {8, 13}, {9, 13}, {10, 13}, {7, 14}, {8, 14}, {9, 14}, {7, 12}, {8, 12}, {9, 12}, {8, 11}};
    // actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
    // EXPECT_EQ(actual_free_coords, expected_free_coords);

    // battle_map->moveCombatant(*test_goblin, Coord({5, 5}));
    // coords = battle_map->getCombatantCoordinates(*test_goblin);
    // free_coords = battle_map->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), static_cast<int>(Size::MEDIUM), 4, -1);
    // EXPECT_FALSE(free_coords.count({1, 1}) || free_coords.count({2, 1}) || free_coords.count({3, 1}) || free_coords.count({4, 1}) || free_coords.count({6, 1}));
    // EXPECT_FALSE(free_coords.count({7, 1}) || free_coords.count({8, 1}));
    // EXPECT_FALSE(free_coords.count({1, 2}) || free_coords.count({1, 3}) || free_coords.count({1, 4}) || free_coords.count({1, 6}) || free_coords.count({1, 7}));
    // EXPECT_FALSE(free_coords.count({1, 8}) || free_coords.count({8, 8}));
    // EXPECT_FALSE(free_coords.count({2, 8}) || free_coords.count({8, 8}) || free_coords.count({9, 8}));
    // EXPECT_TRUE(free_coords.count({9, 5}) && free_coords.count({1, 5}) && free_coords.count({5, 1}) && free_coords.count({5, 9}));
    
    // free_coords = battle_map->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), static_cast<int>(Size::MEDIUM), 4, test_goblin->_id);
    // EXPECT_TRUE(free_coords.count({5, 5}));
}

TEST_F(BattleMapTest, GetFreeCoordsInCartesianRangeLarge) {
    test_goblin->setSize(Size::LARGE);
    battle_map->setCombatantCoordinates(*test_goblin, Coord({2, 2}));

    auto coords = battle_map->getCombatantCoordinates(*test_goblin);
    auto free_coords = battle_map->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), static_cast<int>(Size::LARGE), 1, -1);

    std::set<Coord> expected_free_coords = {{2, 1}, {3, 1}, {1, 2}, {4, 2}, {1, 3}, {4, 3}, {2, 4}, {3, 4}};
    std::set<Coord> actual_free_coords(free_coords.begin(), free_coords.end());
    EXPECT_EQ(actual_free_coords, expected_free_coords);

    free_coords = battle_map->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), static_cast<int>(Size::LARGE), 1, test_goblin->_id);
    expected_free_coords = {{2, 1}, {2, 2}, {3, 2}, {2, 3}, {3, 3}, {3, 1}, {1, 2}, {4, 2}, {1, 3}, {4, 3}, {2, 4}, {3, 4}};
    actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
    EXPECT_EQ(actual_free_coords, expected_free_coords);

    // battle_map->moveCombatant(*test_goblin, Coord({6, 8}));
    // coords = battle_map->getCombatantCoordinates(*test_goblin);
    // free_coords = battle_map->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), static_cast<int>(Size::LARGE), 2, -1);
    // expected_free_coords = {{6, 6}, {7, 6}, {5, 7}, {6, 7}, {7, 7}, {8, 7}, {4, 8}, {5, 8}, {8, 8}, {9, 8}, {4, 9}, {5, 9}, {8, 9}, {9, 9}, {5, 10}, {6, 10}, {7, 10}, {8, 10}, {6, 11}, {7, 11}};
    // actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
    // EXPECT_EQ(actual_free_coords, expected_free_coords);

    // free_coords = battle_map->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), static_cast<int>(Size::LARGE), 2, test_goblin->_id);
    // expected_free_coords = {{6, 6}, {6, 8}, {7, 8}, {6, 9}, {7, 9}, {7, 6}, {5, 7}, {6, 7}, {7, 7}, {8, 7}, {4, 8}, {5, 8}, {8, 8}, {9, 8}, {4, 9}, {5, 9}, {8, 9}, {9, 9}, {5, 10}, {6, 10}, {7, 10}, {8, 10}, {6, 11}, {7, 11}};
    // actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
    // EXPECT_EQ(actual_free_coords, expected_free_coords);
}