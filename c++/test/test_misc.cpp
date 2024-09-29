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

  TEST(DamageCalculationTest, AvgRoll)
  {
    Die d6 = {1, 6};
    Die d8 = {1, 8};
    Die d2d12 = {2, 12};

    EXPECT_NEAR(avgRoll(d6), 3.5, 1e-6);
    EXPECT_NEAR(avgRoll(d8), 4.5, 1e-6);
    EXPECT_NEAR(avgRoll(d2d12), 13.0, 1e-6);
  }

  TEST(DamageCalculationTest, AvgRollMulti)
  {
    std::vector<Die> dice1 = {{1, 6}, {1, 8}};
    std::vector<Die> dice2 = {{2, 6}, {1, 4}};

    EXPECT_NEAR(avgRollMulti(dice1), 8.0, 1e-6);
    EXPECT_NEAR(avgRollMulti(dice2), 9.5, 1e-6);
  }

  TEST(DamageCalculationTest, CalcPHit)
  {
    EXPECT_NEAR(calcPHit(5, 15), 0.55, 1e-6);
    EXPECT_NEAR(calcPHit(0, 10), 0.55, 1e-6);
    EXPECT_NEAR(calcPHit(0, 20), 0.05, 1e-6);  // Minimum probability
    EXPECT_NEAR(calcPHit(0, 21), 0.05, 1e-6);  // Minimum probability (nat 20 still possible)
    EXPECT_NEAR(calcPHit(20, 10), 0.95, 1e-6); // Maximum probability (nat 1 still possible)
    EXPECT_NEAR(calcPHit(10, 10), 0.95, 1e-6);
  }

  TEST(DamageCalculationTest, MeanDmg)
  {
    std::vector<Die> dmgDice = {{2, 6}, {1, 8}};

    // Test normal case
    EXPECT_NEAR(meanDmg(5, dmgDice, 3, 15), 8.55, 1e-6);

    // Test with immunity
    EXPECT_DOUBLE_EQ(meanDmg(5, dmgDice, 3, 15, true), 0.0);

    // Test with resistance
    EXPECT_NEAR(meanDmg(5, dmgDice, 3, 15, false, true), 4.275, 1e-6);

    // Test with increased crit range
    EXPECT_NEAR(meanDmg(5, dmgDice, 3, 15, false, false, 2), 9.125, 1e-6);
  }

  TEST(DamageCalculationTest, MeanDmgDcAttack)
  {
    std::vector<Die> dmgDice = {{2, 6}, {1, 8}};

    // Test normal case
    EXPECT_NEAR(meanDmgDcAttack(15, dmgDice, true, 2), 9.2, 1e-6);

    // Test with immunity
    EXPECT_DOUBLE_EQ(meanDmgDcAttack(15, dmgDice, true, 2, true), 0.0);

    // Test with resistance
    EXPECT_NEAR(meanDmgDcAttack(15, dmgDice, true, 2, false, true), 4.6, 1e-6);

    // Test without half damage on success
    EXPECT_NEAR(meanDmgDcAttack(15, dmgDice, false, 2), 6.8999999999999995, 1e-6);
  }

  TEST(DamageCalculationTest, MeanDmgAutoHit)
  {
    std::vector<Die> dmgDice = {{2, 6}, {1, 8}};

    // Test normal case
    EXPECT_NEAR(meanDmgAutoHit(dmgDice), 11.5, 1e-6);

    // Test with immunity
    EXPECT_DOUBLE_EQ(meanDmgAutoHit(dmgDice, true), 0.0);    
    
    // Test with resistance
    EXPECT_NEAR(meanDmgAutoHit(dmgDice, false, true), 5.75, 1e-6);
  }

  TEST(DamageCalculationTest, RollDice)
  {
    Die die = {3, 6};
    int result = rollDice(die);
    EXPECT_GE(result, 3);
    EXPECT_LE(result, 18);
  }

  TEST(DamageCalculationTest, RollDiceMulti)
  {
    std::vector<Die> dice = {{2, 6}, {1, 8}};
    int result = rollDiceMulti(dice);
    EXPECT_GE(result, 3);
    EXPECT_LE(result, 20);
  }

  // This test checks the distribution of rollDice results
  TEST(DamageCalculationTest, RollDiceDistribution)
  {
    Die die = {1, 6};
    std::vector<int> counts(6, 0);
    int numRolls = 10000;

    for(int i = 0; i < numRolls; ++i)
      {
        int roll = rollDice(die);
        ASSERT_GE(roll, 1);
        ASSERT_LE(roll, 6);
        counts[roll - 1]++;
      }

    // Check if the distribution is roughly uniform
    double expectedCount = numRolls / 6.0;
    double chiSquared = 0.0;
    for(int count : counts)
      {
        chiSquared += std::pow(count - expectedCount, 2) / expectedCount;
      }

    // Chi-squared test with 5 degrees of freedom, 99% confidence level
    EXPECT_LT(chiSquared, 15.086); // Critical value for 99% confidence
  }
}