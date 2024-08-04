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

class BattleMapTest : public ::testing::Test {
protected:
    BattleMap* battle_map;
    std::unique_ptr<Goblin> test_goblin;

    void SetUp() override {
        BattleMap::resetInstance(); // Reset the singleton instance before each test
        battle_map = &BattleMap::getInstance();
        test_goblin = std::make_unique<Goblin>(1);
    }
};

TEST_F(BattleMapTest, GetFreeCoordinatesInHopRangeMedium) {
    battle_map->setCombatantCoordinates(*test_goblin, Coord({5, 7}));
    Coord coords{5, 7};
    
    auto adj = battle_map->getFreeCoordsInHopRange(
        Coords{{5, 7}},
        blaze::DynamicVector<double>(),
        static_cast<int>(Size::MEDIUM),
        1,
        -1
    );

    std::set<Coord> expected_adj = {
        {4, 7}, {6, 7}, {4, 8}, {5, 8}, {6, 8}, {4, 6}, {5, 6}, {6, 6}
    };
    std::set<Coord> actual_adj(adj.begin(), adj.end());
    EXPECT_EQ(actual_adj, expected_adj);

    // Test including the combatant's own coord
    adj = battle_map->getFreeCoordsInHopRange(
        Coords{{5, 7}},
        blaze::DynamicVector<double>(),
        static_cast<int>(Size::MEDIUM),
        1,
        test_goblin->_id
    );

    expected_adj = {
        {4, 7}, {5, 7}, {6, 7}, {4, 8}, {5, 8}, {6, 8}, {4, 6}, {5, 6}, {6, 6}
    };
    actual_adj = std::set<Coord>(adj.begin(), adj.end());
    EXPECT_EQ(actual_adj, expected_adj);
}

TEST_F(BattleMapTest, GetFreeCoordinatesInHopRangeLarge) {
    test_goblin->setSize(Size::LARGE);
    battle_map->setCombatantCoordinates(*test_goblin, Coord({5, 7}));
    auto large_goblin_coords = battle_map->getCombatantCoordinates(*test_goblin);

    auto adj = battle_map->getFreeCoordsInHopRange(
        large_goblin_coords,
        blaze::DynamicVector<double>(),
        static_cast<int>(Size::MEDIUM),
        1,
        -1
    );

    std::set<Coord> expected_adj = {
        {4, 6}, {4, 7}, {4, 8}, {4, 9}, {5, 6}, {5, 9}, {6, 6}, {6, 9}, {7, 6}, {7, 7}, {7, 8}, {7, 9}
    };
    std::set<Coord> actual_adj(adj.begin(), adj.end());
    EXPECT_EQ(actual_adj, expected_adj);

    // Test including the combatant's own coord
    adj = battle_map->getFreeCoordsInHopRange(
        large_goblin_coords,
        blaze::DynamicVector<double>(),
        static_cast<int>(Size::MEDIUM),
        1,
        test_goblin->_id
    );

    expected_adj = {
        {4, 6}, {5, 7}, {6, 7}, {5, 8}, {6, 8}, {4, 7}, {4, 8}, {4, 9}, {5, 6}, {5, 9}, {6, 6}, {6, 9}, {7, 6}, {7, 7}, {7, 8}, {7, 9}
    };
    actual_adj = std::set<Coord>(adj.begin(), adj.end());
    EXPECT_EQ(actual_adj, expected_adj);
}