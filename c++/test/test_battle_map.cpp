#include <gtest/gtest.h>
#include "core/battle_map.hpp"
#include "core/misc.hpp"
#include "core/geometry.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "core/teams.hpp"
#include "core/session.hpp"
#include "spells/spell_stats.hpp"
#include "combatants/goblin.hpp"
#include "combatants/draconic_sorcerer_lvl_1.hpp"
#include "combatants/bugbear.hpp"
#include "combatants/stone_giant.hpp"
#include "combatants/wild_heart_barbarian_lvl_3.hpp"
#include "combatants/battlemaster_fighter_lvl_5.hpp"
#include "combatants/giant_toad.hpp"
#include "combatants/green_dragon_wyrmling.hpp"
#include "combatants/ogre.hpp"
#include <set>
#include <algorithm>
#include <memory>
#include <chrono>

using namespace enc;

class BattleMapTest : public ::testing::Test
{
protected:
  BattleMap *battleMap;
  Teams *teams;
  Session *session;
  Goblin* goblin;
  Bugbear* bugbear;
  DraconicSorcererLvl1* draconic_sorcerer_lvl_1;
  WildHeartBarbarianLvl3* wild_heart_barbarian;
  BattlemasterFighterLvl5* battlemaster_fighter_lvl_5;
  StoneGiant* stone_giant;
  Ogre* ogre;
  GiantToad* giant_toad;
  GreenDragonWyrmling* green_dragon_wyrmling;

  void SetUp() override
  {
    BattleMap::resetInstance(); // Reset the singleton instance before each test
    battleMap = &BattleMap::getInstance();
    Teams::resetInstance();
    teams = &Teams::getInstance();
    session = new Session();
    goblin = new Goblin(1);
    draconic_sorcerer_lvl_1 = new DraconicSorcererLvl1(1);
    bugbear = new Bugbear(1);
    wild_heart_barbarian = new WildHeartBarbarianLvl3(1);
    stone_giant = new StoneGiant(1);
    battlemaster_fighter_lvl_5 = new BattlemasterFighterLvl5(1);
    ogre = new Ogre(1);
    giant_toad = new GiantToad(1);
    green_dragon_wyrmling = new GreenDragonWyrmling(1);
  }
};

TEST_F(BattleMapTest, GetFreeCoordinatesInHopRangeMedium)
{
  battleMap->setCombatantCoordinates(*goblin, Coord({5, 7}));
  Coord coords{5, 7};

  auto adj = battleMap->getFreeCoordsInHopRange(Coords{{5, 7}}, blaze::DynamicVector<double>(), Size::MEDIUM, 1, -1);

  std::set<Coord> expected_adj = {{4, 7}, {6, 7}, {4, 8}, {5, 8}, {6, 8}, {4, 6}, {5, 6}, {6, 6}};
  std::set<Coord> actual_adj(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);

  // Test including the combatant's own coord
  adj = battleMap->getFreeCoordsInHopRange(Coords{{5, 7}}, blaze::DynamicVector<double>(), Size::MEDIUM, 1, goblin->_instanceId);

  expected_adj = {{4, 7}, {5, 7}, {6, 7}, {4, 8}, {5, 8}, {6, 8}, {4, 6}, {5, 6}, {6, 6}};
  actual_adj = std::set<Coord>(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);
}

TEST_F(BattleMapTest, GetFreeCoordinatesInHopRangeLarge)
{
  goblin->setSize(Size::LARGE);
  battleMap->setCombatantCoordinates(*goblin, Coord({5, 7}));
  auto large_goblin_coords = battleMap->getCombatantCoordinates(*goblin);

  auto adj = battleMap->getFreeCoordsInHopRange(large_goblin_coords, blaze::DynamicVector<double>(), Size::MEDIUM, 1, -1);

  std::set<Coord> expected_adj = {{4, 6}, {4, 7}, {4, 8}, {4, 9}, {5, 6}, {5, 9}, {6, 6}, {6, 9}, {7, 6}, {7, 7}, {7, 8}, {7, 9}};
  std::set<Coord> actual_adj(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);

  // Test including the combatant's own coord
  adj = battleMap->getFreeCoordsInHopRange(large_goblin_coords, blaze::DynamicVector<double>(), Size::MEDIUM, 1, goblin->_instanceId);

  expected_adj = {{4, 6}, {5, 7}, {6, 7}, {5, 8}, {6, 8}, {4, 7}, {4, 8}, {4, 9}, {5, 6}, {5, 9}, {6, 6}, {6, 9}, {7, 6}, {7, 7}, {7, 8}, {7, 9}};
  actual_adj = std::set<Coord>(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);
}

TEST_F(BattleMapTest, GetFreeCoordinatesInHopRangeLargeInACorner)
{
  goblin->setSize(Size::LARGE);
  battleMap->setCombatantCoordinates(*goblin, Coord({0, 1}));
  auto large_goblin_coords = battleMap->getCombatantCoordinates(*goblin);

  auto adj = battleMap->getFreeCoordsInHopRange(large_goblin_coords, blaze::DynamicVector<double>(), Size::MEDIUM, 1, -1);

  std::set<Coord> expected_adj = {{0, 0}, {1, 0}, {2, 0}, {2, 1}, {2, 2}, {0, 3}, {1, 3}, {2, 3}};
  std::set<Coord> actual_adj(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);
}

TEST_F(BattleMapTest, GetFreeCoordinatesInHopRangeHugeWithTerrain)
{
  goblin->setSize(Size::HUGE);
  battleMap->setCombatantCoordinates(*goblin, Coord({8, 2}));
  battleMap->placeTerrain(Coord{7, 3}, Terrain::IMPASSABLE_TERRAIN);
  auto huge_goblin_coords = battleMap->getCombatantCoordinates(*goblin);

  auto adj = battleMap->getFreeCoordsInHopRange(huge_goblin_coords, blaze::DynamicVector<double>(), Size::MEDIUM, 1, -1);

  std::set<Coord> expected_adj
    = {{7, 1}, {7, 2}, {7, 4}, {7, 5}, {8, 1}, {8, 5}, {9, 1}, {9, 5}, {10, 1}, {10, 5}, {11, 1}, {11, 2}, {11, 3}, {11, 4}, {11, 5}};
  std::set<Coord> actual_adj(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);

  // Test including the combatant's own coord
  adj = battleMap->getFreeCoordsInHopRange(huge_goblin_coords, blaze::DynamicVector<double>(), Size::MEDIUM, 1, goblin->_instanceId);

  expected_adj = {{7, 1}, {7, 2},  {7, 4}, {7, 5}, {8, 1}, {8, 2},  {9, 2},  {10, 2}, {8, 3},  {9, 3},  {10, 3}, {8, 4},
                  {9, 4}, {10, 4}, {8, 5}, {9, 1}, {9, 5}, {10, 1}, {10, 5}, {11, 1}, {11, 2}, {11, 3}, {11, 4}, {11, 5}};
  actual_adj = std::set<Coord>(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);
}

TEST_F(BattleMapTest, GetFreeCoordsInCartesianRangeMedium)
{
  battleMap->setCombatantCoordinates(*goblin, Coord({5, 7}));

  auto coords = battleMap->getCombatantCoordinates(*goblin);
  auto free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 1, -1);

  std::set<Coord> expected_free_coords = {{4, 7}, {6, 7}, {5, 8}, {5, 6}};
  std::set<Coord> actual_free_coords(free_coords.begin(), free_coords.end());
  EXPECT_EQ(actual_free_coords, expected_free_coords);

  free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 1, goblin->_instanceId);
  expected_free_coords = {{4, 7}, {5, 7}, {6, 7}, {5, 8}, {5, 6}};
  actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
  EXPECT_EQ(actual_free_coords, expected_free_coords);

  battleMap->moveCombatant(*goblin, Coord({8, 13}));
  coords = battleMap->getCombatantCoordinates(*goblin);
  free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 2, -1);
  expected_free_coords = {{6, 13}, {7, 13}, {9, 13}, {10, 13}, {7, 14}, {8, 14}, {9, 14}, {7, 12}, {8, 12}, {9, 12}, {8, 11}};
  actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
  EXPECT_EQ(actual_free_coords, expected_free_coords);

  free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 2, goblin->_instanceId);
  expected_free_coords = {{6, 13}, {7, 13}, {8, 13}, {9, 13}, {10, 13}, {7, 14}, {8, 14}, {9, 14}, {7, 12}, {8, 12}, {9, 12}, {8, 11}};
  actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
  EXPECT_EQ(actual_free_coords, expected_free_coords);

    battleMap->moveCombatant(*goblin, Coord({8, 13}));
    coords = battleMap->getCombatantCoordinates(*goblin);
    free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 2, -1);
    expected_free_coords = {{6, 13}, {7, 13}, {9, 13}, {10, 13}, {7, 14}, {8, 14}, {9, 14}, {7, 12}, {8, 12}, {9, 12}, {8, 11}};
    actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
    EXPECT_EQ(actual_free_coords, expected_free_coords);

    free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 2, goblin->_instanceId);
    expected_free_coords = {{6, 13}, {7, 13}, {8, 13}, {9, 13}, {10, 13}, {7, 14}, {8, 14}, {9, 14}, {7, 12}, {8, 12}, {9, 12}, {8, 11}};
    actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
    EXPECT_EQ(actual_free_coords, expected_free_coords);

    battleMap->moveCombatant(*goblin, Coord({5, 5}));
    coords = battleMap->getCombatantCoordinates(*goblin);
    free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 4, -1);
    
    std::vector<Coord> not_expected = {{1, 1}, {2, 1}, {3, 1}, {4, 1}, {6, 1}, {7, 1}, {8, 1},
                                       {1, 2}, {1, 3}, {1, 4}, {1, 6}, {1, 7}, {1, 8}, {8, 8},
                                       {2, 8}, {9, 8}};
    for (const auto& coord : not_expected) {
        EXPECT_EQ(std::find(free_coords.begin(), free_coords.end(), coord), free_coords.end())
            << "Coordinate " << coord[0] << "," << coord[1] << " should not be in free_coords";
    }

    std::vector<Coord> expected = {{9, 5}, {1, 5}, {5, 1}, {5, 9}};
    for (const auto& coord : expected) {
        EXPECT_NE(std::find(free_coords.begin(), free_coords.end(), coord), free_coords.end())
            << "Coordinate " << coord[0] << "," << coord[1] << " should be in free_coords";
    }

    free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 4, goblin->_instanceId);
    EXPECT_NE(std::find(free_coords.begin(), free_coords.end(), Coord({5, 5})), free_coords.end())
        << "Coordinate 5,5 should be in free_coords";
}

TEST_F(BattleMapTest, GetFreeCoordsInCartesianRangeLarge)
{
  goblin->setSize(Size::LARGE);
  battleMap->setCombatantCoordinates(*goblin, Coord({2, 2}));

  auto coords = battleMap->getCombatantCoordinates(*goblin);
  auto free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::LARGE, 1, -1);

  std::set<Coord> expected_free_coords = {{2, 1}, {3, 1}, {1, 2}, {4, 2}, {1, 3}, {4, 3}, {2, 4}, {3, 4}};
  std::set<Coord> actual_free_coords(free_coords.begin(), free_coords.end());
  EXPECT_EQ(actual_free_coords, expected_free_coords);

  free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::LARGE, 1, goblin->_instanceId);
  expected_free_coords = {{2, 1}, {2, 2}, {3, 2}, {2, 3}, {3, 3}, {3, 1}, {1, 2}, {4, 2}, {1, 3}, {4, 3}, {2, 4}, {3, 4}};
  actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
  EXPECT_EQ(actual_free_coords, expected_free_coords);

  battleMap->moveCombatant(*goblin, Coord({6, 8}));
  coords = battleMap->getCombatantCoordinates(*goblin);
  free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::LARGE, 2, -1);
  expected_free_coords = {{6, 6}, {7, 6}, {5, 7}, {6, 7}, {7, 7},  {8, 7},  {4, 8},  {5, 8},  {8, 8},  {9, 8},
                          {4, 9}, {5, 9}, {8, 9}, {9, 9}, {5, 10}, {6, 10}, {7, 10}, {8, 10}, {6, 11}, {7, 11}};
  actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
  EXPECT_EQ(actual_free_coords, expected_free_coords);

  free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::LARGE, 2, goblin->_instanceId);
  expected_free_coords = {{6, 6}, {6, 8}, {7, 8}, {6, 9}, {7, 9}, {7, 6}, {5, 7},  {6, 7},  {7, 7},  {8, 7},  {4, 8},  {5, 8},
                          {8, 8}, {9, 8}, {4, 9}, {5, 9}, {8, 9}, {9, 9}, {5, 10}, {6, 10}, {7, 10}, {8, 10}, {6, 11}, {7, 11}};
  actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
  EXPECT_EQ(actual_free_coords, expected_free_coords);
}

TEST_F(BattleMapTest, MoveCombatantByIncrementMedium)
{
  Coord initialPos{0, 1};
  battleMap->setCombatantCoordinates(*goblin, initialPos);

  auto coords = battleMap->getCombatantCoordinates(*goblin);
  ASSERT_EQ(coords.get().size(), 1);
  EXPECT_EQ(coords.get()[0], initialPos);

  Coord increment{1, 1};
  battleMap->moveCombatantByIncrement(*goblin, increment);

  coords = battleMap->getCombatantCoordinates(*goblin);
  ASSERT_EQ(coords.get().size(), 1);
  Coord expectedCoord{1, 2};
  EXPECT_EQ(coords.get()[0], expectedCoord);
}

TEST_F(BattleMapTest, MoveCombatantByIncrementMediumInvalid)
{
  Coord initialPos{0, 1};
  battleMap->setCombatantCoordinates(*goblin, initialPos);

  auto coords = battleMap->getCombatantCoordinates(*goblin);
  ASSERT_EQ(coords.get().size(), 1);
  EXPECT_EQ(coords.get()[0], initialPos);

  Coord invalidIncrement{-1, 0};
  EXPECT_THROW(battleMap->moveCombatantByIncrement(*goblin, invalidIncrement), std::out_of_range);
}

TEST_F(BattleMapTest, MoveCombatantByIncrementLarge)
{
  goblin->setSize(Size::LARGE);

  Coord initialPos{0, 1};
  battleMap->setCombatantCoordinates(*goblin, initialPos);

  auto coords = battleMap->getCombatantCoordinates(*goblin);
  ASSERT_EQ(coords.get().size(), 4);
  std::vector<Coord> expectedInitialPos{{0, 1}, {0, 2}, {1, 1}, {1, 2}};
  EXPECT_EQ(coords.get(), expectedInitialPos);

  Coord increment{1, 1};
  battleMap->moveCombatantByIncrement(*goblin, increment);

  coords = battleMap->getCombatantCoordinates(*goblin);
  ASSERT_EQ(coords.get().size(), 4);
  std::vector<Coord> expectedFinalPos{{1, 2}, {1, 3}, {2, 2}, {2, 3}};
  EXPECT_EQ(coords.get(), expectedFinalPos);
}

TEST_F(BattleMapTest, MoveCombatantMedium)
{
  Coord initialPos{0, 1};
  battleMap->setCombatantCoordinates(*goblin, initialPos);

  auto coords = battleMap->getCombatantCoordinates(*goblin);
  ASSERT_EQ(coords.get().size(), 1);
  EXPECT_EQ(coords.get()[0], initialPos);

  Coord newPos{14, 14};
  battleMap->moveCombatant(*goblin, newPos);

  coords = battleMap->getCombatantCoordinates(*goblin);
  ASSERT_EQ(coords.get().size(), 1);
  EXPECT_EQ(coords.get()[0], newPos);
}

TEST_F(BattleMapTest, MoveCombatantMediumInvalid)
{
  Coord initialPos{0, 1};
  battleMap->setCombatantCoordinates(*goblin, initialPos);

  auto coords = battleMap->getCombatantCoordinates(*goblin);
  ASSERT_EQ(coords.get().size(), 1);
  EXPECT_EQ(coords.get()[0], initialPos);

  Coord invalidPos{15, 15};
  EXPECT_THROW(battleMap->moveCombatant(*goblin, invalidPos), std::out_of_range);
}

TEST_F(BattleMapTest, MoveCombatantLarge)
{
  goblin->setSize(Size::LARGE);

  Coord initialPos{0, 1};
  battleMap->setCombatantCoordinates(*goblin, initialPos);

  auto coords = battleMap->getCombatantCoordinates(*goblin);
  ASSERT_EQ(coords.get().size(), 4);
  std::vector<Coord> expectedInitialPos{{0, 1}, {0, 2}, {1, 1}, {1, 2}};
  EXPECT_EQ(coords.get(), expectedInitialPos);

  Coord newPos{9, 9};
  battleMap->moveCombatant(*goblin, newPos);

  coords = battleMap->getCombatantCoordinates(*goblin);
  ASSERT_EQ(coords.get().size(), 4);
  std::vector<Coord> expectedFinalPos{{9, 9}, {9, 10}, {10, 9}, {10, 10}};
  EXPECT_EQ(coords.get(), expectedFinalPos);
}

TEST_F(BattleMapTest, SimplePathTest)
{
  const int N = battleMap->getGridSize();
  battleMap->placeTerrain(Coord{5, 5}, Terrain::IMPASSABLE_TERRAIN);
  battleMap->placeTerrain(Coord{5, 6}, Terrain::IMPASSABLE_TERRAIN);
  battleMap->setCombatantCoordinates(*goblin, Coord({0, 0}));
  battleMap->buildBaseAdjacencyMatrix();
  auto result = battleMap->calcDijkstra(*goblin);

  // Check distance to adjacent cells
  EXPECT_EQ(result.dist[1], 1);
  EXPECT_EQ(result.dist[N], 1);

  // Check distance to a cell blocked by an obstacle
  int blockedIdx = 5 * N + 6;
  EXPECT_EQ(result.dist[blockedIdx], std::numeric_limits<int>::max());

  // Check the shortest path to (6, 6)
  Coord expectedPath = {6, 5}; // Because of the obstacle at (5, 5)
  EXPECT_EQ(result.shortestPaths(6, 6), expectedPath);
}

TEST_F(BattleMapTest, ComplexPathTest)
{
  const int N = battleMap->getGridSize();
  battleMap->placeTerrain(Coord{5, 5}, Terrain::IMPASSABLE_TERRAIN);
  battleMap->placeTerrain(Coord{5, 6}, Terrain::IMPASSABLE_TERRAIN);
  battleMap->placeTerrain(Coord{5, 7}, Terrain::IMPASSABLE_TERRAIN);
  battleMap->placeTerrain(Coord{5, 8}, Terrain::IMPASSABLE_TERRAIN);
  Coord src = {0, 0};
  Coord dest = {14, 14};

  battleMap->setCombatantCoordinates(*goblin, src);
  battleMap->buildBaseAdjacencyMatrix();
  auto result = battleMap->calcDijkstra(*goblin);

  // Check the distance to the farthest cell (bottom-right corner)
  int destIdx = dest[0] * N + dest[1];
  EXPECT_LT(result.dist[destIdx], std::numeric_limits<int>::max());

  // Check the shortest path near the obstacle
  EXPECT_EQ(result.shortestPaths(6, 8), (Coord{6, 7})); // Should go around the obstacle
}

TEST_F(BattleMapTest, NoPathDueToObstacle)
{
  const int N = battleMap->getGridSize();
  Coord src = {0, 0};

  // Add an obstacle that blocks the path entirely
  battleMap->placeTerrain(Coord{0, 1}, Terrain::IMPASSABLE_TERRAIN);
  battleMap->placeTerrain(Coord{1, 1}, Terrain::IMPASSABLE_TERRAIN);
  battleMap->placeTerrain(Coord{1, 0}, Terrain::IMPASSABLE_TERRAIN);

  battleMap->setCombatantCoordinates(*goblin, src);
  battleMap->buildBaseAdjacencyMatrix();
  auto result = battleMap->calcDijkstra(*goblin);

  // All distances except the starting node should be maxsize
  for(int i = 1; i < N * N; ++i)
    {
      EXPECT_EQ(result.dist[i], std::numeric_limits<int>::max());
    }

  // Shortest paths should remain as initialized (-1, -1) for unreachable nodes
  for(int i = 0; i < N; ++i)
    {
      for(int j = 1; j < N; ++j)
        {
          EXPECT_EQ(result.shortestPaths(i, j), (Coord{-1, -1}));
        }
    }
}

TEST_F(BattleMapTest, EmptyGrid) {
  const int N = battleMap->getGridSize();
  Coord src{7, 7}; // Start from the center
  battleMap->setCombatantCoordinates(*goblin, src);
  battleMap->buildBaseAdjacencyMatrix();
  auto result = battleMap->calcDijkstra(*goblin);

  EXPECT_EQ(result.dist[7 * N + 7], 0);
  EXPECT_EQ(result.dist[7 * N + 8], 1);
  EXPECT_EQ(result.dist[9 * N + 9], 2);
  EXPECT_EQ(result.dist[0 * N + 0], 7);
  EXPECT_EQ(result.dist[14 * N + 14], 7);
}

TEST_F(BattleMapTest, WithObstacles)
{
  const int N = battleMap->getGridSize();
  // Place some obstacles
  battleMap->placeTerrain(Coord{5, 5}, Terrain::IMPASSABLE_TERRAIN);
  battleMap->placeTerrain(Coord{5, 6}, Terrain::IMPASSABLE_TERRAIN);
  battleMap->placeTerrain(Coord{5, 7}, Terrain::IMPASSABLE_TERRAIN);
  battleMap->placeTerrain(Coord{6, 7}, Terrain::IMPASSABLE_TERRAIN);
  battleMap->placeTerrain(Coord{7, 7}, Terrain::IMPASSABLE_TERRAIN);

  Coord src{4, 6}; // Start just left of the obstacles
  battleMap->setCombatantCoordinates(*goblin, src);
  battleMap->buildBaseAdjacencyMatrix();
  auto result = battleMap->calcDijkstra(*goblin);

  EXPECT_EQ(result.dist[4 * N + 6], 0);
  EXPECT_EQ(result.dist[6 * N + 6], 4); // Have to go around
  EXPECT_EQ(result.dist[8 * N + 8], 5); // Have to go around

  // Check path
  Coord dest{8, 8};
  std::vector<Coord> path = battleMap->reconstructFromShortestPath(result.shortestPaths, src, dest);
  EXPECT_EQ(path.size(), 6); // [4,6] -> [4,7] -> [5,8] ->[6,8] -> [7,8] -> [8,8]
  EXPECT_EQ(path[0], (Coord{4, 6}));
  EXPECT_EQ(path[1], (Coord{4, 7}));
  EXPECT_EQ(path[2], (Coord{5, 8}));
  EXPECT_EQ(path[3], (Coord{6, 8}));
  EXPECT_EQ(path[4], (Coord{7, 8}));
  EXPECT_EQ(path[5], (Coord{8, 8}));
}

TEST_F(BattleMapTest, Unreachable)
{
  const int N = battleMap->getGridSize();
  // Create a wall dividing the grid
  for(int i = 0; i < N; ++i)
    {
      battleMap->placeTerrain(Coord{7, i}, Terrain::IMPASSABLE_TERRAIN);
    }

  Coord src{0, 0};
  battleMap->setCombatantCoordinates(*goblin, src);
  battleMap->buildBaseAdjacencyMatrix();
  auto result = battleMap->calcDijkstra(*goblin);

  EXPECT_EQ(result.dist[0 * N + 0], 0);
  EXPECT_EQ(result.dist[6 * N + 0], 6);
  EXPECT_EQ(result.dist[7 * N + 0], std::numeric_limits<int>::max());
  EXPECT_EQ(result.dist[14 * N + 14], std::numeric_limits<int>::max());
}

TEST_F(BattleMapTest, CombatantPositions)
{
  const int N = battleMap->getGridSize();
  teams->addCombatantToTeam(*goblin, Color::BLUE);
  teams->addCombatantToTeam(*draconic_sorcerer_lvl_1, Color::RED);
  teams->addCombatantToTeam(*bugbear, Color::RED);
  // Place combatants (treated as obstacles for this test)
  Coord sorcererSrc{3, 3};
  Coord bugbearSrc{10, 10};
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, sorcererSrc);
  battleMap->setCombatantCoordinates(*bugbear, bugbearSrc);

  Coord src{0, 0};
  battleMap->setCombatantCoordinates(*goblin, src);
  battleMap->buildBaseAdjacencyMatrix();
  auto result = battleMap->calcDijkstra(*goblin);

  EXPECT_EQ(result.dist[3 * N + 3], std::numeric_limits<int>::max());
  EXPECT_EQ(result.dist[10 * N + 10], std::numeric_limits<int>::max());
  EXPECT_EQ(result.dist[4 * N + 4], 5); // Have to go around combatant
}

TEST_F(BattleMapTest, EdgeCases)
{
  const int N = battleMap->getGridSize();
  Coord src{0, 0};
  battleMap->setCombatantCoordinates(*goblin, src);
  battleMap->buildBaseAdjacencyMatrix();
  auto result = battleMap->calcDijkstra(*goblin);

  // Test corners
  EXPECT_EQ(result.dist[0 * N + 14], 14);
  EXPECT_EQ(result.dist[14 * N + 0], 14);
  EXPECT_EQ(result.dist[14 * N + 14], 14);

  // Test edge midpoints
  EXPECT_EQ(result.dist[0 * N + 7], 7);
  EXPECT_EQ(result.dist[7 * N + 0], 7);
  EXPECT_EQ(result.dist[14 * N + 7], 14);
  EXPECT_EQ(result.dist[7 * N + 14], 14);
}

TEST_F(BattleMapTest, GetPathToCombatantMediumToMedium)
{
  teams->addCombatantToTeam(*draconic_sorcerer_lvl_1, Color::BLUE);
  teams->addCombatantToTeam(*bugbear, Color::BLUE);
  Coord sorcererSrc{0, 1};
  Coord bugbearSrc{11, 3};
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, sorcererSrc);
  battleMap->setCombatantCoordinates(*bugbear, bugbearSrc);

  battleMap->buildBaseAdjacencyMatrix();

  auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *bugbear);
  ASSERT_TRUE(path.has_value());

  std::vector<Coord> expectedPath = {{1, 1}, {1, 0}, {1, 0}, {1, 0}, {1, 0}, {1, 0}, {1, 0}, {1, 0}, {1, 0}, {1, 0}};
  EXPECT_EQ(*path, expectedPath);
}

TEST_F(BattleMapTest, GetPathToCoordMediumToCoord)
{
  teams->addCombatantToTeam(*draconic_sorcerer_lvl_1, Color::BLUE);
  battleMap->buildBaseAdjacencyMatrix();
  Coord sorcererSrc{0, 1};
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, sorcererSrc);

  auto path = battleMap->getPathToCoord(*draconic_sorcerer_lvl_1, {11, 3});
  ASSERT_TRUE(path.has_value());

  std::vector<Coord> expectedPath = {{1, 1}, {1, 1}, {1, 0}, {1, 0}, {1, 0}, {1, 0}, {1, 0}, {1, 0}, {1, 0}, {1, 0}, {1, 0}};
  EXPECT_EQ(*path, expectedPath);
}

TEST_F(BattleMapTest, GetPathToCombatantLargeToLarge)
{
  teams->addCombatantToTeam(*draconic_sorcerer_lvl_1, Color::BLUE);
  teams->addCombatantToTeam(*bugbear, Color::BLUE);
  battleMap->buildBaseAdjacencyMatrix();
  draconic_sorcerer_lvl_1->setSize(Size::LARGE);
  bugbear->setSize(Size::LARGE);
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, {0, 1});
  battleMap->setCombatantCoordinates(*bugbear, {5, 7});

  auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *bugbear);
  ASSERT_TRUE(path.has_value());

  std::vector<Coord> expectedPath = {{1, 1}, {1, 1}, {1, 1}, {0, 1}};
  EXPECT_EQ(*path, expectedPath);
}

TEST_F(BattleMapTest, GetPathToCombatantMediumToLarge)
{
  teams->addCombatantToTeam(*draconic_sorcerer_lvl_1, Color::BLUE);
  teams->addCombatantToTeam(*bugbear, Color::BLUE);
  battleMap->buildBaseAdjacencyMatrix();
  bugbear->setSize(Size::LARGE);
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, {0, 1});
  battleMap->setCombatantCoordinates(*bugbear, {5, 7});

  auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *bugbear);
  ASSERT_TRUE(path.has_value());

  std::vector<Coord> expectedPath1 = {{1, 1}, {1, 1}, {1, 1}, {1, 1}, {0, 1}};
  std::vector<Coord> expectedPath2 = {{1, 1}, {1, 1}, {1, 1}, {1, 1}, {1, 1}};
  EXPECT_TRUE(*path == expectedPath1 || *path == expectedPath2);
}

TEST_F(BattleMapTest, GetPathToCombatantLargeToMedium)
{
  teams->addCombatantToTeam(*draconic_sorcerer_lvl_1, Color::BLUE);
  teams->addCombatantToTeam(*bugbear, Color::BLUE);
  battleMap->buildBaseAdjacencyMatrix();
  draconic_sorcerer_lvl_1->setSize(Size::LARGE);
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, {0, 1});
  battleMap->setCombatantCoordinates(*bugbear, {5, 7});

  auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *bugbear);
  ASSERT_TRUE(path.has_value());

  std::vector<Coord> expectedPath = {{1, 1}, {1, 1}, {1, 1}, {0, 1}};
  EXPECT_EQ(*path, expectedPath);
}

TEST_F(BattleMapTest, GetPathToCombatantLargeToMedium2)
{
  teams->addCombatantToTeam(*draconic_sorcerer_lvl_1, Color::BLUE);
  teams->addCombatantToTeam(*bugbear, Color::BLUE);
  battleMap->placeTerrain(Coord{7, 14}, Terrain::DIFFICULT_TERRAIN);
  battleMap->placeTerrain(Coord{9, 14}, Terrain::DIFFICULT_TERRAIN);
  battleMap->buildBaseAdjacencyMatrix();
  draconic_sorcerer_lvl_1->setSize(Size::LARGE);
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, {4, 13});
  battleMap->setCombatantCoordinates(*bugbear, {8, 14});

  auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *bugbear);
  ASSERT_TRUE(path.has_value());

  std::vector<Coord> expectedPath = {{1, 0}, {1, 0}};
  EXPECT_EQ(*path, expectedPath);
}

TEST_F(BattleMapTest, GetPathToCombatantHugeToHuge)
{
  teams->addCombatantToTeam(*draconic_sorcerer_lvl_1, Color::BLUE);
  teams->addCombatantToTeam(*bugbear, Color::BLUE);
  battleMap->buildBaseAdjacencyMatrix();
  draconic_sorcerer_lvl_1->setSize(Size::HUGE);
  bugbear->setSize(Size::HUGE);
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, {0, 1});
  battleMap->setCombatantCoordinates(*bugbear, {5, 7});

  auto path = battleMap->getPathToCombatant(*draconic_sorcerer_lvl_1, *bugbear);
  ASSERT_TRUE(path.has_value());

  std::vector<Coord> expectedPath = {{1, 1}, {1, 1}, {0, 1}};
  EXPECT_EQ(*path, expectedPath);
}

TEST_F(BattleMapTest, RemoveCombatant) {
    draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, {4, 5});

    battleMap->removeCombatant(*draconic_sorcerer_lvl_1);

    // Check that the combatant is no longer in the battle map
    EXPECT_THROW(battleMap->getCombatantCoordinates(*draconic_sorcerer_lvl_1), std::out_of_range);

    // Check that the grid cells previously occupied by the combatant are now empty
    EXPECT_EQ(battleMap->getCombatantGridValueAt({4, 5}), -1);
    EXPECT_EQ(battleMap->getCombatantGridValueAt({5, 5}), -1);
    EXPECT_EQ(battleMap->getCombatantGridValueAt({4, 6}), -1);
    EXPECT_EQ(battleMap->getCombatantGridValueAt({5, 6}), -1);
}


TEST_F(BattleMapTest, FindBestPlacementHarmfulSquare)
{
    stone_giant->setSize(Size::MEDIUM);
    teams->addCombatantToTeam(*draconic_sorcerer_lvl_1, Color::BLUE);
    teams->addCombatantToTeam(*goblin, Color::RED);
    teams->addCombatantToTeam(*bugbear, Color::RED);
    teams->addCombatantToTeam(*wild_heart_barbarian, Color::BLUE);
    teams->addCombatantToTeam(*stone_giant, Color::RED);
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, {1, 1});
    battleMap->setCombatantCoordinates(*goblin, {4, 4});
    battleMap->setCombatantCoordinates(*bugbear, {10, 5});
    battleMap->setCombatantCoordinates(*wild_heart_barbarian, {6, 7});
    battleMap->setCombatantCoordinates(*stone_giant, {5, 5});

    // Test case 1: Original scenario
    auto [coord, score, affected] = battleMap->findBestPlacementHarmfulSquare(draconic_sorcerer_lvl_1, 20, 2);
    EXPECT_EQ(coord, (Coord{4, 4}));
    EXPECT_EQ(score, 2);
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), goblin) != affected.end());
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), bugbear) == affected.end());
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), wild_heart_barbarian) == affected.end());
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), stone_giant) != affected.end());

    // Test case 2: Ally blocking
    battleMap->moveCombatant(*wild_heart_barbarian, {5, 4});
    std::tie(coord, score, affected) = battleMap->findBestPlacementHarmfulSquare(draconic_sorcerer_lvl_1, 20, 2);
    EXPECT_EQ(score, 1);
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), goblin) != affected.end() ||
                std::find(affected.begin(), affected.end(), bugbear) != affected.end() ||
                std::find(affected.begin(), affected.end(), stone_giant) != affected.end());
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), wild_heart_barbarian) == affected.end());

    // Test case 3: A corner of a HUGE sized creature can be hit
    stone_giant->setSize(Size::HUGE);
    battleMap->moveCombatant(*stone_giant, {6, 1});  // move him so that only a corner can be hit
    std::tie(coord, score, affected) = battleMap->findBestPlacementHarmfulSquare(draconic_sorcerer_lvl_1, 20, 3);
    EXPECT_EQ(coord, (Coord{8, 3}));
    EXPECT_EQ(score, 2);
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), goblin) == affected.end());
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), bugbear) != affected.end());
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), wild_heart_barbarian) == affected.end());
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), stone_giant) != affected.end());

    // Test case 4: Spell range too short to hit anybody
    stone_giant->setSize(Size::MEDIUM);  // shrink him again
    battleMap->moveCombatant(*stone_giant, {5, 5}); // move him back
    std::tie(coord, score, affected) = battleMap->findBestPlacementHarmfulSquare(draconic_sorcerer_lvl_1, 1, 2);
    EXPECT_EQ(score, 0);
    EXPECT_TRUE(affected.empty());

    // Test case 5: Larger square size
    battleMap->moveCombatant(*wild_heart_barbarian, {6, 7});  // Move ally out of the way
    std::tie(coord, score, affected) = battleMap->findBestPlacementHarmfulSquare(draconic_sorcerer_lvl_1, 20, 3);
    EXPECT_EQ(score, 2);
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), goblin) != affected.end());
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), stone_giant) != affected.end());

    // Test case 6: Edge of map
    battleMap->moveCombatant(*draconic_sorcerer_lvl_1, {14, 14});
    battleMap->moveCombatant(*goblin, {13, 13});
    std::tie(coord, score, affected) = battleMap->findBestPlacementHarmfulSquare(draconic_sorcerer_lvl_1, 5, 2);
    EXPECT_EQ(coord, (Coord{12, 12}));
    EXPECT_EQ(score, 1);
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), goblin) != affected.end());

    // Test case 7: Allies and enemies bunched up
    battleMap->moveCombatant(*draconic_sorcerer_lvl_1, {0, 0});
    battleMap->moveCombatant(*goblin, {14, 14});
    battleMap->moveCombatant(*bugbear, {14, 13});
    battleMap->moveCombatant(*stone_giant, {13, 14});
    battleMap->moveCombatant(*wild_heart_barbarian, {13, 13});
    std::tie(coord, score, affected) = battleMap->findBestPlacementHarmfulSquare(draconic_sorcerer_lvl_1, 16, 2);
    EXPECT_TRUE(affected.empty());
}

TEST_F(BattleMapTest, FindBestPlacementHarmfulCircular)
{
    goblin->setSize(Size::LARGE);
    teams->addCombatantToTeam(*draconic_sorcerer_lvl_1, Color::BLUE);
    teams->addCombatantToTeam(*goblin, Color::RED);
    teams->addCombatantToTeam(*bugbear, Color::RED);
    teams->addCombatantToTeam(*wild_heart_barbarian, Color::BLUE);
    
    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, {1, 1});
    battleMap->setCombatantCoordinates(*goblin, {4, 4});
    battleMap->setCombatantCoordinates(*bugbear, {10, 5});
    battleMap->setCombatantCoordinates(*wild_heart_barbarian, {6, 7});

    // As if it was a Fireball
    constexpr int FIREBALL_RANGE = static_cast<int>(enc::SpellRange::FEET_150);
    constexpr int FIREBALL_RADIUS = 4;

    auto [coord, score, affected] = battleMap->findBestPlacementHarmfulCircular(draconic_sorcerer_lvl_1, FIREBALL_RANGE, FIREBALL_RADIUS);
    
    EXPECT_EQ(coord, (Coord{7, 3}));
    EXPECT_EQ(score, 2);
    EXPECT_EQ(affected.size(), 2);
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), goblin) != affected.end());
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), bugbear) != affected.end());
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), wild_heart_barbarian) == affected.end());

    // Move the ally in between the targets
    battleMap->moveCombatant(*wild_heart_barbarian, {6, 4});
    
    std::tie(coord, score, affected) = battleMap->findBestPlacementHarmfulCircular(draconic_sorcerer_lvl_1, FIREBALL_RANGE, FIREBALL_RADIUS);
    
    EXPECT_EQ(score, 1);  // Assuming only the large goblin is hit
    EXPECT_EQ(affected.size(), 1);
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), goblin) != affected.end());
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), bugbear) == affected.end());
    EXPECT_TRUE(std::find(affected.begin(), affected.end(), wild_heart_barbarian) == affected.end());
}

TEST_F(BattleMapTest, FindBestPlacementsHarmfulCone1)
{
  session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
  session->addCombatant(goblin, Color::RED);
  session->addCombatant(bugbear, Color::RED);
  session->addCombatant(ogre, Color::BLUE);
  session->addCombatant(stone_giant, Color::RED);
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, {1, 1});
  battleMap->setCombatantCoordinates(*goblin, {2, 11});
  battleMap->setCombatantCoordinates(*bugbear, {4, 11});
  battleMap->setCombatantCoordinates(*ogre, {5, 10});
  battleMap->setCombatantCoordinates(*stone_giant, {5, 12});

  // auto start = std::chrono::high_resolution_clock::now();
  auto result = battleMap->findBestPlacementHarmfulCone(draconic_sorcerer_lvl_1, TRANSLATE_CONE.at(SpellTarget::CONE_30));
  //  auto end = std::chrono::high_resolution_clock::now();
  // auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
  // std::cout << "Execution time of findBestPlacementHarmfulCone: " << duration.count() << " microseconds" << std::endl;
  ASSERT_TRUE(result.has_value());
  auto [bestCoord, bestAngle, maxScore] = *result;
  EXPECT_EQ(bestCoord, (Coord{0, 10}));
  EXPECT_EQ(maxScore, 3);
  EXPECT_NEAR(bestAngle, 48.43, 0.01);

  battleMap->moveCombatant(*ogre, {2, 12});
  result = battleMap->findBestPlacementHarmfulCone(draconic_sorcerer_lvl_1, TRANSLATE_CONE.at(SpellTarget::CONE_30));

  ASSERT_TRUE(result.has_value());
  std::tie(bestCoord, bestAngle, maxScore) = *result;
  EXPECT_EQ(bestCoord, (Coord{0, 9}));
  EXPECT_EQ(maxScore, 2);
  EXPECT_NEAR(bestAngle, 75.43, 0.01);
}

TEST_F(BattleMapTest, FindBestPlacementsHarmfulCone2)
{
  session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
  session->addCombatant(goblin, Color::RED);
  session->addCombatant(bugbear, Color::RED);
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, {4, 4});
  battleMap->setCombatantCoordinates(*goblin, {5, 8});
  battleMap->setCombatantCoordinates(*bugbear, {8, 5});

  auto result = battleMap->findBestPlacementHarmfulCone(draconic_sorcerer_lvl_1, TRANSLATE_CONE.at(SpellTarget::CONE_30));
    
  ASSERT_TRUE(result.has_value());
  auto [bestCoord, bestAngle, maxScore] = *result;
  EXPECT_EQ(bestCoord, (Coord{4, 9}));
  EXPECT_EQ(maxScore, 2);
  EXPECT_TRUE(std::abs(bestAngle - 135.0) < 0.01 || std::abs(bestAngle - 132.0) < 0.01 || std::abs(bestAngle - 138.0) < 0.01);
}

TEST_F(BattleMapTest, FindBestPlacementsHarmfulCone3)
{
  session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
  session->addCombatant(wild_heart_barbarian, Color::RED);
  session->addCombatant(battlemaster_fighter_lvl_5, Color::BLUE);
  session->addCombatant(green_dragon_wyrmling, Color::BLUE);
  session->addCombatant(giant_toad, Color::BLUE);
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, {8, 8});
  battleMap->setCombatantCoordinates(*wild_heart_barbarian, {7, 13});
  battleMap->setCombatantCoordinates(*battlemaster_fighter_lvl_5, {7, 12});
  battleMap->setCombatantCoordinates(*green_dragon_wyrmling, {8, 7});
  battleMap->setCombatantCoordinates(*giant_toad, {5, 11});

  auto result = battleMap->findBestPlacementHarmfulCone(green_dragon_wyrmling, TRANSLATE_CONE.at(SpellTarget::CONE_15));

  EXPECT_FALSE(result.has_value());
}

TEST_F(BattleMapTest, FindBestPlacementsHarmfulLine1)
{
  session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
  session->addCombatant(goblin, Color::RED);
  session->addCombatant(bugbear, Color::RED);
  session->addCombatant(ogre, Color::BLUE);
  session->addCombatant(stone_giant, Color::RED);
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, {1, 1});
  battleMap->setCombatantCoordinates(*goblin, {2, 11});
  battleMap->setCombatantCoordinates(*bugbear, {4, 11});
  battleMap->setCombatantCoordinates(*ogre, {5, 10});
  battleMap->setCombatantCoordinates(*stone_giant, {5, 12});
  // std::cout << battleMap->toString(true);

  auto result = battleMap->findBestPlacementHarmfulLine(draconic_sorcerer_lvl_1, 6, 1); // 6 squares long, 1 square wide

  ASSERT_TRUE(result.has_value());
  auto [bestCoord, bestAngle, maxScore] = *result;
  EXPECT_EQ(bestCoord, (Coord{0, 10}));
  EXPECT_EQ(maxScore, 3);
  EXPECT_NEAR(bestAngle, 69.43, 0.01);
}

TEST_F(BattleMapTest, FindBestPlacementsHarmfulLine2)
{
  ogre->setSize(Size::MEDIUM);
  session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
  session->addCombatant(goblin, Color::RED);
  session->addCombatant(bugbear, Color::RED);
  session->addCombatant(ogre, Color::BLUE);
  session->addCombatant(stone_giant, Color::RED);
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, {1, 1});
  battleMap->setCombatantCoordinates(*goblin, {2, 11});
  battleMap->setCombatantCoordinates(*bugbear, {4, 11});
  battleMap->setCombatantCoordinates(*ogre, {3, 11});
  battleMap->setCombatantCoordinates(*stone_giant, {5, 12});

  // std::cout << battleMap->toString(true);
  auto result = battleMap->findBestPlacementHarmfulLine(draconic_sorcerer_lvl_1, 6, 1);

  ASSERT_TRUE(result.has_value());
  auto [bestCoord, bestAngle, maxScore] = *result;
  EXPECT_EQ(bestCoord, (Coord{0, 10}));
  EXPECT_EQ(maxScore, 2);
  EXPECT_NEAR(bestAngle, 54.43, 0.01);
}

TEST_F(BattleMapTest, FindBestPlacementsHarmfulLineDifferentLengths)
{
  session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
  session->addCombatant(wild_heart_barbarian, Color::RED);
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, {0, 0});
  battleMap->setCombatantCoordinates(*wild_heart_barbarian, {14, 14});
  // std::cout << battleMap->toString(true);

  auto result = battleMap->findBestPlacementHarmfulLine(draconic_sorcerer_lvl_1, 2, 1);
  EXPECT_TRUE(result.has_value());
  auto [bestCoord, bestAngle, maxScore] = *result;
  EXPECT_EQ(bestCoord, (Coord{13, 13}));
  EXPECT_EQ(maxScore, 1);
  EXPECT_NEAR(bestAngle, 45.0, 0.01);

  result = battleMap->findBestPlacementHarmfulLine(draconic_sorcerer_lvl_1, 20, 1);
  EXPECT_TRUE(result.has_value());
  std::tie(bestCoord, bestAngle, maxScore) = *result;
  EXPECT_EQ(bestCoord, (Coord{0, 0}));
  EXPECT_EQ(maxScore, 1);
  EXPECT_NEAR(bestAngle, 45.0, 0.01);
}

TEST_F(BattleMapTest, FindBestPlacementsHarmfulLineNoValidPlacement)
{
  session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
  session->addCombatant(goblin, Color::BLUE);
  session->addCombatant(bugbear, Color::BLUE);
  session->addCombatant(green_dragon_wyrmling, Color::BLUE);
  session->addCombatant(wild_heart_barbarian, Color::RED);
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, {0, 0});
  battleMap->setCombatantCoordinates(*goblin, {13, 14});
  battleMap->setCombatantCoordinates(*bugbear, {13, 13});
  battleMap->setCombatantCoordinates(*green_dragon_wyrmling, {14, 13});
  battleMap->setCombatantCoordinates(*wild_heart_barbarian, {14, 14});
  // std::cout << battleMap->toString(true);

  auto result = battleMap->findBestPlacementHarmfulLine(draconic_sorcerer_lvl_1, 2, 1);
  EXPECT_FALSE(result.has_value());
}

TEST_F(BattleMapTest, FindBestPlacementsHarmfulLineWiderLine)
{
  session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
  session->addCombatant(goblin, Color::RED);
  session->addCombatant(bugbear, Color::RED);
  session->addCombatant(wild_heart_barbarian, Color::RED);
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, {4, 4});
  battleMap->setCombatantCoordinates(*goblin, {5, 7});
  battleMap->setCombatantCoordinates(*bugbear, {8, 6});
  battleMap->setCombatantCoordinates(*wild_heart_barbarian, {8, 4});
  // std::cout << battleMap->toString(true);

  auto result = battleMap->findBestPlacementHarmfulLine(draconic_sorcerer_lvl_1, 6, 3);

  ASSERT_TRUE(result.has_value());
  auto [bestCoord, bestAngle, maxScore] = *result;
  EXPECT_EQ(bestCoord, (Coord{4, 8}));
  EXPECT_EQ(maxScore, 3);
  EXPECT_NEAR(bestAngle, 135.69, 0.01);
}

TEST_F(BattleMapTest, GetCombatantsAffectedBySphereAoE)
{
  session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
  session->addCombatant(ogre, Color::RED);
  session->addCombatant(bugbear, Color::RED);
  session->addCombatant(wild_heart_barbarian, Color::BLUE);

  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{1, 1});
  battleMap->setCombatantCoordinates(*ogre, Coord{4, 4});
  battleMap->setCombatantCoordinates(*bugbear, Coord{10, 5});
  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{6, 7});
  auto combatants = battleMap->getCombatantsAffectedBySphereAoE(draconic_sorcerer_lvl_1, SpellTarget::RADIUS_20, Type::HARMFUL, Coord{7, 3});

  EXPECT_EQ(std::count(combatants.begin(), combatants.end(), draconic_sorcerer_lvl_1), 0);
  EXPECT_NE(std::find(combatants.begin(), combatants.end(), ogre), combatants.end());
  EXPECT_NE(std::find(combatants.begin(), combatants.end(), bugbear), combatants.end());
  EXPECT_EQ(std::count(combatants.begin(), combatants.end(), wild_heart_barbarian), 0);
}

TEST_F(BattleMapTest, GetCombatantsAffectedByBoxAoE)
{
    session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
    session->addCombatant(goblin, Color::RED);
    session->addCombatant(bugbear, Color::RED);
    session->addCombatant(wild_heart_barbarian, Color::BLUE);
    session->addCombatant(stone_giant, Color::BLUE);
    session->addCombatant(ogre, Color::RED);

    goblin->setSize(Size::LARGE);

    battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{1, 1});
    battleMap->setCombatantCoordinates(*goblin, Coord{8, 5});
    battleMap->setCombatantCoordinates(*bugbear, Coord{10, 5});
    battleMap->setCombatantCoordinates(*wild_heart_barbarian, Coord{11, 4});
    battleMap->setCombatantCoordinates(*stone_giant, Coord{10, 6});
    battleMap->setCombatantCoordinates(*ogre, Coord{5, 3});

    auto combatants = battleMap->getCombatantsAffectedByBoxAoE(SpellTarget::BOX_20, Coord{7, 3});

    EXPECT_EQ(std::count(combatants.begin(), combatants.end(), draconic_sorcerer_lvl_1), 0);
    EXPECT_NE(std::find(combatants.begin(), combatants.end(), goblin), combatants.end());
    EXPECT_NE(std::find(combatants.begin(), combatants.end(), bugbear), combatants.end());
    EXPECT_EQ(std::count(combatants.begin(), combatants.end(), wild_heart_barbarian), 0);
    EXPECT_NE(std::find(combatants.begin(), combatants.end(), stone_giant), combatants.end());
    EXPECT_EQ(std::count(combatants.begin(), combatants.end(), ogre), 0);
}

TEST_F(BattleMapTest, GetCombatantsAffectedByConeAoE)
{
  session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
  session->addCombatant(goblin, Color::RED);
  session->addCombatant(bugbear, Color::RED);
  session->addCombatant(wild_heart_barbarian, Color::BLUE);
  session->addCombatant(stone_giant, Color::RED);

  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{5, 5});
  battleMap->setCombatantCoordinates(*goblin, Coord{7, 7});
  battleMap->setCombatantCoordinates(*bugbear, Coord{8, 8});
  battleMap->setCombatantCoordinates(*wild_heart_barbarian, Coord{3, 3});
  battleMap->setCombatantCoordinates(*stone_giant, Coord{9, 9});

  auto combatants = battleMap->getCombatantsAffectedByConeAoE(draconic_sorcerer_lvl_1, SpellTarget::CONE_30, Coord{5, 5}, 45.0);

  EXPECT_EQ(std::count(combatants.begin(), combatants.end(), draconic_sorcerer_lvl_1), 0);
  EXPECT_NE(std::find(combatants.begin(), combatants.end(), goblin), combatants.end());
  EXPECT_NE(std::find(combatants.begin(), combatants.end(), bugbear), combatants.end());
  EXPECT_EQ(std::count(combatants.begin(), combatants.end(), wild_heart_barbarian), 0);
  EXPECT_NE(std::find(combatants.begin(), combatants.end(), stone_giant), combatants.end());
}

TEST_F(BattleMapTest, GetCombatantsAffectedByLineAoE)
{
  session->addCombatant(draconic_sorcerer_lvl_1, Color::BLUE);
  session->addCombatant(goblin, Color::RED);
  session->addCombatant(bugbear, Color::RED);
  session->addCombatant(wild_heart_barbarian, Color::BLUE);
  session->addCombatant(stone_giant, Color::RED);

  battleMap->setCombatantCoordinates(*draconic_sorcerer_lvl_1, Coord{1, 1});
  battleMap->setCombatantCoordinates(*goblin, Coord{3, 3});
  battleMap->setCombatantCoordinates(*bugbear, Coord{5, 5});
  battleMap->setCombatantCoordinates(*wild_heart_barbarian, Coord{2, 4});
  battleMap->setCombatantCoordinates(*stone_giant, Coord{7, 7});
  std::cout << battleMap->toString(true);

  auto combatants = battleMap->getCombatantsAffectedByLineAoE(draconic_sorcerer_lvl_1, Coord{1, 1}, 45.0, 8, 1);

  EXPECT_EQ(std::count(combatants.begin(), combatants.end(), draconic_sorcerer_lvl_1), 0);
  EXPECT_NE(std::find(combatants.begin(), combatants.end(), goblin), combatants.end());
  EXPECT_NE(std::find(combatants.begin(), combatants.end(), bugbear), combatants.end());
  EXPECT_EQ(std::count(combatants.begin(), combatants.end(), wild_heart_barbarian), 0);
  EXPECT_EQ(std::count(combatants.begin(), combatants.end(), stone_giant), 0);
}

// TEST_F(BattleMapTest, FindBestPlacementHarmfulSquareThunderwave)
// {
//     stone_giant->setSize(Size::MEDIUM);
//     teams->addCombatantToTeam(draconic_sorcerer_5lvl, Teams::Color::BLUE);
//     teams->addCombatantToTeam(goblin, Teams::Color::RED);
//     teams->addCombatantToTeam(bugbear, Teams::Color::RED);
//     teams->addCombatantToTeam(wild_heart_barbarian, Teams::Color::BLUE);
//     teams->addCombatantToTeam(stone_giant, Teams::Color::RED);
//     battleMap->setCombatantCoordinates(*draconic_sorcerer_5lvl, {3, 4});
//     battleMap->setCombatantCoordinates(*goblin, {4, 4});
//     battleMap->setCombatantCoordinates(*bugbear, {5, 6});
//     battleMap->setCombatantCoordinates(*wild_heart_barbarian, {4, 6});
//     battleMap->setCombatantCoordinates(*stone_giant, {5, 5});

//     ThunderwaveFactory twf(draconic_sorcerer_5lvl->getDC(), Action::THUNDERWAVE, test_draconic_sorcerer_5lvl.get(), test_draconic_sorcerer_5lvl->getSpellSlots());
//     auto coord = twf.findBestArgs(draconic_sorcerer_5lvl.get());
//     EXPECT_EQ(coord, (Coord{4, 3}));

//     battleMap->moveCombatant(*draconic_sorcerer_5lvl, {2, 4});
//     coord = twf.findBestArgs(draconic_sorcerer_5lvl.get());
//     EXPECT_EQ(coord, (Coord{3, 3}));

//     battleMap->moveCombatant(*wild_heart_barbarian, {4, 7});
//     coord = twf.findBestArgs(draconic_sorcerer_5lvl.get());
//     EXPECT_EQ(coord, (Coord{3, 4}));
// }

// TEST_F(BattleMapTest, FindBestPlacementHarmfulSquareThunderwaveOutOfSpellRange)
// {
//     teams->addCombatantToTeam(fighter_lvl_1.get(), Teams::Color::BLUE);
//     teams->addCombatantToTeam(druid_lvl_1.get(), Teams::Color::RED);
//     battleMap->setCombatantCoordinates(*fighter_lvl_1, {14, 3});
//     battleMap->setCombatantCoordinates(*druid_lvl_1, {2, 9});
    
//     ThunderwaveFactory twf(druid_lvl_1->getDC(), Action::THUNDERWAVE, test_druid_lvl_1.get(), test_druid_lvl_1->getSpellSlots());
//     auto coords = twf.findBestArgs(druid_lvl_1.get());
//     EXPECT_EQ(coords, std::nullopt);
// }
