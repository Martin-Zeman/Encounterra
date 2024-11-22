#include "core/threat_utils.hpp"
#include "core/geometry.hpp"
#include "core/misc.hpp"
#include "core/teams.hpp"
#include "core/state_machine.hpp"
#include "effects/effect_tracker.hpp"
#include "spells/misty_step.hpp"
#include <numeric>
#include <algorithm>
#include <cmath>

namespace enc
{

  double dmgIncrementForToHitFlat(int toHit, const std::vector<Die> &dmgDice, int dmgBonus, int ac, int toHitIncrement, Combatant *target,
                                  DamageType dmgType, int critRange)
  {
    return meanDmg(toHit + toHitIncrement, dmgDice, dmgBonus, ac, target->isImmuneTo(dmgType), target->isResistantTo(dmgType), critRange)
           - meanDmg(toHit, dmgDice, dmgBonus, ac, target->isImmuneTo(dmgType), target->isResistantTo(dmgType), critRange);
  }

  double
  dmgIncrementForDmgFlat(int toHit, const std::vector<Die> &dmgDice, int dmgBonus, int ac, int dmgIncrement, Combatant *target, DamageType dmgType)
  {
    return meanDmg(toHit, dmgDice, dmgBonus + dmgIncrement, ac, target->isImmuneTo(dmgType), target->isResistantTo(dmgType))
           - meanDmg(toHit, dmgDice, dmgBonus, ac, target->isImmuneTo(dmgType), target->isResistantTo(dmgType));
  }

  double dmgDecrementForAcFlat(int toHit, const std::vector<Die> &dmgDice, int dmgBonus, int ac, int acBonus, Combatant *target, DamageType dmgType,
                               int critRange)
  {
    return meanDmg(toHit, dmgDice, dmgBonus, ac, target->isImmuneTo(dmgType), target->isResistantTo(dmgType), critRange)
           - meanDmg(toHit, dmgDice, dmgBonus, ac + acBonus, target->isImmuneTo(dmgType), target->isResistantTo(dmgType), critRange);
  }

  // std::vector<std::shared_ptr<DirectThreatFactory>> getDirectThreatFactories(const std::vector<std::shared_ptr<ActoidFactory>> &factories)
  // {
  //   std::vector<std::shared_ptr<DirectThreatFactory>> threatFactories;
  //   for(const auto &factory : factories)
  //     {
  //       if(auto threatFactory = std::dynamic_pointer_cast<DirectThreatFactory>(factory))
  //         {
  //           threatFactories.push_back(threatFactory);
  //         }
  //     }
  //   return threatFactories;
  // }

  std::pair<double, double> calculateThreatInDelta(Combatant *combatant, int threatRadius, const ThreatModifiers &modifiers, uint32_t factoryFlags)
  {
    auto &battleMap = BattleMap::getInstance();
    auto potentialAttackers = battleMap.getNonSwallowedEnemiesWithinHopDistance(combatant, threatRadius);
    double minThreat = 0.0;
    double maxThreat = 0.0;

    for(auto *pa : potentialAttackers)
      {
        for(const auto &factory : pa->getActionFactories())
          {
            if(auto threatFactory = std::dynamic_pointer_cast<DirectThreatFactory>(factory))
              {
                if((threatFactory->getFlags() & factoryFlags)
                   && !(threatFactory->getFlags() & static_cast<uint32_t>(FactoryFlags::PREVENT_ENDLESS_RECURSION)))
                  {
                    double delta = threatFactory->calculateThreatToTargetDelta(combatant, modifiers);
                    maxThreat = std::max(delta, maxThreat);
                    minThreat = std::min(delta, minThreat);
                  }
              }
          }

        for(const auto &factory : pa->getBonusActionFactories())
          {
            if(auto threatFactory = std::dynamic_pointer_cast<DirectThreatFactory>(factory))
              {
                if((threatFactory->getFlags() & factoryFlags)
                   && !(threatFactory->getFlags() & static_cast<uint32_t>(FactoryFlags::PREVENT_ENDLESS_RECURSION)))
                  {
                    double delta = threatFactory->calculateThreatToTargetDelta(combatant, modifiers);
                    maxThreat = std::max(delta, maxThreat);
                    minThreat = std::min(delta, minThreat);
                  }
              }
          }

        for(const auto &factory : pa->getHasteActionFactories())
          {
            if(auto threatFactory = std::dynamic_pointer_cast<DirectThreatFactory>(factory))
              {
                if((threatFactory->getFlags() & factoryFlags)
                   && !(threatFactory->getFlags() & static_cast<uint32_t>(FactoryFlags::PREVENT_ENDLESS_RECURSION)))
                  {
                    double delta = threatFactory->calculateThreatToTargetDelta(combatant, modifiers);
                    maxThreat = std::max(delta, maxThreat);
                    minThreat = std::min(delta, minThreat);
                  }
              }
          }
      }
    return {minThreat, maxThreat};
  }

  std::pair<double, double> calculateThreatOutDelta(Combatant *combatant, int threatRadius, const ThreatModifiers &modifiers, uint32_t factoryFlags)
  {
    auto &battleMap = BattleMap::getInstance();
    auto potentialTargets = battleMap.getNonSwallowedEnemiesWithinHopDistance(combatant, threatRadius);
    double outThreatMaxDeltaAcc = 0.0;
    double outThreatMinDeltaAcc = 0.0;

    for(auto *pt : potentialTargets)
      {
        double minThreat = 0.0;
        double maxThreat = 0.0;

        for(const auto &factory : combatant->getActionFactories())
          {
            if(auto threatFactory = std::dynamic_pointer_cast<DirectThreatFactory>(factory))
              {
                if((threatFactory->getFlags() & factoryFlags)
                   && !(threatFactory->getFlags() & static_cast<uint32_t>(FactoryFlags::PREVENT_ENDLESS_RECURSION)))
                  {
                    double delta = threatFactory->calculateThreatToTargetDelta(pt, modifiers);
                    maxThreat = std::max(delta, maxThreat);
                    minThreat = std::min(delta, minThreat);
                  }
              }
          }
        outThreatMaxDeltaAcc += maxThreat;
        outThreatMinDeltaAcc += minThreat;

        minThreat = maxThreat = 0.0;
        for(const auto &factory : combatant->getBonusActionFactories())
          {
            if(auto threatFactory = std::dynamic_pointer_cast<DirectThreatFactory>(factory))
              {
                if((threatFactory->getFlags() & factoryFlags)
                   && !(threatFactory->getFlags() & static_cast<uint32_t>(FactoryFlags::PREVENT_ENDLESS_RECURSION)))
                  {
                    double delta = threatFactory->calculateThreatToTargetDelta(pt, modifiers);
                    maxThreat = std::max(delta, maxThreat);
                    minThreat = std::min(delta, minThreat);
                  }
              }
          }
        outThreatMaxDeltaAcc += maxThreat;
        outThreatMinDeltaAcc += minThreat;

        minThreat = maxThreat = 0.0;
        for(const auto &factory : combatant->getHasteActionFactories())
          {
            if(auto threatFactory = std::dynamic_pointer_cast<DirectThreatFactory>(factory))
              {
                if((threatFactory->getFlags() & factoryFlags)
                   && !(threatFactory->getFlags() & static_cast<uint32_t>(FactoryFlags::PREVENT_ENDLESS_RECURSION)))
                  {
                    double delta = threatFactory->calculateThreatToTargetDelta(pt, modifiers);
                    maxThreat = std::max(delta, maxThreat);
                    minThreat = std::min(delta, minThreat);
                  }
              }
          }
        outThreatMaxDeltaAcc += maxThreat;
        outThreatMinDeltaAcc += minThreat;
      }
    return {outThreatMinDeltaAcc, outThreatMaxDeltaAcc};
  }

  double calculateAvgThreatIn(Combatant *combatant, int threatRadius, uint32_t factoryFlags)
  {
    auto &battleMap = BattleMap::getInstance();
    auto potentialAttackers = battleMap.getNonSwallowedEnemiesWithinHopDistance(combatant, threatRadius);
    double incomingThreatAcc = 0.0;
    int counter = 0;

    for(auto *pa : potentialAttackers)
      {
        for(const auto &factory : pa->getActionFactories())
          {
            if(auto threatFactory = std::dynamic_pointer_cast<DirectThreatFactory>(factory))
              {
                if(threatFactory->getFlags() & factoryFlags)
                  {
                    incomingThreatAcc += threatFactory->calculateThreatToTarget(combatant, {});
                    ++counter;
                  }
              }
          }

        for(const auto &factory : pa->getBonusActionFactories())
          {
            if(auto threatFactory = std::dynamic_pointer_cast<DirectThreatFactory>(factory))
              {
                if(threatFactory->getFlags() & factoryFlags)
                  {
                    incomingThreatAcc += threatFactory->calculateThreatToTarget(combatant, {});
                    ++counter;
                  }
              }
          }

        for(const auto &factory : pa->getHasteActionFactories())
          {
            if(auto threatFactory = std::dynamic_pointer_cast<DirectThreatFactory>(factory))
              {
                if(threatFactory->getFlags() & factoryFlags)
                  {
                    incomingThreatAcc += threatFactory->calculateThreatToTarget(combatant, {});
                    ++counter;
                  }
              }
          }
      }

    return counter > 0 ? incomingThreatAcc / counter : 0.0;
  }

  double getSavingThrowSuccessProb(int dc, int stBonus) { return 1.0 - getSavingThrowFailProb(dc, stBonus); }

  double getSavingThrowFailProb(int dc, int stBonus) { return std::max(0.0, std::min(1.0, (dc - 1 - stBonus) / 20.0)); }

  double getDangerZoneThreat(const Coords &coords, Combatant *combatant, int delta)
  {
    auto &battleMap = BattleMap::getInstance();
    Teams &teams = Teams::getInstance();
    auto enemies = teams.getAliveNonSwallowedEnemies(*combatant);
    double threatAcc = 0.0;

    for(auto *enemy : enemies)
      {
        const Coords& enemyPos = battleMap.getCombatantCoordinates(*enemy);
        DirectThreatFactory* dzFactory = enemy->getDangerZoneAttack();

        if(dzFactory && getHopDistanceCoords(enemyPos, coords) + delta <= enemy->getSpeed() + dzFactory->getRange())
          {
            threatAcc += dzFactory->calculateThreatToTarget(combatant, {{"considerDist", false}}) * DZ_CONSTANT;
          }
      }

    return threatAcc;
  }

  double getThreatForStayingAtCoord(const Coords &coords, Combatant *combatant)
  {
    double threatAcc = 0.0;
    auto &battleMap = BattleMap::getInstance();
    auto &effectTracker = EffectTracker::getInstance();

    std::unordered_map<AoeEffect *, Coords> effectToCoords;
    for(const auto &effect : effectTracker.getAoeEffects())
      {
        effectToCoords[effect.get()] = effect->getAffectedCoords();
      }

    // Process AoE effects
    for(const auto &[effect, affectedCoords] : effectToCoords)
      {
        if(getHopDistanceCoords(affectedCoords, coords) == 0)
          {
            double startTurnThreat = effect->threatOnStartOfTurn(combatant, {});
            assert(startTurnThreat >= 0);
            threatAcc += startTurnThreat;

            double endTurnThreat = effect->threatOnEndOfTurn(combatant, {});
            assert(endTurnThreat >= 0);
            threatAcc += endTurnThreat;
          }
      }

    // Add danger zone threat
    double dzThreat = getDangerZoneThreat(coords, combatant);
    assert(dzThreat >= 0);
    threatAcc += dzThreat;

    return threatAcc;
  }

  double getAoeAndAooThreatForIncrement(const Coords &currCoordsData, const Coord &increment, Combatant *combatant,
                                        const std::unordered_map<AoeEffect *, Coords> &effectToCoords, bool disengaged, bool dodged)
  {
    auto rollType = dodged ? RollType::DISADVANTAGE : RollType::STRAIGHT;
    double threatAcc = 0.0;
    auto &battleMap = BattleMap::getInstance();

    auto withPosition = [&](const std::function<void()> &fn) { battleMap.withCombatantPosition(combatant, currCoordsData.get()[0], fn); };

    withPosition([&]() {
      // Account for AoO
      if(!disengaged)
        {
          auto enemies = battleMap.getAooEligibleCombatants(combatant, increment);
          for(auto *enemy : enemies)
            {
              AttackFactory* aooFactory = enemy->getAoOFactory();
              if (!aooFactory)
              {
                continue;
              }
              double threat = aooFactory->calculateThreatToTarget(combatant, Kwargs{{"rollType", rollType}, {"considerDist", false}});
              assert(threat >= 0);
              threatAcc -= threat;
            }
        }

      // Account for AoE
      Coords postIncrementCoords = currCoordsData + increment;

      for(const auto &[effect, affectedCoords] : effectToCoords)
        {
          int preIncrementDist = getHopDistanceCoords(currCoordsData, affectedCoords);
          int postIncrementDist = getHopDistanceCoords(postIncrementCoords, affectedCoords);

          if(preIncrementDist == 1 && postIncrementDist == 0)
            {
              double threat = effect->threatOnEnter(combatant, {});
              assert(threat >= 0);
              threatAcc -= threat;
            }
          else if(preIncrementDist == 0 && postIncrementDist == 0)
            {
              double threat = effect->threatOnMoveWithin(combatant, {});
              assert(threat >= 0);
              threatAcc -= threat;
            }
        }
    });

    return threatAcc;
  }

  std::vector<double> accumulateThreatAlongPath(const std::vector<Coord> &path, Combatant *combatant,
                                                const std::unordered_map<AoeEffect *, Coords> &effectToCoords, bool disengaged, bool dodged)
  {
    double threatAcc = 0.0;
    auto &battleMap = BattleMap::getInstance();
    auto currCoords = battleMap.getCombatantCoordinates(*combatant);

    std::vector<double> threatAlongPath;
    threatAlongPath.push_back(-getThreatForStayingAtCoord({currCoords}, combatant));

    auto currCoordsData = currCoords;
    for(const auto &increment : path)
      {
        double t = getAoeAndAooThreatForIncrement({currCoordsData}, increment, combatant, effectToCoords, disengaged, dodged);
        assert(t <= 0);
        threatAcc += t;

        currCoordsData = currCoordsData + increment;

        threatAlongPath.push_back(threatAcc - getThreatForStayingAtCoord({currCoordsData}, combatant));
      }

    return threatAlongPath;
  }

  // std::pair<std::vector<double>, std::vector<std::string>>
  // calcThreatForPathWithMistyStep(const std::vector<Coord> &path, Combatant *combatant,
  //                                const std::unordered_map<AoeEffect *, std::vector<Coord>> &effectToCoords)
  // {
  //   double threatAcc = 0.0;
  //   std::vector<double> maxThreatPath;
  //   std::vector<std::string> bestPath;
  //   auto &battleMap = BattleMap::getInstance();
  //   auto currCoords = battleMap.getCombatantCoordinates(*combatant);
    
  //   // No path case
  //   if(path.empty())
  //     {
  //       return {{-getThreatForStayingAtCoord(currCoords, combatant)}, {}};
  //     }

  //   // Build the Misty Step DAG
    
  //   std::vector<Coord> coords = currCoords.get();

  //   // Create state machine for path analysis
  //   StateMachine msDAG;
  //   std::string initialStateName = coordToString(currCoords);
  //   msDAG.states.push_back(initialStateName);

  //   std::unordered_map<std::string, std::string> maxThreatBackwardsTransition;
  //   maxThreatBackwardsTransition[initialStateName] = "";
  //   std::unordered_map<std::string, double> transitionToThreat;

  //   // Build states and transitions along the path
  //   Coord currentPos = currCoords.get()[0];
  //   std::string previousState = initialStateName;
  //   std::string previousMsState = initialStateName;

  //   // We build a DAG with two branches where one branch represents moving before using Misty Step and the other after
  //   // The only transitions between the branches represent Misty Step itself which can be taken at different points of the path
  //   for(const auto &increment : path)
  //     {
  //       currentPos[0] += increment[0];
  //       currentPos[1] += increment[1];
  //       coords.push_back(currentPos);

  //       std::string newStateName = coordToString(currentPos);
  //       std::string newMsStateName = "ms_" + newStateName;
  //       msDAG.states.push_back(newStateName);
  //       msDAG.states.push_back(newMsStateName);

  //       // Add regular movement transitions
  //       std::string transitionName = "m_to_" + newStateName;
  //       std::string msTransitionName = "m_to_" + newMsStateName;

  //       msDAG.addTransition(transitionName, previousState, newStateName);
  //       msDAG.addTransition(msTransitionName, previousMsState, newMsStateName);

  //       // Calculate threats for transitions
  //       double currThreat = getAoeAndAooThreatForIncrement({coords[coords.size() - 2]}, increment, combatant, effectToCoords, false, false);
  //       transitionToThreat[transitionName] = currThreat;
  //       transitionToThreat[msTransitionName] = currThreat;

  //       previousState = newStateName;
  //       previousMsState = newMsStateName;
  //     }

  //   // Add Misty Step connections between eligible positions
  //   for(size_t i = 0; i < coords.size() - 1; ++i)
  //     {
  //       for(size_t j = i + 1; j < coords.size(); ++j)
  //         {
  //           if(std::hypot(coords[i][0] - coords[j][0], coords[i][1] - coords[j][1]) <= MistyStepFactory::RANGE)
  //             {
  //               std::string destName = "ms_" + coordToString(coords[j]);
  //               std::string originName = coordToString(coords[i]);
  //               std::string transitionName = "ms_to_" + destName;
  //               msDAG.addTransition(transitionName, originName, destName);
  //             }
  //         }
  //     }

  //   // Perform topological sort and find the longest (best) path
  //   auto sortedStates = msDAG.toposort();
  //   assert(!sortedStates.empty() && sortedStates.back().find("ms_") != std::string::npos);

  //   std::unordered_map<std::string, double> stateThreat;
  //   const double MINUS_INF = -std::numeric_limits<double>::infinity();

  //   // Initialize threats
  //   for(const auto &state : sortedStates)
  //     {
  //       stateThreat[state] = MINUS_INF;
  //     }
  //   stateThreat[sortedStates[0]] = 0.0;

  //   // Calculate maximum threat path
  //   for(const auto &state : sortedStates)
  //     {
  //       for(const auto &transition : msDAG.getForwardTransitions(state))
  //         {
  //           const auto &[transitionName, targetState] = transition;

  //           double threatForTransition = transitionName.starts_with("ms") ? 0.0 : transitionToThreat[transitionName];
  //           double totalThreat = (stateThreat[state] > MINUS_INF) ? stateThreat[state] + threatForTransition : 0.0;

  //           if(totalThreat > stateThreat[targetState])
  //             {
  //               stateThreat[targetState] = totalThreat;
  //               maxThreatBackwardsTransition[targetState] = transitionName + "|" + state;
  //             }
  //         }
  //     }

  //   // Reconstruct the best path
  //   std::string currentState = sortedStates.back();
  //   while(!maxThreatBackwardsTransition[currentState].empty())
  //     {
  //       auto [transitionName, prevState] = [&]() {
  //         auto pos = maxThreatBackwardsTransition[currentState].find('|');
  //         return std::make_pair(maxThreatBackwardsTransition[currentState].substr(0, pos),
  //                               maxThreatBackwardsTransition[currentState].substr(pos + 1));
  //       }();

  //       bestPath.insert(bestPath.begin(), transitionName);
  //       currentState = prevState;
  //     }

  //   // Calculate final threat
  //   threatAcc += stateThreat[sortedStates.back()];
  //   Coord finalCoord = currentPos;
  //   threatAcc -= getThreatForStayingAtCoord({finalCoord}, combatant);

  //   return {{threatAcc}, bestPath};
  // }

  std::pair<std::vector<double>, std::vector<std::string>>
calcThreatForPathWithMistyStep(const std::vector<Coord> &path, Combatant *combatant,
                              const std::unordered_map<AoeEffect *, std::vector<Coord>> &effectToCoords)
{
    double threatAcc = 0.0;
    std::vector<std::string> bestPath;
    auto &battleMap = BattleMap::getInstance();
    auto currCoords = battleMap.getCombatantCoordinates(*combatant);
    
    // No path case
    if(path.empty())
    {
        return {{-getThreatForStayingAtCoord(currCoords, combatant)}, {}};
    }

    // Build the Misty Step DAG
    std::vector<Coord> coords = currCoords.get();
    
    // Create state machine for path analysis
    StateMachine msDAG;
    
    // Convert initial coordinates to state ID and add it
    StateId initialState = msDAG.getNextStateId();
    msDAG.addNewState(initialState);
    
    std::unordered_map<std::string, StateId> coordToStateId;  // Map to track coordinate strings to state IDs
    std::unordered_map<StateId, std::string> stateIdToCoord;  // Reverse mapping for reconstruction
    std::unordered_map<std::string, double> transitionToThreat;
    std::unordered_map<StateId, std::string> maxThreatBackwardsTransition;
    
    // Build states and transitions along the path
    Coord currentPos = coords[0];
    StateId previousState = initialState;
    StateId previousMsState = initialState;

    std::string initialCoordStr = coordToString(currentPos);
    coordToStateId[initialCoordStr] = initialState;
    stateIdToCoord[initialState] = initialCoordStr;
    maxThreatBackwardsTransition[initialState] = "";

    // We build a DAG with two branches where one branch represents moving before using Misty Step and the other after
    for(const auto &increment : path)
    {
        currentPos[0] += increment[0];
        currentPos[1] += increment[1];
        coords.push_back(currentPos);

        std::string newCoordStr = coordToString({currentPos});
        
        // Create new states for both regular and misty step versions
        StateId newState = msDAG.getNextStateId();
        StateId newMsState = msDAG.getNextStateId();
        
        msDAG.addNewState(newState);
        msDAG.addNewState(newMsState);
        
        coordToStateId[newCoordStr] = newState;
        coordToStateId["ms_" + newCoordStr] = newMsState;
        stateIdToCoord[newState] = newCoordStr;
        stateIdToCoord[newMsState] = "ms_" + newCoordStr;

        // Add regular movement transitions
        std::string transitionName = "m_to_" + newCoordStr;
        std::string msTransitionName = "m_to_ms_" + newCoordStr;

        msDAG.addTransition(transitionName, previousState, newState);
        msDAG.addTransition(msTransitionName, previousMsState, newMsState);

        // Calculate threats for transitions
        double currThreat = getAoeAndAooThreatForIncrement({coords[coords.size() - 2]}, increment, combatant, effectToCoords, false, false);
        transitionToThreat[transitionName] = currThreat;
        transitionToThreat[msTransitionName] = currThreat;

        previousState = newState;
        previousMsState = newMsState;
    }

    // Add Misty Step connections between eligible positions
    for(size_t i = 0; i < coords.size() - 1; ++i)
    {
        for(size_t j = i + 1; j < coords.size(); ++j)
        {
            if(std::hypot(coords[i][0] - coords[j][0], coords[i][1] - coords[j][1]) <= static_cast<double>(MistyStepFactory::range))
            {
                std::string originCoord = coordToString({coords[i]});
                std::string destCoord = coordToString({coords[j]});
                std::string transitionName = "ms_to_ms_" + destCoord;
                
                msDAG.addTransition(transitionName, 
                                  coordToStateId[originCoord], 
                                  coordToStateId["ms_" + destCoord]);
            }
        }
    }

    // Perform topological sort and find the longest (best) path
    auto sortedStates = msDAG.toposort();
    assert(!sortedStates.empty());
    assert(stateIdToCoord[sortedStates.back()].find("ms_") != std::string::npos);

    std::unordered_map<StateId, double> stateThreat;
    const double MINUS_INF = -std::numeric_limits<double>::infinity();

    // Initialize threats
    for(const auto &state : sortedStates)
    {
        stateThreat[state] = MINUS_INF;
    }
    stateThreat[sortedStates[0]] = 0.0;

    // Calculate maximum threat path
    for(const auto &state : sortedStates)
    {
        auto transitions = msDAG.getForwardTransitions(state);
        for(const auto &[transitionName, _] : transitions)
        {
            StateId targetState = msDAG.getCurrentState();  // Need to add a method to get destination state
            
            double threatForTransition = transitionName.starts_with("ms") ? 0.0 : transitionToThreat[transitionName];
            double totalThreat = (stateThreat[state] > MINUS_INF) ? stateThreat[state] + threatForTransition : 0.0;

            if(totalThreat > stateThreat[targetState])
            {
                stateThreat[targetState] = totalThreat;
                maxThreatBackwardsTransition[targetState] = transitionName + "|" + std::to_string(state);
            }
        }
    }

    // Reconstruct the best path
    StateId currentState = sortedStates.back();
    while(!maxThreatBackwardsTransition[currentState].empty())
    {
        auto [transitionName, prevStateStr] = [&]() {
            auto pos = maxThreatBackwardsTransition[currentState].find('|');
            return std::make_pair(maxThreatBackwardsTransition[currentState].substr(0, pos),
                                maxThreatBackwardsTransition[currentState].substr(pos + 1));
        }();

        bestPath.insert(bestPath.begin(), transitionName);
        currentState = std::stoi(prevStateStr);
    }

    // Calculate final threat
    threatAcc += stateThreat[sortedStates.back()];
    Coord finalCoord = currentPos;
    threatAcc -= getThreatForStayingAtCoord({finalCoord}, combatant);

    return {{threatAcc}, bestPath};
}

} // namespace enc