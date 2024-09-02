#include <gtest/gtest.h>
#include <blaze/Math.h>
#include "core/battle_map.hpp"
#include "core/misc.hpp"
#include "core/geometry.hpp"
#include "core/combatant.hpp"
#include "core/coords.hpp"
#include "spells/spell_stats.hpp"
#include "combatants/goblin.hpp"
#include "combatants/draconic_sorcerer_lvl_1.hpp"
#include <set>
#include <algorithm>
#include <memory>

using namespace enc;

namespace {

bool vectorEqual(const Vector2D& a, const Vector2D& b, double epsilon = 1e-6) {
    return std::abs(a[0] - b[0]) < epsilon && std::abs(a[1] - b[1]) < epsilon;
}

bool coordEqual(const Coord &a, const Coord &b) { return a[0] == b[0] && a[1] == b[1]; }

Vector2D normalize(const Vector2D& v) {
    return v / blaze::length(v);
}

class getHopDistance : public ::testing::Test
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

TEST_F(getHopDistance, HopDistanceDiagonalMedium) {
    battle_map->setCombatantCoordinates(*test_draconic_sorcerer_lvl_1, Coord{0, 0});
    battle_map->setCombatantCoordinates(*test_goblin, Coord{4, 4});

    auto draconic_sorcerer_coords = battle_map->getCombatantCoordinates(*test_draconic_sorcerer_lvl_1);
    auto goblin_coords = battle_map->getCombatantCoordinates(*test_goblin);

    EXPECT_EQ(battle_map->getHopDistanceCombatants(*test_draconic_sorcerer_lvl_1, *test_goblin), 4) 
        << "Incorrect distance between two large combatants";
    EXPECT_EQ(getHopDistanceCoords(draconic_sorcerer_coords, goblin_coords), 4) 
        << "Incorrect distance between two large combatants";
}

TEST_F(getHopDistance, HopDistanceDiagonalLarge) {
    test_draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    test_goblin->setSize(Size::LARGE);
    battle_map->setCombatantCoordinates(*test_draconic_sorcerer_lvl_1, Coord{0, 0});
    battle_map->setCombatantCoordinates(*test_goblin, Coord{4, 4});

    auto draconic_sorcerer_coords = battle_map->getCombatantCoordinates(*test_draconic_sorcerer_lvl_1);
    auto goblin_coords = battle_map->getCombatantCoordinates(*test_goblin);

    EXPECT_EQ(battle_map->getHopDistanceCombatants(*test_draconic_sorcerer_lvl_1, *test_goblin), 3) 
        << "Incorrect distance between two large combatants";
    EXPECT_EQ(getHopDistanceCoords(draconic_sorcerer_coords, goblin_coords), 3) 
        << "Incorrect distance between two large combatants";
}

TEST_F(getHopDistance, HopDistanceSameY) {
    test_draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    test_goblin->setSize(Size::LARGE);
    battle_map->setCombatantCoordinates(*test_draconic_sorcerer_lvl_1, Coord{0, 0});
    battle_map->setCombatantCoordinates(*test_goblin, Coord{6, 0});

    auto draconic_sorcerer_coords = battle_map->getCombatantCoordinates(*test_draconic_sorcerer_lvl_1);
    auto goblin_coords = battle_map->getCombatantCoordinates(*test_goblin);

    EXPECT_EQ(battle_map->getHopDistanceCombatants(*test_draconic_sorcerer_lvl_1, *test_goblin), 5) 
        << "Incorrect distance between two large combatants";
    EXPECT_EQ(getHopDistanceCoords(draconic_sorcerer_coords, goblin_coords), 5) 
        << "Incorrect distance between two large combatants";
}

TEST_F(getHopDistance, HopDistanceSameX) {
    test_draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    test_goblin->setSize(Size::LARGE);
    battle_map->setCombatantCoordinates(*test_draconic_sorcerer_lvl_1, Coord{0, 0});
    battle_map->setCombatantCoordinates(*test_goblin, Coord{0, 4});

    auto draconic_sorcerer_coords = battle_map->getCombatantCoordinates(*test_draconic_sorcerer_lvl_1);
    auto goblin_coords = battle_map->getCombatantCoordinates(*test_goblin);

    EXPECT_EQ(battle_map->getHopDistanceCombatants(*test_draconic_sorcerer_lvl_1, *test_goblin), 3) 
        << "Incorrect distance between two large combatants";
    EXPECT_EQ(getHopDistanceCoords(draconic_sorcerer_coords, goblin_coords), 3) 
        << "Incorrect distance between two large combatants";
}

TEST_F(getHopDistance, HopDistanceRandom) {
    test_draconic_sorcerer_lvl_1->setSize(Size::LARGE);
    test_goblin->setSize(Size::LARGE);
    battle_map->setCombatantCoordinates(*test_draconic_sorcerer_lvl_1, Coord{0, 0});
    battle_map->setCombatantCoordinates(*test_goblin, Coord{3, 5});

    auto draconic_sorcerer_coords = battle_map->getCombatantCoordinates(*test_draconic_sorcerer_lvl_1);
    auto goblin_coords = battle_map->getCombatantCoordinates(*test_goblin);

    EXPECT_EQ(battle_map->getHopDistanceCombatants(*test_draconic_sorcerer_lvl_1, *test_goblin), 4) 
        << "Incorrect distance between two large combatants";
    EXPECT_EQ(getHopDistanceCoords(draconic_sorcerer_coords, goblin_coords), 4) 
        << "Incorrect distance between two large combatants";
}


TEST(getAffectedByCone, Cone15Feet) {
    std::set<Coord> coords = getAffectedByCone({2, 0}, 45, TRANSLATE_CONE.at(SpellTarget::CONE_15), 15);
    std::set<Coord> expectedCoords = {{3, 1}, {4, 1}, {3, 2}, {4, 2}};
    EXPECT_EQ(coords, expectedCoords);

    coords = getAffectedByCone({2, 0}, 29, TRANSLATE_CONE.at(SpellTarget::CONE_15), 15);
    expectedCoords = {{2, 1}, {3, 1}, {2, 2}, {3, 2}, {4, 2}};
    EXPECT_EQ(coords, expectedCoords);

    coords = getAffectedByCone({2, 0}, 0, TRANSLATE_CONE.at(SpellTarget::CONE_15), 15);
    expectedCoords = {{2, 1}, {2, 2}, {1, 2}, {3, 2}};
    EXPECT_EQ(coords, expectedCoords);

    coords = getAffectedByCone({2, 0}, 30, TRANSLATE_CONE.at(SpellTarget::CONE_15), 15);
    expectedCoords = {{2, 1}, {2, 2}, {3, 1}, {3, 2}, {4, 2}};
    EXPECT_EQ(coords, expectedCoords);
}

TEST(getAffectedByCone, Cone30Feet) {
    std::set<Coord> coords = getAffectedByCone({4, 7}, 180, TRANSLATE_CONE.at(SpellTarget::CONE_30), 15);
    std::set<Coord> expectedCoords = {
        {2, 2}, {3, 2}, {4, 2}, {5, 2}, {6, 2}, {3, 2}, {2, 3}, {3, 3}, {4, 3}, {5, 3}, {6, 3},
        {3, 4}, {4, 4}, {5, 4}, {3, 5}, {4, 5}, {5, 5}, {4, 6}
    };
    EXPECT_EQ(coords, expectedCoords);

    coords = getAffectedByCone({1, 4}, 90, TRANSLATE_CONE.at(SpellTarget::CONE_30), 15);
    expectedCoords = {
        {2, 4}, {3, 3}, {3, 4}, {3, 5}, {4, 3}, {4, 4}, {4, 5}, {5, 2}, {5, 3}, {5, 4}, {5, 5},
        {5, 6}, {6, 2}, {6, 3}, {6, 4}, {6, 5}, {6, 6}
    };
    EXPECT_EQ(coords, expectedCoords);

    coords = getAffectedByCone({7, 4}, 270, TRANSLATE_CONE.at(SpellTarget::CONE_30), 15);
    expectedCoords = {
        {2, 2}, {2, 3}, {2, 4}, {2, 5}, {2, 6}, {3, 2}, {3, 3}, {3, 4}, {3, 5}, {3, 6}, {4, 3},
        {4, 4}, {4, 5}, {5, 3}, {5, 4}, {5, 5}, {6, 4}
    };
    EXPECT_EQ(coords, expectedCoords);
}

TEST(GetAffectedByLineTest, VerticalLine)
{
  Coord origin = {3, 3};
  double angleDeg = 0;
  double length = 5;
  double width = 1;
  int gridSize = 15;
  std::set<Coord> expectedCoords = {{{3, 3}, {3, 4}, {3, 5}, {3, 6}, {3, 7}, {3, 8}}};
  std::set<Coord> actualCoords = getAffectedByLine(origin, angleDeg, length, width, gridSize);
  EXPECT_EQ(actualCoords, expectedCoords);
}

TEST(GetAffectedByLineTest, HorizontalLine)
{
  Coord origin = {3, 3};
  double angleDeg = 90;
  double length = 5;
  double width = 1;
  int gridSize = 15;
  std::set<Coord> expectedCoords = {{{3, 3}, {4, 3}, {5, 3}, {6, 3}, {7, 3}, {8, 3}}};
  std::set<Coord> actualCoords = getAffectedByLine(origin, angleDeg, length, width, gridSize);
  EXPECT_EQ(actualCoords, expectedCoords);
}

TEST(GetAffectedByLineTest, DiagonalLine)
{
  Coord origin = {2, 2};
  double angleDeg = 45;
  double length = 4;
  double width = 2;
  int gridSize = 15;
  std::set<Coord> expectedCoords = {{{4, 4}, {3, 4}, {4, 3}, {5, 4}, {2, 3}, {4, 5}, {3, 3}, {2, 2}, {3, 2}}};
  std::set<Coord> actualCoords = getAffectedByLine(origin, angleDeg, length, width, gridSize);
  EXPECT_EQ(actualCoords, expectedCoords);
}

TEST(GetAffectedByLineTest, AngleGreaterThan180)
{
  Coord origin = {3, 3};
  double angleDeg = 270;
  double length = 5;
  double width = 1;
  int gridSize = 15;
  std::set<Coord> expectedCoords = {{{2, 3}, {0, 3}, {1, 3}, {3, 3}}};
  std::set<Coord> actualCoords = getAffectedByLine(origin, angleDeg, length, width, gridSize);
  EXPECT_EQ(actualCoords, expectedCoords);
}

TEST(GetAffectedByLineTest, OriginAtEdge)
{
  Coord origin = {0, 0};
  double angleDeg = 180;
  double length = 5;
  double width = 1;
  int gridSize = 15;
  std::set<Coord> expectedCoords = {{{0, 0}}};
  std::set<Coord> actualCoords = getAffectedByLine(origin, angleDeg, length, width, gridSize);
  EXPECT_EQ(actualCoords, expectedCoords);
}

TEST(GetAffectedByLineTest, OriginAtOppositeEdge)
{
  Coord origin = {12, 7};
  double angleDeg = 90;
  double length = 5;
  double width = 1;
  int gridSize = 15;
  std::set<Coord> expectedCoords = {{{12, 7}, {13, 7}, {14, 7}}};
  std::set<Coord> actualCoords = getAffectedByLine(origin, angleDeg, length, width, gridSize);
  EXPECT_EQ(actualCoords, expectedCoords);
}

TEST(GetAffectedByLineTest, LineWidth3)
{
  Coord origin = {3, 3};
  double angleDeg = 45;
  double length = 5;
  double width = 3;
  int gridSize = 15;
  std::set<Coord> expectedCoords = {{{3, 4}, {4, 3}, {5, 4}, {4, 6}, {5, 7}, {6, 5}, {4, 5},
                                     {3, 3}, {5, 6}, {5, 3}, {2, 4}, {6, 4}, {6, 7}, {7, 6},
                                     {3, 5}, {4, 4}, {5, 5}, {6, 6}, {7, 5}}};
  std::set<Coord> actualCoords = getAffectedByLine(origin, angleDeg, length, width, gridSize);
  EXPECT_EQ(actualCoords, expectedCoords);
}

TEST(AffectedBySquareAoETest, SquareAoECenterOfMap) {
    Coord origin = {7, 7};
    int length = 3;
    auto affectedCoords = getCoordsAffectedBySquareAoE(origin, length, 15);

    ASSERT_EQ(affectedCoords.size(), 9);
    EXPECT_TRUE(std::find(affectedCoords.begin(), affectedCoords.end(), Coord{7, 7}) != affectedCoords.end());
    EXPECT_TRUE(std::find(affectedCoords.begin(), affectedCoords.end(), Coord{8, 8}) != affectedCoords.end());
    EXPECT_TRUE(std::find(affectedCoords.begin(), affectedCoords.end(), Coord{9, 9}) != affectedCoords.end());
}

TEST(AffectedBySquareAoETest, SquareAoECornerOfMap) {
    Coord origin = {0, 0};
    int length = 2;
    auto affectedCoords = getCoordsAffectedBySquareAoE(origin, length, 15);

    ASSERT_EQ(affectedCoords.size(), 4);
    EXPECT_TRUE(std::find(affectedCoords.begin(), affectedCoords.end(), Coord{0, 0}) != affectedCoords.end());
    EXPECT_TRUE(std::find(affectedCoords.begin(), affectedCoords.end(), Coord{1, 1}) != affectedCoords.end());
}

TEST(AffectedBySquareAoETest, SquareAoEPartiallyOffMap) {
    Coord origin = {13, 13};
    int length = 3;
    auto affectedCoords = getCoordsAffectedBySquareAoE(origin, length, 15);

    ASSERT_EQ(affectedCoords.size(), 4);
    EXPECT_TRUE(std::find(affectedCoords.begin(), affectedCoords.end(), Coord{13, 13}) != affectedCoords.end());
    EXPECT_TRUE(std::find(affectedCoords.begin(), affectedCoords.end(), Coord{14, 14}) != affectedCoords.end());
}

TEST(AffectedBySquareAoETest, SquareAoECompletelyOffMap) {
    Coord origin = {15, 15};
    int length = 2;
    auto affectedCoords = getCoordsAffectedBySquareAoE(origin, length, 15);

    EXPECT_TRUE(affectedCoords.empty());
}

TEST(AffectedBySquareAoETest, SquareAoELargeSize) {
    Coord origin = {0, 0};
    int length = 15;
    auto affectedCoords = getCoordsAffectedBySquareAoE(origin, length, 15);

    ASSERT_EQ(affectedCoords.size(), 225);
    EXPECT_TRUE(std::find(affectedCoords.begin(), affectedCoords.end(), Coord{0, 0}) != affectedCoords.end());
    EXPECT_TRUE(std::find(affectedCoords.begin(), affectedCoords.end(), Coord{14, 14}) != affectedCoords.end());
}

TEST(AffectedBySquareAoETest, SquareAoESizeOne) {
    Coord origin = {7, 7};
    int length = 1;
    auto affectedCoords = getCoordsAffectedBySquareAoE(origin, length, 15);

    ASSERT_EQ(affectedCoords.size(), 1);
    EXPECT_EQ(affectedCoords[0], (Coord{7, 7}));
}

TEST(FindFovVectorsTest, DirectlySideBySide) {
    auto outlines = findFovVectors(Coords({3, 7}, Size::MEDIUM), Coords({6, 6}, Size::HUGE));
    Vector2D expected1 = normalize(Vector2D{2.5, 1.5});
    Vector2D expected2 = normalize(Vector2D{2.5, -1.5});
    EXPECT_TRUE(vectorEqual(outlines.first, expected1) || vectorEqual(outlines.second, expected1));
    EXPECT_TRUE(vectorEqual(outlines.first, expected2) || vectorEqual(outlines.second, expected2));
}

TEST(FindFovVectorsTest, SwappedObserverAndTarget) {
    auto outlines = findFovVectors(Coords({6, 6}, Size::HUGE), Coords({3, 7}, Size::MEDIUM));
    Vector2D expected1 = normalize(Vector2D{-3.5, 0.5});
    Vector2D expected2 = normalize(Vector2D{-3.5, -0.5});
    EXPECT_TRUE(vectorEqual(outlines.first, expected1) || vectorEqual(outlines.second, expected1));
    EXPECT_TRUE(vectorEqual(outlines.first, expected2) || vectorEqual(outlines.second, expected2));
}

TEST(FindFovVectorsTest, SlightAngle) {
    auto outlines = findFovVectors(Coords({0, 0}, Size::HUGE), Coords({5, 2}, Size::LARGE));
    Vector2D expected1 = normalize(Vector2D{3.5, 2.5});
    Vector2D expected2 = normalize(Vector2D{5.5, 0.5});
    EXPECT_TRUE(vectorEqual(outlines.first, expected1) || vectorEqual(outlines.second, expected1));
    EXPECT_TRUE(vectorEqual(outlines.first, expected2) || vectorEqual(outlines.second, expected2));
}

TEST(FindFovVectorsTest, BreakingPoint1) {
    auto outlines = findFovVectors(Coords({5, 2}, Size::MEDIUM), Coords({6, 6}, Size::HUGE));
    Vector2D expected1 = normalize(Vector2D{3.5, 3.5});
    Vector2D expected2 = normalize(Vector2D{0.5, 6.5});
    EXPECT_TRUE(vectorEqual(outlines.first, expected1) || vectorEqual(outlines.second, expected1));
    EXPECT_TRUE(vectorEqual(outlines.first, expected2) || vectorEqual(outlines.second, expected2));
}

TEST(FindFovVectorsTest, BreakingPoint2) {
    auto outlines = findFovVectors(Coords({6, 2}, Size::MEDIUM), Coords({6, 6}, Size::HUGE));
    Vector2D expected1 = normalize(Vector2D{-0.5, 3.5});
    Vector2D expected2 = normalize(Vector2D{2.5, 3.5});
    EXPECT_TRUE(vectorEqual(outlines.first, expected1) || vectorEqual(outlines.second, expected1));
    EXPECT_TRUE(vectorEqual(outlines.first, expected2) || vectorEqual(outlines.second, expected2));
}

TEST(AngleBetweenVectorsTest, AngleBetweenVectors)
{
  EXPECT_NEAR(angleBetweenVectors(Vector2D{0, 1}, Vector2D{1, 0}), 90.0, 1e-4);
  EXPECT_NEAR(angleBetweenVectors(Vector2D{0, 1}, Vector2D{1, -1}), 135.0, 1e-4);
  EXPECT_NEAR(angleBetweenVectors(Vector2D{0, 1}, Vector2D{0, -1}), 180.0, 1e-4);
  EXPECT_NEAR(angleBetweenVectors(Vector2D{0, 2}, Vector2D{-1, 2}), 26.5650, 1e-4);
  EXPECT_NEAR(angleBetweenVectors(Vector2D{1, 0.5}, Vector2D{1.5, -1}), 60.2551, 1e-4);
  EXPECT_NEAR(angleBetweenVectors(Vector2D{6, 4}, Vector2D{6, 4}), 0.0, 1e-4);
  EXPECT_NEAR(angleBetweenVectors(Vector2D{0, 4}, Vector2D{4, 4}), 45.0, 1e-4);
}

TEST(AngleBetweenVectorsTest, AngleBetweenVectorsRad)
{
  EXPECT_NEAR(angleBetweenVectorsRad(Vector2D{0, 1}, Vector2D{1, 0}), M_PI / 2, 1e-4);
  EXPECT_NEAR(angleBetweenVectorsRad(Vector2D{0, 1}, Vector2D{1, -1}), M_PI * 3 / 4, 1e-4);
  EXPECT_NEAR(angleBetweenVectorsRad(Vector2D{0, 1}, Vector2D{0, -1}), M_PI, 1e-4);
  EXPECT_NEAR(angleBetweenVectorsRad(Vector2D{0, 2}, Vector2D{-1, 2}), 0.463647609, 1e-4);     // radians for 26.5650 degrees
  EXPECT_NEAR(angleBetweenVectorsRad(Vector2D{1, 0.5}, Vector2D{1.5, -1}), 1.051650213, 1e-4); // radians for 60.2551 degrees
  EXPECT_NEAR(angleBetweenVectorsRad(Vector2D{6, 4}, Vector2D{6, 4}), 0.0, 1e-4);
  EXPECT_NEAR(angleBetweenVectorsRad(Vector2D{0, 4}, Vector2D{4, 4}), M_PI / 4, 1e-4);
}

TEST(GetBoundingBoxTest, TwoCombatantsSameSize) {
    Coords coord1({1, 1}, Size::MEDIUM);
    Coords coord2({3, 3}, Size::MEDIUM);
    auto [bottom_left, top_right] = getBoundingBox(coord1.get(), coord2.get());
    EXPECT_TRUE(coordEqual(bottom_left, {1, 1}));
    EXPECT_TRUE(coordEqual(top_right, {3, 3}));
}

TEST(GetBoundingBoxTest, TwoCombatantsDifferentSizes) {
    Coords coord1({0, 0}, Size::SMALL);
    Coords coord2({4, 4}, Size::LARGE);
    auto [bottom_left, top_right] = getBoundingBox(coord1.get(), coord2.get());
    EXPECT_TRUE(coordEqual(bottom_left, {0, 0}));
    EXPECT_TRUE(coordEqual(top_right, {5, 5}));
}

TEST(GetBoundingBoxTest, TwoCombatantsOverlappingPositions) {
    Coords coord1({2, 2}, Size::HUGE);
    Coords coord2({3, 3}, Size::GARGANTUAN);
    auto [bottom_left, top_right] = getBoundingBox(coord1.get(), coord2.get());
    EXPECT_TRUE(coordEqual(bottom_left, {2, 2}));
    EXPECT_TRUE(coordEqual(top_right, {6, 6}));
}

TEST(GetBoundingBoxTest, TwoCombatantsSamePosition) {
    Coords coord1({0, 0}, Size::TINY);
    Coords coord2({0, 0}, Size::TINY);
    auto [bottom_left, top_right] = getBoundingBox(coord1.get(), coord2.get());
    EXPECT_TRUE(coordEqual(bottom_left, {0, 0}));
    EXPECT_TRUE(coordEqual(top_right, {0, 0}));
}

TEST(GetBoundingBoxTest, HugeAndLarge) {
    Coords coord1({1, 11}, Size::HUGE);
    Coords coord2({9, 13}, Size::LARGE);
    auto [bottom_left, top_right] = getBoundingBox(coord1.get(), coord2.get());
    EXPECT_TRUE(coordEqual(bottom_left, {1, 11}));
    EXPECT_TRUE(coordEqual(top_right, {10, 14}));
}
}
