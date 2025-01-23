#include "core/round_manager.hpp"
#include "actions/action_selection.hpp"
#include "abilities/wildshape_utils.hpp"

namespace enc
{

  void RoundManager::rollInitiative()
  {
    for(auto &combatant : _combatants)
      {
        combatant->rollInitiative();
      }
  }

  void RoundManager::orderByInitiative()
  {
    std::sort(_combatants.begin(), _combatants.end(),
              [](const std::shared_ptr<Combatant> &a, const std::shared_ptr<Combatant> &b) { return a->getCurrentInit() > b->getCurrentInit(); });

    std::cout << "--------------INITIATIVE ORDER--------------\n";
    for(const auto &combatant : _combatants)
      {
        std::cout << combatant->toString() << " with " << combatant->getCurrentInit() << "\n";
      }
  }

  void RoundManager::prepCombatants()
  {
    for(auto &combatant : _combatants)
      {
        // Check for moon & regular wildshape
        for(const auto &factory : combatant->getBonusActionFactoriesConst())
          {
            if(factory->getAbilityType() == AbilityType::MOON_WILDSHAPE || factory->getAbilityType() == AbilityType::WILDSHAPE)
              {
                auto *wildshapeFactory = static_cast<WildshapeFactory *>(factory.get());
                combatant->setAvailableWildshapeForms(preallocateWildshapeForms(combatant, factory->getAbilityType(), *wildshapeFactory));
                break;
              }
          }
      }
  }

  bool RoundManager::goesBeforeInInitiative(const Combatant &combatant1, const Combatant &combatant2) const
  {
    auto it1 = std::find(_combatants.begin(), _combatants.end(), combatant1);
    auto it2 = std::find(_combatants.begin(), _combatants.end(), combatant2);
    return it1 < it2;
  }

  bool RoundManager::isOnlyOneTeamStanding() const { return Teams::getInstance().getSurvivingTeams().size() == 1; }

  void RoundManager::reset(const std::unordered_map<int, Coords> &combatantInitialPositions)
  {
    EffectTracker::getInstance().reset();
    for(auto &combatant : _combatants)
      {
        combatant->reset();
      }
    BattleMap::getInstance().resetCombatantsToInitialPositions(combatantInitialPositions);
  }

  std::unordered_map<Color, std::unordered_map<Statistics, int>>
  RoundManager::simulateN(int n, std::queue<std::unordered_map<Color, std::unordered_map<Statistics, int>>> *resultQueue)
  {
    if(n <= 0)
      {
        std::cout << "Wrong input. n has to be 1 or higher!\n";
        return {};
      }

    std::unordered_map<Color, std::unordered_map<Statistics, int>> teamTally;
    for(Color color : Teams::getInstance().getTeamColors())
      {
        teamTally[color] = std::unordered_map<Statistics, int>();
        for(const auto &stat : getAllStatistics())
          {
            teamTally[color][stat] = 0;
          }
      }

    auto &battleMap = BattleMap::getInstance();
    std::unordered_map<int, Coords> combatantInitialPositions;
    for(const auto &combatant : _combatants)
      {
        combatantInitialPositions.emplace(combatant->_instanceId, battleMap.getCombatantCoordinates(*combatant));
      }

    prepCombatants();

    for(int i = 0; i < n; ++i)
      {
        std::cout << i << ". Iteration\n";
        simulate();

        auto survivingTeams = Teams::getInstance().getSurvivingTeams();
        if(survivingTeams.size() > 1)
          {
            std::cout << "There's more than one surviving team. Battle's not over yet!\n";
          }
        else if(survivingTeams.empty())
          {
            std::cout << "Everyone's dead. No winners!\n";
          }
        else
          {
            std::cout << "Team " << COLOR_NAMES.at(survivingTeams[0]) << " wins\n";
            teamTally[survivingTeams[0]][Statistics::VICTORIES]++;

            auto [deadBlue, deadRed] = Teams::getInstance().getDeathCount();
            if(deadBlue > 0)
              teamTally[Color::BLUE][Statistics::AT_LEAST_ONE_DIED]++;
            if(deadRed > 0)
              teamTally[Color::RED][Statistics::AT_LEAST_ONE_DIED]++;
            if(deadBlue > 1)
              teamTally[Color::BLUE][Statistics::AT_LEAST_TWO_DIED]++;
            if(deadRed > 1)
              teamTally[Color::RED][Statistics::AT_LEAST_TWO_DIED]++;
            if(deadBlue > 2)
              teamTally[Color::BLUE][Statistics::AT_LEAST_THREE_DIED]++;
            if(deadRed > 2)
              teamTally[Color::RED][Statistics::AT_LEAST_THREE_DIED]++;
          }

        reset(combatantInitialPositions);
      }

    if(resultQueue)
      {
        resultQueue->push(teamTally);
      }

    return teamTally;
  }

  void RoundManager::simulate()
  {
    auto &battleMap = BattleMap::getInstance();
    auto &effectTracker = EffectTracker::getInstance();

    rollInitiative();
    orderByInitiative();
    bool done = false;

    std::cout << "--------------START--------------\n";
    for(int r = 0; r < _numRounds; ++r)
      {
        battleMap.setCombatRound(r);
        std::cout << "Round " << (r + 1) << ":\n";

        if(done)
          {
            std::cout << "The fight is over\n";
            break;
          }

        for(auto &combatant : _combatants)
          {
            if(done)
              {
                break;
              }
            if(!combatant->isAlive())
              {
                continue;
              }

            std::cout << "It's " << combatant->toString() << "'s turn\n";
            _currCombatant = combatant;
            std::cout << battleMap.toString() << "\n";

            combatant->rollForRecharge();
            effectTracker.startOfTurnTick(*combatant);
            effectTracker.startOfTurn(*combatant);

            if(!combatant->isAlive())
              {
                continue; // Start of turn effects can kill
              }

            combatant->newTurn();
            auto effects = effectTracker.getAffectingCombatant(*combatant);
            resolveEffects(effects, *combatant);

            if(combatant->isAffectedByAny(
                 {Conditions::INCAPACITATED, Conditions::STUNNED, Conditions::PARALYZED, Conditions::PETRIFIED, Conditions::UNCONSCIOUS}))
              {
                std::cout << combatant->toString() << " is affected by a condition which prevents any action. Skipping turn\n";
                effectTracker.endOfTurn(*combatant);
                combatant->onEndOfTurn();
                continue;
              }

            if(isOnlyOneTeamStanding())
              {
                done = true;
                break;
              }

            while(true)
              {
                auto action = getAction(*combatant);
                if(!action)
                  {
                    break;
                  }

                ActionResult resolution = resolveAction(action, *combatant);
                if(resolution == ActionResult::UNFEASIBLE)
                  {
                    break;
                  }

                if(isOnlyOneTeamStanding())
                  {
                    done = true;
                    break;
                  }

                if(!combatant->isAlive())
                  {
                    effectTracker.combatantDied(*combatant);
                    break;
                  }
              }

            if(combatant->isAlive())
              {
                effectTracker.endOfTurn(*combatant);
                combatant->onEndOfTurn();
              }
          }

        std::cout << "----------------------------------\n";
        printStatus();
      }
  }

  void RoundManager::printStatus()
  {
    for(const auto &combatant : _combatants)
      {
        Combatant &currentForm = combatant->getCurrentForm();
        std::string status = currentForm.isAlive() ? "alive with " + std::to_string(currentForm.getCurrentHp()) + " hp" : "dead";

        std::cout << combatant->toString() << " is " << status << "\n";
      }
  }

  void RoundManager::printResults()
  {
    std::cout << "--------------RESULT--------------\n";
    printStatus();
  }

} // namespace enc
