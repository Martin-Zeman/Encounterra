#pragma once

#include <unordered_map>
#include <vector>
#include <queue>
#include <core/types.hpp>
#include <core/combatant.hpp>
#include <core/teams.hpp>
#include <core/battle_map.hpp>
#include <effects/effect_tracker.hpp>

namespace enc
{
  class RoundManager
  {
  public:
    RoundManager(std::vector<Combatant *> &combatants, int numRounds = 50)
        : _combatants(combatants), _numRounds(numRounds), _actionResolver(combatants), _currCombatant(nullptr)
    {}

    void rollInitiative()
    {
      for(auto &combatant : _combatants)
        {
          combatant->rollInitiative();
        }
    }

    void orderByInitiative()
    {
      std::sort(_combatants.begin(), _combatants.end(),
                [](const Combatant *a, const Combatant *b) { return a->getCurrentInit() > b->getCurrentInit(); });

      std::cout << "--------------INITIATIVE ORDER--------------\n";
      for(const auto &combatant : _combatants)
        {
          std::cout << combatant->toString() << " with " << combatant->getCurrentInit() << "\n";
        }
    }

    void prepCombatants()
    {
      for(auto &combatant : _combatants)
        {
          // Check for moon wildshape
          for(const auto &[type, factory] : combatant->getBonusActionFactories())
            {
              if(type == AbilityType::MOON_WILDSHAPE)
                {
                  combatant->setAvailableWildshapeForms(preallocateWildshapeForms(combatant, AbilityType::MOON_WILDSHAPE, factory));
                  break;
                }
            }
          // Check for regular wildshape
          for(const auto &[type, factory] : combatant->getActionFactories())
            {
              if(type == AbilityType::WILDSHAPE)
                {
                  combatant->setAvailableWildshapeForms(preallocateWildshapeForms(combatant, AbilityType::WILDSHAPE, factory));
                  break;
                }
            }
        }
    }

    bool goesBeforeInInitiative(Combatant *combatant1, Combatant *combatant2) const
    {
      auto it1 = std::find(_combatants.begin(), _combatants.end(), combatant1);
      auto it2 = std::find(_combatants.begin(), _combatants.end(), combatant2);
      return it1 < it2;
    }

    bool isOnlyOneTeamStanding() const { return Teams::getInstance().getSurvivingTeams().size() == 1; }

    void reset(const std::unordered_map<Combatant *, Coord> &combatantInitialPositions)
    {
      EffectTracker::getInstance().reset();
      for(auto &combatant : _combatants)
        {
          combatant->reset();
        }
      BattleMap::getInstance().resetCombatantsToInitialPositions(combatantInitialPositions);
    }

    std::unordered_map<Color, std::unordered_map<Statistics, int>>
    simulateN(int n = 1, std::queue<std::unordered_map<Color, std::unordered_map<Statistics, int>>> *resultQueue = nullptr);

    void simulate();
    void printStatus();
    void printResults();

  private:
    std::vector<Combatant *> &_combatants;
    int _numRounds;
    ActionResolver _actionResolver;
    Combatant *_currCombatant; // For serialization purposes
  };
}
