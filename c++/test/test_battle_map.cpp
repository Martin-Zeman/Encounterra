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
  BattleMap *battleMap;
  std::unique_ptr<Goblin> test_goblin;

  void SetUp() override
  {
    BattleMap::resetInstance(); // Reset the singleton instance before each test
    battleMap = &BattleMap::getInstance();
    test_goblin = std::make_unique<Goblin>(1);
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

TEST_F(BattleMapTest, GetFreeCoordsInCartesianRangeMedium) {
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

    // battleMap->moveCombatant(*test_goblin, Coord({8, 13}));
    // coords = battleMap->getCombatantCoordinates(*test_goblin);
    // free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 2, -1);
    // expected_free_coords = {{6, 13}, {7, 13}, {9, 13}, {10, 13}, {7, 14}, {8, 14}, {9, 14}, {7, 12}, {8, 12}, {9, 12}, {8, 11}};
    // actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
    // EXPECT_EQ(actual_free_coords, expected_free_coords);

    // free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 2, test_goblin->_id);
    // expected_free_coords = {{6, 13}, {7, 13}, {8, 13}, {9, 13}, {10, 13}, {7, 14}, {8, 14}, {9, 14}, {7, 12}, {8, 12}, {9, 12}, {8, 11}};
    // actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
    // EXPECT_EQ(actual_free_coords, expected_free_coords);

    // battleMap->moveCombatant(*test_goblin, Coord({5, 5}));
    // coords = battleMap->getCombatantCoordinates(*test_goblin);
    // free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 4, -1);
    // EXPECT_FALSE(free_coords.count({1, 1}) || free_coords.count({2, 1}) || free_coords.count({3, 1}) || free_coords.count({4, 1}) || free_coords.count({6, 1}));
    // EXPECT_FALSE(free_coords.count({7, 1}) || free_coords.count({8, 1}));
    // EXPECT_FALSE(free_coords.count({1, 2}) || free_coords.count({1, 3}) || free_coords.count({1, 4}) || free_coords.count({1, 6}) || free_coords.count({1, 7}));
    // EXPECT_FALSE(free_coords.count({1, 8}) || free_coords.count({8, 8}));
    // EXPECT_FALSE(free_coords.count({2, 8}) || free_coords.count({8, 8}) || free_coords.count({9, 8}));
    // EXPECT_TRUE(free_coords.count({9, 5}) && free_coords.count({1, 5}) && free_coords.count({5, 1}) && free_coords.count({5, 9}));
    
    // free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::MEDIUM, 4, test_goblin->_id);
    // EXPECT_TRUE(free_coords.count({5, 5}));
}

TEST_F(BattleMapTest, GetFreeCoordsInCartesianRangeLarge) {
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

    // battleMap->moveCombatant(*test_goblin, Coord({6, 8}));
    // coords = battleMap->getCombatantCoordinates(*test_goblin);
    // free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::LARGE, 2, -1);
    // expected_free_coords = {{6, 6}, {7, 6}, {5, 7}, {6, 7}, {7, 7}, {8, 7}, {4, 8}, {5, 8}, {8, 8}, {9, 8}, {4, 9}, {5, 9}, {8, 9}, {9, 9}, {5, 10}, {6, 10}, {7, 10}, {8, 10}, {6, 11}, {7, 11}};
    // actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
    // EXPECT_EQ(actual_free_coords, expected_free_coords);

    // free_coords = battleMap->getFreeCoordsInCartesianRange(coords, blaze::DynamicVector<double>(), Size::LARGE, 2, test_goblin->_id);
    // expected_free_coords = {{6, 6}, {6, 8}, {7, 8}, {6, 9}, {7, 9}, {7, 6}, {5, 7}, {6, 7}, {7, 7}, {8, 7}, {4, 8}, {5, 8}, {8, 8}, {9, 8}, {4, 9}, {5, 9}, {8, 9}, {9, 9}, {5, 10}, {6, 10}, {7, 10}, {8, 10}, {6, 11}, {7, 11}};
    // actual_free_coords = std::set<Coord>(free_coords.begin(), free_coords.end());
    // EXPECT_EQ(actual_free_coords, expected_free_coords);
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

// TEST_F(BattleMapTest, ComplexPathTest) {
//     BattleMap battleMap;
//     Coord src = {0, 0};
//     Coord dest = {14, 14};

//     auto result = battleMap.dijkstra(src, N, adjMatrix, mask);

//     // Check the distance to the farthest cell (bottom-right corner)
//     int destIdx = dest[0] * N + dest[1];
//     EXPECT_LT(result.dist[destIdx], std::numeric_limits<int>::max());

//     // Check the shortest path near the obstacle
//     Coord pathAroundObstacle = result.shortestPaths[6][8];
//     EXPECT_EQ(pathAroundObstacle, (Coord{6, 7}));  // Should go around the obstacle
// }

// TEST_F(BattleMapTest, NoPathDueToObstacle) {
//     BattleMap battleMap;
//     Coord src = {0, 0};
    
//     // Add an obstacle that blocks the path entirely
//     for (int i = 1; i < N; ++i) {
//         addObstacle({i, 0});  // Block the entire first column except the source
//     }
    
//     auto result = battleMap.dijkstra(src, N, adjMatrix, mask);

//     // All distances except the starting node should be maxsize
//     for (int i = 1; i < N * N; ++i) {
//         EXPECT_EQ(result.dist[i], std::numeric_limits<int>::max());
//     }

//     // Shortest paths should remain as initialized (-1, -1) for unreachable nodes
//     for (int i = 0; i < N; ++i) {
//         for (int j = 1; j < N; ++j) {
//             EXPECT_EQ(result.shortestPaths(i, j), (Coord{-1, -1}));
//         }
//     }
// }


// TEST_F(BattleMapTest, EmptyGrid) {
//     Coord src{7, 7}; // Start from the center
//     auto result = battleMap.dijkstra(src, SIZE, adjMatrix, mask);

//     EXPECT_EQ(getDistance(result.dist, 7, 7), 0);
//     EXPECT_EQ(getDistance(result.dist, 7, 8), 1);
//     EXPECT_EQ(getDistance(result.dist, 8, 8), 2);
//     EXPECT_EQ(getDistance(result.dist, 0, 0), 14);
//     EXPECT_EQ(getDistance(result.dist, 14, 14), 14);
// }

// TEST_F(BattleMapTest, WithObstacles) {
//     // Place some obstacles
//     setImpassable(5, 5);
//     setImpassable(5, 6);
//     setImpassable(5, 7);
//     setImpassable(6, 7);
//     setImpassable(7, 7);

//     Coord src{4, 6}; // Start just left of the obstacles
//     auto result = battleMap.dijkstra(src, SIZE, adjMatrix, mask);

//     EXPECT_EQ(getDistance(result.dist, 4, 6), 0);
//     EXPECT_EQ(getDistance(result.dist, 6, 6), 2); // Have to go around
//     EXPECT_EQ(getDistance(result.dist, 8, 8), 6); // Have to go around

//     // Check path
//     Coord current{8, 8};
//     std::vector<Coord> path;
//     while (current[0] != -1 && current[1] != -1) {
//         path.push_back(current);
//         current = getShortestPathNext(result.shortestPaths, current[0], current[1]);
//     }
//     EXPECT_EQ(path.size(), 7); // [8,8] -> [7,8] -> [6,8] -> [6,6] -> [5,6] -> [4,6]
// }

// TEST_F(BattleMapTest, Unreachable) {
//     // Create a wall dividing the grid
//     for (int i = 0; i < SIZE; ++i) {
//         setImpassable(7, i);
//     }

//     Coord src{0, 0};
//     auto result = battleMap.dijkstra(src, SIZE, adjMatrix, mask);

//     EXPECT_EQ(getDistance(result.dist, 0, 0), 0);
//     EXPECT_EQ(getDistance(result.dist, 7, 0), std::numeric_limits<int>::max());
//     EXPECT_EQ(getDistance(result.dist, 14, 14), std::numeric_limits<int>::max());
// }

// TEST_F(BattleMapTest, CombatantPositions) {
//     // Place combatants (treated as obstacles for this test)
//     setImpassable(3, 3);
//     setImpassable(10, 10);

//     Coord src{0, 0};
//     auto result = battleMap.dijkstra(src, SIZE, adjMatrix, mask);

//     EXPECT_EQ(getDistance(result.dist, 3, 3), std::numeric_limits<int>::max());
//     EXPECT_EQ(getDistance(result.dist, 10, 10), std::numeric_limits<int>::max());
//     EXPECT_EQ(getDistance(result.dist, 4, 4), 8); // Have to go around combatant
// }

// TEST_F(BattleMapTest, EdgeCases) {
//     Coord src{0, 0};
//     auto result = battleMap.dijkstra(src, SIZE, adjMatrix, mask);

//     // Test corners
//     EXPECT_EQ(getDistance(result.dist, 0, 14), 14);
//     EXPECT_EQ(getDistance(result.dist, 14, 0), 14);
//     EXPECT_EQ(getDistance(result.dist, 14, 14), 28);

//     // Test edge midpoints
//     EXPECT_EQ(getDistance(result.dist, 0, 7), 7);
//     EXPECT_EQ(getDistance(result.dist, 7, 0), 7);
//     EXPECT_EQ(getDistance(result.dist, 14, 7), 21);
//     EXPECT_EQ(getDistance(result.dist, 7, 14), 21);
// }