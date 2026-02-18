#include "core/misc.hpp"
#include <iostream>

namespace enc
{
  int getRollTypeDelta(RollType rollType, int rollNeeded, int defaultValue)
  {
    auto rollTypeIt = ROLL_TYPE_DELTA.find(rollType);
    if(rollTypeIt != ROLL_TYPE_DELTA.end())
      {
        auto keyIt = rollTypeIt->second.find(rollNeeded);
        if(keyIt != rollTypeIt->second.end())
          {
            return keyIt->second;
          }
      }
    return defaultValue;
  }

  /**
   * Reconciles multiple roll type modifiers into a single modifier.
   * If both advantage and disadvantage are present, returns straight roll.
   * Otherwise, returns the present modifier (or straight if none).
   *
   * @param types Set of roll type modifiers
   * @return The resulting single modifier
   */
  RollType reconcileRollTypes(const std::unordered_set<RollType> &types)
  {
    bool hasAdvantage = types.contains(RollType::ADVANTAGE);
    bool hasDisadvantage = types.contains(RollType::DISADVANTAGE);

    // If both are present, it's a straight roll
    if(hasAdvantage && hasDisadvantage)
      {
        return RollType::STRAIGHT;
      }

    // Return the present modifier (or STRAIGHT if none)
    if(hasAdvantage)
      {
        return RollType::ADVANTAGE;
      }
    if(hasDisadvantage)
      {
        return RollType::DISADVANTAGE;
      }

    return RollType::STRAIGHT;
  }

  std::vector<int> generateOutcomes(const Die &die)
  {
    static std::unordered_map<Die, std::vector<int>> cache;

    // Check if result is in cache
    auto it = cache.find(die);
    if(it != cache.end())
      {
        return it->second;
      }

    std::vector<int> outcomes;
    int numDice = die[0];
    int numSides = die[1];
    int total_combinations = std::pow(numSides, numDice);

    for(int i = 0; i < total_combinations; ++i)
      {
        int temp = i;
        int sum = 0;
        for(int j = 0; j < numDice; ++j)
          {
            sum += (temp % numSides) + 1;
            temp /= numSides;
          }
        outcomes.push_back(sum);
      }

    // Store result in cache
    cache[die] = outcomes;
    return outcomes;
  }

  int findPercentileValue(const std::vector<int> &outcomes, int percentile)
  {
    if(percentile < 0 || percentile > 100)
      {
        throw std::invalid_argument("Percentile must be between 0 and 100");
      }
    std::vector<int> sortedOutcomes = outcomes;
    std::sort(sortedOutcomes.begin(), sortedOutcomes.end());

    // Use nearest-rank method
    double index = (percentile / 100.0) * sortedOutcomes.size();
    return sortedOutcomes[std::ceil(index) - 1];
  }

  int percentileRoll(const Die &die, int percentile)
  {
    static std::unordered_map<std::pair<Die, int>, int> cache;

    auto cache_key = std::make_pair(die, percentile);
    auto it = cache.find(cache_key);
    if(it != cache.end())
      {
        return it->second;
      }

    auto outcomes = generateOutcomes(die);
    int result = findPercentileValue(outcomes, percentile);

    cache[cache_key] = result;
    return result;
  }

  double percentOfCurrHp(double currHp, double dmg) { return dmg / (currHp * 0.01); }

  double avgRoll(const Die &die) { return static_cast<double>(die[0]) * ((1.0 + static_cast<double>(die[1])) / 2.0); }

  double avgRollMulti(const std::vector<Die> &dice)
  {
    return std::accumulate(dice.begin(), dice.end(), 0.0, [](double sum, const Die &die) {
      return sum + static_cast<double>(die[0]) * ((1.0 + static_cast<double>(die[1])) / 2.0);
    });
  }

  /**
   * @brief Calculates mean damage of an attack-like ability.
   *
   */
  double meanDmg(int toHit, const std::vector<Die> &dmgDice, int dmgBonus, int ac, bool isImmune, bool isResistant, int critRange)
  {
    if(isImmune)
      {
        return 0.0;
      }

    // Calculate probability of hit
    double pHit = std::max(0.05, std::min(0.95, 1.0 - (std::max(0, std::min(ac - toHit - 1, 19)) / 20.0)));

    double avgDmgDieRoll = avgRollMulti(dmgDice);

    double res = (avgDmgDieRoll + dmgBonus) * pHit + 0.05 * critRange * avgDmgDieRoll;

    if(isResistant)
      {
        res /= 2.0;
      }

    return res;
  }

  /**
   * @brief Calculates the probability of hitting
   *
   * This function calculates the probability of a successful hit based on
   * the attacker's to-hit bonus and the target's Armor Class (AC).
   *
   * @param toHit The to-hit bonus of the attacker
   * @param ac The Armor Class of the target
   * @return double The probability of hitting, ranging from 0.05 to 0.95
   */
  double calcPHit(int toHit, int ac)
  {
    int minRoll = ac - toHit;
    minRoll = std::max(1, std::min(20, minRoll));
    double pHit = (21.0 - minRoll) / 20.0;
    return std::max(0.05, std::min(0.95, pHit));
  }

double meanDmgDcAttack(int dc, const std::vector<Die> &dmgDice, bool halfOnSuccess, int stBonus, bool isImmune, bool isResistant)
{
  if(isImmune)
    {
      return 0.0;
    }

  double avgDmgDieRoll = avgRollMulti(dmgDice);

  // Calculate probability of failing the saving throw
  double pFail = std::min(std::max((dc - stBonus - 1.0) / 20.0, 0.0), 1.0);

  double failDmg = avgDmgDieRoll * pFail;
  double successDmg = halfOnSuccess ? (avgDmgDieRoll / 2.0 * (1.0 - pFail)) : 0.0;
  double finalAvgDmg = failDmg + successDmg;

  return isResistant ? finalAvgDmg / 2.0 : finalAvgDmg;
}

double meanDmgAutoHit(const std::vector<Die> &dmgDice, bool isImmune, bool isResistant)
{
  if(isImmune)
    {
      return 0.0;
    }
  double avgDmgDieRoll = avgRollMulti(dmgDice);
  return isResistant ? avgDmgDieRoll / 2.0 : avgDmgDieRoll;
}

int rollDice(const Die &dice)
{
  static std::random_device rd;
  static std::mt19937 gen(rd());

  int numDice = dice[0];
  int numSides = dice[1];

  std::uniform_int_distribution<> dis(1, numSides);

  int sum = 0;
  for(int i = 0; i < numDice; ++i)
    {
      sum += dis(gen);
    }

  return sum;
}

int rollDiceMulti(const std::vector<Die> &diceList)
{
  return std::accumulate(diceList.begin(), diceList.end(), 0, [](int sum, const Die &dice) { return sum + rollDice(dice); });
  
}

// Helper function to create random number generator
inline std::mt19937 &getRNG()
{
  //! @todo: use this in the other instances too
  static std::random_device rd;
  static std::mt19937 gen(rd());
  return gen;
}

int rollDiceWithReroll(const Die &die, int rerollMaxValue)
{
  int numDice = die[0];
  int diceSides = die[1];
  std::uniform_int_distribution<> dis(1, diceSides);
  auto &gen = getRNG();

  int diceSum = 0;
  for(int i = 0; i < numDice; ++i)
    {
      int rolled = dis(gen);
      if(rolled <= rerollMaxValue)
        {
          int rerolled = dis(gen);
          std::cout << "Re-rolling " << rolled << " as " << rerolled << std::endl;
          rolled = rerolled;
        }
      diceSum += rolled;
    }

  return diceSum;
}

bool rollSavingThrow(int bonus, int dc, RollType rollType)
{
  Die d20{1, 20};
  std::uniform_int_distribution<> dis(1, 20);
  auto &gen = getRNG();

  int roll;
  switch(rollType)
    {
    case RollType::STRAIGHT: roll = dis(gen); break;

      case RollType::ADVANTAGE: {
        int roll1 = dis(gen);
        int roll2 = dis(gen);
        roll = std::max(roll1, roll2);
        break;
      }

      case RollType::DISADVANTAGE: {
        int roll1 = dis(gen);
        int roll2 = dis(gen);
        roll = std::min(roll1, roll2);
        break;
      }
    }

  if(roll == 20)
    return true;
  return roll + bonus >= dc;
}

bool rollAbilityCheck(int bonus, int dc, RollType rollType)
{
  Die d20{1, 20};
  std::uniform_int_distribution<> dis(1, 20);
  auto &gen = getRNG();

  int roll;
  switch(rollType)
    {
    case RollType::STRAIGHT: roll = dis(gen); break;

      case RollType::ADVANTAGE: {
        int roll1 = dis(gen);
        int roll2 = dis(gen);
        roll = std::max(roll1, roll2);
        break;
      }

      case RollType::DISADVANTAGE: {
        int roll1 = dis(gen);
        int roll2 = dis(gen);
        roll = std::min(roll1, roll2);
        break;
      }
    }

  return roll + bonus >= dc;
}

ChaosBoltResult rollDiceChaosBolt(const Die &die)
{
  int numDice = die[0];
  int diceSides = die[1];
  std::uniform_int_distribution<> dis(1, diceSides);
  auto &gen = getRNG();

  ChaosBoltResult result;
  result.sum = 0;

  for(int i = 0; i < numDice; ++i)
    {
      int rolled = dis(gen);
      result.sum += rolled;
      result.numbersRolled.push_back(rolled);
    }

  return result;
}

std::pair<int, std::vector<int>> rollChaosBoltDmg(const DmgDieWithType &dmgDice, const Die &additionalDmgDice)
{
  auto [primaryDmg, numbers] = rollDiceChaosBolt(dmgDice.first);
  int secondaryDmg = rollDice(additionalDmgDice);
  return {primaryDmg + secondaryDmg, numbers};
}

std::string coordToString(const Coord &coord) { return "(" + std::to_string(coord[0]) + ", " + std::to_string(coord[1]) + ")"; }
}
