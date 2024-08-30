#include <gtest/gtest.h>
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
