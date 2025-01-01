#pragma once

#include <unordered_map>
#include <vector>
#include <queue>
#include <core/types.hpp>
#include <core/combatant.hpp>
#include <core/teams.hpp>
#include <core/battle_map.hpp>
#include <core/action_resolver.hpp>
#include <effects/effect_tracker.hpp>

namespace enc
{
  class RoundManager
  {
  public:
    RoundManager(std::vector<Combatant *> &combatants, int numRounds = 50) : _combatants(combatants), _numRounds(numRounds), _currCombatant(nullptr)
    {}

    void rollInitiative();

    void orderByInitiative();

    void prepCombatants();

    bool goesBeforeInInitiative(Combatant *combatant1, Combatant *combatant2) const;

    bool isOnlyOneTeamStanding() const;

    void reset(const std::unordered_map<int, Coords> &combatantInitialPositions);

    std::unordered_map<Color, std::unordered_map<Statistics, int>>
    simulateN(int n = 1, std::queue<std::unordered_map<Color, std::unordered_map<Statistics, int>>> *resultQueue = nullptr);

    void simulate();
    void printStatus();
    void printResults();

  private:
    std::vector<Combatant *> &_combatants;
    int _numRounds;
    Combatant *_currCombatant; // For serialization purposes
  };
} // namespace enc
