#include "core/misc.hpp"

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

  RollType reconcileRollTypes(RollType types)
  {
    uint8_t typeBits = static_cast<uint8_t>(types);

    // If both ADVANTAGE and DISADVANTAGE are present, or if it's STRAIGHT, return STRAIGHT
    if((typeBits & (static_cast<uint8_t>(RollType::ADVANTAGE) | static_cast<uint8_t>(RollType::DISADVANTAGE)))
         == (static_cast<uint8_t>(RollType::ADVANTAGE) | static_cast<uint8_t>(RollType::DISADVANTAGE))
       || typeBits == static_cast<uint8_t>(RollType::STRAIGHT))
      {
        return RollType::STRAIGHT;
      }

    // If only ADVANTAGE is present
    if(typeBits & static_cast<uint8_t>(RollType::ADVANTAGE))
      {
        return RollType::ADVANTAGE;
      }

    // If only DISADVANTAGE is present
    if(typeBits & static_cast<uint8_t>(RollType::DISADVANTAGE))
      {
        return RollType::DISADVANTAGE;
      }

    // Default case (should not happen with valid input)
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

int findPercentileValue(const std::vector<int>& outcomes, int percentile) {
    if (percentile < 0 || percentile > 100) {
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

double percentOfCurrHp(double currHp, double dmg) {
    return dmg / (currHp * 0.01);
}
}
