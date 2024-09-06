#include <gtest/gtest.h>
#include "core/misc.hpp"

using namespace enc;

namespace
{
  TEST(RollTypeTest, AdvantageAndDisadvantage) { EXPECT_EQ(reconcileRollTypes(RollType::ADVANTAGE | RollType::DISADVANTAGE), RollType::STRAIGHT); }
  TEST(RollTypeTest, MultipleAdvantagesAndDisadvantage)
  {
    EXPECT_EQ(reconcileRollTypes(RollType::ADVANTAGE | RollType::DISADVANTAGE | RollType::ADVANTAGE), RollType::STRAIGHT);
  }
  TEST(RollTypeTest, MultipleDisadvantagesAndAdvantage)
  {
    EXPECT_EQ(reconcileRollTypes(RollType::ADVANTAGE | RollType::DISADVANTAGE | RollType::DISADVANTAGE), RollType::STRAIGHT);
  }

  TEST(RollTypeTest, MultipleAdvantages) { EXPECT_EQ(reconcileRollTypes(RollType::ADVANTAGE | RollType::ADVANTAGE), RollType::ADVANTAGE); }

  TEST(RollTypeTest, SingleDisadvantage) { EXPECT_EQ(reconcileRollTypes(RollType::DISADVANTAGE), RollType::DISADVANTAGE); }

  TEST(RollTypeTest, Straight) { EXPECT_EQ(reconcileRollTypes(RollType::STRAIGHT), RollType::STRAIGHT); }

  TEST(RollTypeTest, AdvantageAndStraight) { EXPECT_EQ(reconcileRollTypes(RollType::ADVANTAGE | RollType::STRAIGHT), RollType::ADVANTAGE); }

  TEST(RollTypeTest, DisadvantageAndStraight) { EXPECT_EQ(reconcileRollTypes(RollType::DISADVANTAGE | RollType::STRAIGHT), RollType::DISADVANTAGE); }

  TEST(RollTypeTest, AllTypes)
  {
    EXPECT_EQ(reconcileRollTypes(RollType::ADVANTAGE | RollType::DISADVANTAGE | RollType::STRAIGHT), RollType::STRAIGHT);
  }

  TEST(FetRollTypeDelta, GetRollTypeDeltaStraight)
  {
    EXPECT_EQ(getRollTypeDelta(RollType::STRAIGHT, 10), 0);
    EXPECT_EQ(getRollTypeDelta(RollType::STRAIGHT, 20), 0);
  }

  TEST(FetRollTypeDelta, GetRollTypeDeltaAdvantage)
  {
    EXPECT_EQ(getRollTypeDelta(RollType::ADVANTAGE, 10), 5);
    EXPECT_EQ(getRollTypeDelta(RollType::ADVANTAGE, 20), 1);
    EXPECT_EQ(getRollTypeDelta(RollType::ADVANTAGE, 17), 3);
  }

  TEST(FetRollTypeDelta, GetRollTypeDeltaDisadvantage)
  {
    EXPECT_EQ(getRollTypeDelta(RollType::DISADVANTAGE, 10), -5);
    EXPECT_EQ(getRollTypeDelta(RollType::DISADVANTAGE, 20), -1);
    EXPECT_EQ(getRollTypeDelta(RollType::DISADVANTAGE, 17), -3);
  }

  TEST(FetRollTypeDelta, GetRollTypeDeltaInvalidKey)
  {
    EXPECT_EQ(getRollTypeDelta(RollType::ADVANTAGE, 21), 0); // 21 is not in the map, should return default
  }

  TEST(FetRollTypeDelta, GetRollTypeDeltaCustomDefault)
  {
    EXPECT_EQ(getRollTypeDelta(RollType::ADVANTAGE, 21, -1), -1); // Custom default value
  }

  TEST(GenerateOutcomes, ForD6)
  {
    Die d6 = {1, 6};
    auto outcomes = generateOutcomes(d6);
    ASSERT_EQ(outcomes.size(), 6);
    std::vector<int> expected = {1, 2, 3, 4, 5, 6};
    EXPECT_EQ(outcomes, expected);
  }

  TEST(GenerateOutcomes, For2D4)
  {
    Die d4 = {2, 4};
    auto outcomes = generateOutcomes(d4);
    ASSERT_EQ(outcomes.size(), 16);
    // Check for correct range of outcomes
    EXPECT_EQ(*std::min_element(outcomes.begin(), outcomes.end()), 2);
    EXPECT_EQ(*std::max_element(outcomes.begin(), outcomes.end()), 8);
    EXPECT_EQ(std::count(outcomes.cbegin(), outcomes.cend(), 2), 1);
    EXPECT_EQ(std::count(outcomes.cbegin(), outcomes.cend(), 3), 2);
    EXPECT_EQ(std::count(outcomes.cbegin(), outcomes.cend(), 4), 3);
    // Check for specific common outcomes
    EXPECT_TRUE(std::find(outcomes.begin(), outcomes.end(), 5) != outcomes.end());
    EXPECT_TRUE(std::find(outcomes.begin(), outcomes.end(), 7) != outcomes.end());
    EXPECT_TRUE(std::find(outcomes.begin(), outcomes.end(), 1) == outcomes.end());
    EXPECT_TRUE(std::find(outcomes.begin(), outcomes.end(), 9) == outcomes.end());
  }

  TEST(GenerateOutcomes, For3D6) {
    Die d6 = {3, 6};
    auto outcomes = generateOutcomes(d6);
    ASSERT_EQ(outcomes.size(), 216);  // 6^3
    EXPECT_EQ(*std::min_element(outcomes.begin(), outcomes.end()), 3);
    EXPECT_EQ(*std::max_element(outcomes.begin(), outcomes.end()), 18);
    EXPECT_EQ(std::count(outcomes.cbegin(), outcomes.cend(), 3), 1);
    EXPECT_EQ(std::count(outcomes.cbegin(), outcomes.cend(), 4), 3);
    EXPECT_EQ(std::count(outcomes.cbegin(), outcomes.cend(), 5), 6);
}

  // Tests for find_percentile_value
  TEST(FindPercentileValue, Median)
  {
    std::vector<int> values = {1, 2, 3, 4, 5};
    EXPECT_EQ(findPercentileValue(values, 50), 3);
  }

  TEST(FindPercentileValue, 90th)
  {
    std::vector<int> values = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    EXPECT_EQ(findPercentileValue(values, 90), 9);
  }

  // Tests for percentile_roll
  TEST(PercentileRoll, D6Median)
  {
    Die d6 = {1, 6};                      // 1d6
    EXPECT_EQ(percentileRoll(d6, 50), 3); // Median of 1d6 is 3.5, rounded down to 3
  }

  TEST(PercentileRoll, 2D6_92nd)
  {
    Die d6 = {2, 6};                       // 2d6
    EXPECT_EQ(percentileRoll(d6, 92), 11); // 92nd percentile of 2d6 is 11
  }

  // Tests for percent_of_curr_hp
  TEST(PercentOfCurrHp, PercentOfCurrHPHalf) { EXPECT_DOUBLE_EQ(percentOfCurrHp(100, 50), 50.0); }

  TEST(PercentOfCurrHp, PercentOfCurrHPQuarter) { EXPECT_DOUBLE_EQ(percentOfCurrHp(100, 25), 25.0); }

  TEST(PercentOfCurrHp, PercentOfCurrHPZeroDamage) { EXPECT_DOUBLE_EQ(percentOfCurrHp(100, 0), 0.0); }

  // Optional: Test for edge cases and error handling
  TEST(PercentileRoll, PercentileRollInvalidPercentile)
  {
    Die d6 = {1, 6};
    EXPECT_THROW(percentileRoll(d6, 101), std::invalid_argument);
    EXPECT_THROW(percentileRoll(d6, -1), std::invalid_argument);
  }
}