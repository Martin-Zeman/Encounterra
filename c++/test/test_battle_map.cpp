#include <gtest/gtest.h>
#include "core/battle_map.hpp"
#include "core/misc.hpp"
#include "core/geometry.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "core/teams.hpp"
#include "combatants/goblin.hpp"
#include "combatants/draconic_sorcerer_lvl_1.hpp"
#include "combatants/bugbear.hpp"
#include <set>
#include <algorithm>
#include <memory>

using namespace enc;

class BattleMapTest : public ::testing::Test
{
protected:
  BattleMap *battleMap;
  Teams *teams;
  std::unique_ptr<Goblin> test_goblin;
  std::unique_ptr<Bugbear> test_bugbear;
  std::unique_ptr<DraconicSorcererLvl1> test_draconic_sorcerer_lvl_1;

  void SetUp() override
  {
    BattleMap::resetInstance(); // Reset the singleton instance before each test
    battleMap = &BattleMap::getInstance();
    Teams::resetInstance();
    teams = &Teams::getInstance();
    test_goblin = std::make_unique<Goblin>(1);
    test_draconic_sorcerer_lvl_1 = std::make_unique<DraconicSorcererLvl1>(1);
    test_bugbear = std::make_unique<Bugbear>(1);
  }
};

TEST_F(BattleMapTest, GetFreeCoordinatesInHopRangeMedium)
{
  battleMap->setCombatantCoordinates(*test_goblin, Coord({5, 7}));
  Coord coords{5, 7};

  auto adj = battleMap->getFreeCoordsInHopRange(Coords{{5, 7}}, blaze::DynamicVector<double>(), Size::MEDIUM, 1, -1);

  std::set<Coord> expected_adj = {{4, 7}, {6, 7}, {4, 8}, {5, 8}, {6, 8}, {4, 6}, {5, 6}, {6, 6}};
  std::set<Coord> actual_adj(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);

  // Test including the combatant's own coord
  adj = battleMap->getFreeCoordsInHopRange(Coords{{5, 7}}, blaze::DynamicVector<double>(), Size::MEDIUM, 1, test_goblin->_id);

  expected_adj = {{4, 7}, {5, 7}, {6, 7}, {4, 8}, {5, 8}, {6, 8}, {4, 6}, {5, 6}, {6, 6}};
  actual_adj = std::set<Coord>(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);
}

TEST_F(BattleMapTest, GetFreeCoordinatesInHopRangeLarge)
{
  test_goblin->setSize(Size::LARGE);
  battleMap->setCombatantCoordinates(*test_goblin, Coord({5, 7}));
  auto large_goblin_coords = battleMap->getCombatantCoordinates(*test_goblin);

  auto adj = battleMap->getFreeCoordsInHopRange(large_goblin_coords, blaze::DynamicVector<double>(), Size::MEDIUM, 1, -1);

  std::set<Coord> expected_adj = {{4, 6}, {4, 7}, {4, 8}, {4, 9}, {5, 6}, {5, 9}, {6, 6}, {6, 9}, {7, 6}, {7, 7}, {7, 8}, {7, 9}};
  std::set<Coord> actual_adj(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);

  // Test including the combatant's own coord
  adj = battleMap->getFreeCoordsInHopRange(large_goblin_coords, blaze::DynamicVector<double>(), Size::MEDIUM, 1, test_goblin->_id);

  expected_adj = {{4, 6}, {5, 7}, {6, 7}, {5, 8}, {6, 8}, {4, 7}, {4, 8}, {4, 9}, {5, 6}, {5, 9}, {6, 6}, {6, 9}, {7, 6}, {7, 7}, {7, 8}, {7, 9}};
  actual_adj = std::set<Coord>(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);
}

TEST_F(BattleMapTest, GetFreeCoordinatesInHopRangeLargeInACorner)
{
  test_goblin->setSize(Size::LARGE);
  battleMap->setCombatantCoordinates(*test_goblin, Coord({0, 1}));
  auto large_goblin_coords = battleMap->getCombatantCoordinates(*test_goblin);

  auto adj = battleMap->getFreeCoordsInHopRange(large_goblin_coords, blaze::DynamicVector<double>(), Size::MEDIUM, 1, -1);

  std::set<Coord> expected_adj = {{0, 0}, {1, 0}, {2, 0}, {2, 1}, {2, 2}, {0, 3}, {1, 3}, {2, 3}};
  std::set<Coord> actual_adj(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);
}

TEST_F(BattleMapTest, GetFreeCoordinatesInHopRangeHugeWithTerrain)
{
  test_goblin->setSize(Size::HUGE);
  battleMap->setCombatantCoordinates(*test_goblin, Coord({8, 2}));
  battleMap->placeTerrain(Coord{7, 3}, Terrain::IMPASSABLE_TERRAIN);
  auto huge_goblin_coords = battleMap->getCombatantCoordinates(*test_goblin);

  auto adj = battleMap->getFreeCoordsInHopRange(huge_goblin_coords, blaze::DynamicVector<double>(), Size::MEDIUM, 1, -1);

  std::set<Coord> expected_adj
    = {{7, 1}, {7, 2}, {7, 4}, {7, 5}, {8, 1}, {8, 5}, {9, 1}, {9, 5}, {10, 1}, {10, 5}, {11, 1}, {11, 2}, {11, 3}, {11, 4}, {11, 5}};
  std::set<Coord> actual_adj(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);

  // Test including the combatant's own coord
  adj = battleMap->getFreeCoordsInHopRange(huge_goblin_coords, blaze::DynamicVector<double>(), Size::MEDIUM, 1, test_goblin->_id);

  expected_adj = {{7, 1}, {7, 2},  {7, 4}, {7, 5}, {8, 1}, {8, 2},  {9, 2},  {10, 2}, {8, 3},  {9, 3},  {10, 3}, {8, 4},
                  {9, 4}, {10, 4}, {8, 5}, {9, 1}, {9, 5}, {10, 1}, {10, 5}, {11, 1}, {11, 2}, {11, 3}, {11, 4}, {11, 5}};
  actual_adj = std::set<Coord>(adj.begin(), adj.end());
  EXPECT_EQ(actual_adj, expected_adj);
}

TEST_F(BattleMapTest, GetFreeCoordsInCartesianRangeMedium)
{
  battleMap->setCombatantCoordinates(*test_goblin, Coord({5, 7}));

  auto coords = battleMap->getCombatantCoordinates(*test_goblin);
  auto free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 1, -1);

  std::set<Coord> expected_free_coords = {{4, 7}, {6, 7}, {5, 8}, {5, 6}};
  std::set<Coord> actual_free_coords(free_coords.begin(), free_coords.end());
  EXPECT_EQ(actual_free_coords, expected_free_coords);

  free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 1, test_goblin->_id);
  expected_free_coords = {{4, 7}, {5, 7}, {6, 7}, {5, 8}, {5, 6}};
  actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
  EXPECT_EQ(actual_free_coords, expected_free_coords);

  battleMap->moveCombatant(*test_goblin, Coord({8, 13}));
  coords = battleMap->getCombatantCoordinates(*test_goblin);
  free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 2, -1);
  expected_free_coords = {{6, 13}, {7, 13}, {9, 13}, {10, 13}, {7, 14}, {8, 14}, {9, 14}, {7, 12}, {8, 12}, {9, 12}, {8, 11}};
  actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
  EXPECT_EQ(actual_free_coords, expected_free_coords);

  free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 2, test_goblin->_id);
  expected_free_coords = {{6, 13}, {7, 13}, {8, 13}, {9, 13}, {10, 13}, {7, 14}, {8, 14}, {9, 14}, {7, 12}, {8, 12}, {9, 12}, {8, 11}};
  actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
  EXPECT_EQ(actual_free_coords, expected_free_coords);

    battleMap->moveCombatant(*test_goblin, Coord({8, 13}));
    coords = battleMap->getCombatantCoordinates(*test_goblin);
    free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 2, -1);
    expected_free_coords = {{6, 13}, {7, 13}, {9, 13}, {10, 13}, {7, 14}, {8, 14}, {9, 14}, {7, 12}, {8, 12}, {9, 12}, {8, 11}};
    actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
    EXPECT_EQ(actual_free_coords, expected_free_coords);

    free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 2, test_goblin->_id);
    expected_free_coords = {{6, 13}, {7, 13}, {8, 13}, {9, 13}, {10, 13}, {7, 14}, {8, 14}, {9, 14}, {7, 12}, {8, 12}, {9, 12}, {8, 11}};
    actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
    EXPECT_EQ(actual_free_coords, expected_free_coords);

    battleMap->moveCombatant(*test_goblin, Coord({5, 5}));
    coords = battleMap->getCombatantCoordinates(*test_goblin);
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

    free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 4, test_goblin->_id);
    EXPECT_NE(std::find(free_coords.begin(), free_coords.end(), Coord({5, 5})), free_coords.end())
        << "Coordinate 5,5 should be in free_coords";
}

TEST_F(BattleMapTest, GetFreeCoordsInCartesianRangeLarge)
{
  test_goblin->setSize(Size::LARGE);
  battleMap->setCombatantCoordinates(*test_goblin, Coord({2, 2}));

  auto coords = battleMap->getCombatantCoordinates(*test_goblin);
  auto free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::LARGE, 1, -1);

  std::set<Coord> expected_free_coords = {{2, 1}, {3, 1}, {1, 2}, {4, 2}, {1, 3}, {4, 3}, {2, 4}, {3, 4}};
  std::set<Coord> actual_free_coords(free_coords.begin(), free_coords.end());
  EXPECT_EQ(actual_free_coords, expected_free_coords);

  free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::LARGE, 1, test_goblin->_id);
  expected_free_coords = {{2, 1}, {2, 2}, {3, 2}, {2, 3}, {3, 3}, {3, 1}, {1, 2}, {4, 2}, {1, 3}, {4, 3}, {2, 4}, {3, 4}};
  actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
  EXPECT_EQ(actual_free_coords, expected_free_coords);

  battleMap->moveCombatant(*test_goblin, Coord({6, 8}));
  coords = battleMap->getCombatantCoordinates(*test_goblin);
  free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::LARGE, 2, -1);
  expected_free_coords = {{6, 6}, {7, 6}, {5, 7}, {6, 7}, {7, 7},  {8, 7},  {4, 8},  {5, 8},  {8, 8},  {9, 8},
                          {4, 9}, {5, 9}, {8, 9}, {9, 9}, {5, 10}, {6, 10}, {7, 10}, {8, 10}, {6, 11}, {7, 11}};
  actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
  EXPECT_EQ(actual_free_coords, expected_free_coords);

  free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::LARGE, 2, test_goblin->_id);
  expected_free_coords = {{6, 6}, {6, 8}, {7, 8}, {6, 9}, {7, 9}, {7, 6}, {5, 7},  {6, 7},  {7, 7},  {8, 7},  {4, 8},  {5, 8},
                          {8, 8}, {9, 8}, {4, 9}, {5, 9}, {8, 9}, {9, 9}, {5, 10}, {6, 10}, {7, 10}, {8, 10}, {6, 11}, {7, 11}};
  actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
  EXPECT_EQ(actual_free_coords, expected_free_coords);
}

TEST_F(BattleMapTest, MoveCombatantByIncrementMedium)
{
  Coord initialPos{0, 1};
  battleMap->setCombatantCoordinates(*test_goblin, initialPos);

  auto coords = battleMap->getCombatantCoordinates(*test_goblin);
  ASSERT_EQ(coords.get().size(), 1);
  EXPECT_EQ(coords.get()[0], initialPos);

  Coord increment{1, 1};
  battleMap->moveCombatantByIncrement(*test_goblin, increment);

  coords = battleMap->getCombatantCoordinates(*test_goblin);
  ASSERT_EQ(coords.get().size(), 1);
  Coord expectedCoord{1, 2};
  EXPECT_EQ(coords.get()[0], expectedCoord);
}

TEST_F(BattleMapTest, MoveCombatantByIncrementMediumInvalid)
{
  Coord initialPos{0, 1};
  battleMap->setCombatantCoordinates(*test_goblin, initialPos);

  auto coords = battleMap->getCombatantCoordinates(*test_goblin);
  ASSERT_EQ(coords.get().size(), 1);
  EXPECT_EQ(coords.get()[0], initialPos);

  Coord invalidIncrement{-1, 0};
  EXPECT_THROW(battleMap->moveCombatantByIncrement(*test_goblin, invalidIncrement), std::out_of_range);
}

TEST_F(BattleMapTest, MoveCombatantByIncrementLarge)
{
  test_goblin->setSize(Size::LARGE);

  Coord initialPos{0, 1};
  battleMap->setCombatantCoordinates(*test_goblin, initialPos);

  auto coords = battleMap->getCombatantCoordinates(*test_goblin);
  ASSERT_EQ(coords.get().size(), 4);
  std::vector<Coord> expectedInitialPos{{0, 1}, {0, 2}, {1, 1}, {1, 2}};
  EXPECT_EQ(coords.get(), expectedInitialPos);

  Coord increment{1, 1};
  battleMap->moveCombatantByIncrement(*test_goblin, increment);

  coords = battleMap->getCombatantCoordinates(*test_goblin);
  ASSERT_EQ(coords.get().size(), 4);
  std::vector<Coord> expectedFinalPos{{1, 2}, {1, 3}, {2, 2}, {2, 3}};
  EXPECT_EQ(coords.get(), expectedFinalPos);
}

TEST_F(BattleMapTest, MoveCombatantMedium)
{
  Coord initialPos{0, 1};
  battleMap->setCombatantCoordinates(*test_goblin, initialPos);

  auto coords = battleMap->getCombatantCoordinates(*test_goblin);
  ASSERT_EQ(coords.get().size(), 1);
  EXPECT_EQ(coords.get()[0], initialPos);

  Coord newPos{14, 14};
  battleMap->moveCombatant(*test_goblin, newPos);

  coords = battleMap->getCombatantCoordinates(*test_goblin);
  ASSERT_EQ(coords.get().size(), 1);
  EXPECT_EQ(coords.get()[0], newPos);
}

TEST_F(BattleMapTest, MoveCombatantMediumInvalid)
{
  Coord initialPos{0, 1};
  battleMap->setCombatantCoordinates(*test_goblin, initialPos);

  auto coords = battleMap->getCombatantCoordinates(*test_goblin);
  ASSERT_EQ(coords.get().size(), 1);
  EXPECT_EQ(coords.get()[0], initialPos);

  Coord invalidPos{15, 15};
  EXPECT_THROW(battleMap->moveCombatant(*test_goblin, invalidPos), std::out_of_range);
}

TEST_F(BattleMapTest, MoveCombatantLarge)
{
  test_goblin->setSize(Size::LARGE);

  Coord initialPos{0, 1};
  battleMap->setCombatantCoordinates(*test_goblin, initialPos);

  auto coords = battleMap->getCombatantCoordinates(*test_goblin);
  ASSERT_EQ(coords.get().size(), 4);
  std::vector<Coord> expectedInitialPos{{0, 1}, {0, 2}, {1, 1}, {1, 2}};
  EXPECT_EQ(coords.get(), expectedInitialPos);

  Coord newPos{9, 9};
  battleMap->moveCombatant(*test_goblin, newPos);

  coords = battleMap->getCombatantCoordinates(*test_goblin);
  ASSERT_EQ(coords.get().size(), 4);
  std::vector<Coord> expectedFinalPos{{9, 9}, {9, 10}, {10, 9}, {10, 10}};
  EXPECT_EQ(coords.get(), expectedFinalPos);
}

TEST_F(BattleMapTest, SimplePathTest)
{
  const int N = battleMap->getGridSize();
  battleMap->placeTerrain(Coord{5, 5}, Terrain::IMPASSABLE_TERRAIN);
  battleMap->placeTerrain(Coord{5, 6}, Terrain::IMPASSABLE_TERRAIN);
  battleMap->setCombatantCoordinates(*test_goblin, Coord({0, 0}));
  battleMap->buildBaseAdjacencyMatrix();
  auto result = battleMap->calcDijkstra(*test_goblin);

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

  battleMap->setCombatantCoordinates(*test_goblin, src);
  battleMap->buildBaseAdjacencyMatrix();
  auto result = battleMap->calcDijkstra(*test_goblin);

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

  battleMap->setCombatantCoordinates(*test_goblin, src);
  battleMap->buildBaseAdjacencyMatrix();
  auto result = battleMap->calcDijkstra(*test_goblin);

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
  battleMap->setCombatantCoordinates(*test_goblin, src);
  battleMap->buildBaseAdjacencyMatrix();
  auto result = battleMap->calcDijkstra(*test_goblin);

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
  battleMap->setCombatantCoordinates(*test_goblin, src);
  battleMap->buildBaseAdjacencyMatrix();
  auto result = battleMap->calcDijkstra(*test_goblin);

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
  battleMap->setCombatantCoordinates(*test_goblin, src);
  battleMap->buildBaseAdjacencyMatrix();
  auto result = battleMap->calcDijkstra(*test_goblin);

  EXPECT_EQ(result.dist[0 * N + 0], 0);
  EXPECT_EQ(result.dist[6 * N + 0], 6);
  EXPECT_EQ(result.dist[7 * N + 0], std::numeric_limits<int>::max());
  EXPECT_EQ(result.dist[14 * N + 14], std::numeric_limits<int>::max());
}

TEST_F(BattleMapTest, CombatantPositions)
{
  const int N = battleMap->getGridSize();
  teams->addCombatantToTeam(*test_goblin, Color::BLUE);
  teams->addCombatantToTeam(*test_draconic_sorcerer_lvl_1, Color::RED);
  teams->addCombatantToTeam(*test_bugbear, Color::RED);
  // Place combatants (treated as obstacles for this test)
  Coord sorcererSrc{3, 3};
  Coord bugbearSrc{10, 10};
  battleMap->setCombatantCoordinates(*test_draconic_sorcerer_lvl_1, sorcererSrc);
  battleMap->setCombatantCoordinates(*test_bugbear, bugbearSrc);

  Coord src{0, 0};
  battleMap->setCombatantCoordinates(*test_goblin, src);
  battleMap->buildBaseAdjacencyMatrix();
  auto result = battleMap->calcDijkstra(*test_goblin);

  EXPECT_EQ(result.dist[3 * N + 3], std::numeric_limits<int>::max());
  EXPECT_EQ(result.dist[10 * N + 10], std::numeric_limits<int>::max());
  EXPECT_EQ(result.dist[4 * N + 4], 5); // Have to go around combatant
}

TEST_F(BattleMapTest, EdgeCases)
{
  const int N = battleMap->getGridSize();
  Coord src{0, 0};
  battleMap->setCombatantCoordinates(*test_goblin, src);
  battleMap->buildBaseAdjacencyMatrix();
  auto result = battleMap->calcDijkstra(*test_goblin);

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
