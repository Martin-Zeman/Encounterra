#include "core/round_manager.hpp"
#include "actions/action_selection.hpp"

namespace enc
{

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
    std::unordered_map<Combatant *, Coord> combatantInitialPositions;
    for(const auto &combatant : _combatants)
      {
        combatantInitialPositions.emplace(combatant, battleMap.getCombatantCoordinates(*combatant));
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
            effectTracker.startOfTurnTick(combatant);
            effectTracker.startOfTurn(combatant);

            if(!combatant->isAlive())
              {
                continue; // Start of turn effects can kill
              }

            combatant->newTurn();
            auto effects = effectTracker.getAffectingCombatant(combatant);
            _actionResolver.resolveEffects(effects, combatant);

            if(combatant->isAffectedByAny(
                 {Conditions::INCAPACITATED, Conditions::STUNNED, Conditions::PARALYZED, Conditions::PETRIFIED, Conditions::UNCONSCIOUS}))
              {
                std::cout << combatant->toString() << " is affected by a condition which prevents any action. Skipping turn\n";
                effectTracker.endOfTurn(combatant);
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
                auto action = getAction(combatant);
                if(!action)
                  break;

                auto resolution = _actionResolver.resolveAction(action, combatant);
                if(!resolution)
                  break;

                if(isOnlyOneTeamStanding())
                  {
                    done = true;
                    break;
                  }

                if(!combatant->isAlive())
                  {
                    effectTracker.combatantDied(combatant);
                    break;
                  }
              }

            if(combatant->isAlive())
              {
                effectTracker.endOfTurn(combatant);
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
        Combatant *currentForm = combatant->getCurrentForm();
        std::string status = currentForm->isAlive() ? "alive with " + std::to_string(currentForm->getCurrentHp()) + " hp" : "dead";

        std::cout << combatant->toString() << " is " << status << "\n";
      }
  }

  void RoundManager::printResults()
  {
    std::cout << "--------------RESULT--------------\n";
    printStatus();
  }

} // namespace enc
