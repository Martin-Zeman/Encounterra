#include <gtest/gtest.h>
#include "battle_map.hpp"
#include "misc.hpp"
#include "geometry.hpp"
#include "combatant.hpp"
#include <set>
#include <algorithm>

using namespace enc;

class BattleMapTest : public ::testing::Test {
protected:
    BattleMap& battle_map = BattleMap::getInstance();
    Combatant test_draconic_sorcerer_5lvl;

    void SetUp() override {
        // Initialize your battle map and test combatant here
        battle_map.initializeGrid();
        test_draconic_sorcerer_5lvl = Combatant(1, "Test Sorcerer", Size::MEDIUM);
    }
};

TEST_F(BattleMapTest, GetFreeCoordinatesInHopRangeMedium) {
    battle_map.setGridValue(5, 7, test_draconic_sorcerer_5lvl.getId());
    Coord coords{5, 7};
    
    auto adj = battle_map.getFreeCoordsInHopRange(
        blaze::DynamicMatrix<double>{{5.0, 7.0}},
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
    adj = battle_map.getFreeCoordsInHopRange(
        blaze::DynamicMatrix<double>{{5.0, 7.0}},
        blaze::DynamicVector<double>(),
        static_cast<int>(Size::MEDIUM),
        1,
        test_draconic_sorcerer_5lvl.getId()
    );

    expected_adj = {
        {4, 7}, {5, 7}, {6, 7}, {4, 8}, {5, 8}, {6, 8}, {4, 6}, {5, 6}, {6, 6}
    };
    actual_adj = std::set<Coord>(adj.begin(), adj.end());
    EXPECT_EQ(actual_adj, expected_adj);
}

TEST_F(BattleMapTest, GetFreeCoordinatesInHopRangeLarge) {
    test_draconic_sorcerer_5lvl.setSize(Size::LARGE);
    battle_map.setGridValue(5, 7, test_draconic_sorcerer_5lvl.getId());
    battle_map.setGridValue(6, 7, test_draconic_sorcerer_5lvl.getId());
    battle_map.setGridValue(5, 8, test_draconic_sorcerer_5lvl.getId());
    battle_map.setGridValue(6, 8, test_draconic_sorcerer_5lvl.getId());

    auto adj = battle_map.get_free_coords_in_hop_range(
        blaze::DynamicMatrix<double>{{5.0, 7.0}},
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
    adj = battle_map.get_free_coords_in_hop_range(
        blaze::DynamicMatrix<double>{{5.0, 7.0}},
        blaze::DynamicVector<double>(),
        static_cast<int>(Size::MEDIUM),
        1,
        test_draconic_sorcerer_5lvl.getId()
    );

    expected_adj = {
        {4, 6}, {5, 7}, {6, 7}, {5, 8}, {6, 8}, {4, 7}, {4, 8}, {4, 9}, {5, 6}, {5, 9}, {6, 6}, {6, 9}, {7, 6}, {7, 7}, {7, 8}, {7, 9}
    };
    actual_adj = std::set<Coord>(adj.begin(), adj.end());
    EXPECT_EQ(actual_adj, expected_adj);
}