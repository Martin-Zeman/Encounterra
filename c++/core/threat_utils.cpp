#include "combat/threat_utils.hpp"
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

  std::pair<double, double>
  calculateThreatInDelta(Combatant *combatant, int threatRadius, const std::unordered_map<std::string, double> &modifiers, uint32_t factoryFlags)
  {
    auto &battleMap = BattleMap::get();
    auto potentialAttackers = battleMap.getNonSwallowedEnemiesWithinHopDistance(combatant, threatRadius);
    double minThreat = 0.0;
    double maxThreat = 0.0;

    for(auto *pa : potentialAttackers)
      {
        for(const auto &[_, factory] : pa->getActionFactories())
          {
            if((factory->getFlags() & factoryFlags) && !(factory->getFlags() & FactoryFlags::PREVENT_ENDLESS_RECURSION))
              {
                double delta = factory->calculateThreatToTargetDelta(combatant, modifiers);
                maxThreat = std::max(delta, maxThreat);
                minThreat = std::min(delta, minThreat);
              }
          }

        for(const auto &[_, factory] : pa->getBonusActionFactories())
          {
            if((factory->getFlags() & factoryFlags) && !(factory->getFlags() & FactoryFlags::PREVENT_ENDLESS_RECURSION))
              {
                double delta = factory->calculateThreatToTargetDelta(combatant, modifiers);
                maxThreat = std::max(delta, maxThreat);
                minThreat = std::min(delta, minThreat);
              }
          }

        for(const auto &[_, factory] : pa->getHasteActionFactories())
          {
            if((factory->getFlags() & factoryFlags) && !(factory->getFlags() & FactoryFlags::PREVENT_ENDLESS_RECURSION))
              {
                double delta = factory->calculateThreatToTargetDelta(combatant, modifiers);
                maxThreat = std::max(delta, maxThreat);
                minThreat = std::min(delta, minThreat);
              }
          }
      }
    return {minThreat, maxThreat};
  }

  std::pair<double, double>
  calculateThreatOutDelta(Combatant *combatant, int threatRadius, const std::unordered_map<std::string, double> &modifiers, uint32_t factoryFlags)
  {
    auto &battleMap = BattleMap::get();
    auto potentialTargets = battleMap.getNonSwallowedEnemiesWithinHopDistance(combatant, threatRadius);
    double outThreatMaxDeltaAcc = 0.0;
    double outThreatMinDeltaAcc = 0.0;

    for(auto *pt : potentialTargets)
      {
        double minThreat = 0.0;
        double maxThreat = 0.0;

        // Check action factories
        for(const auto &[_, factory] : combatant->getActionFactories())
          {
            if((factory->getFlags() & factoryFlags) && !(factory->getFlags() & FactoryFlags::PREVENT_ENDLESS_RECURSION))
              {
                double delta = factory->calculateThreatToTargetDelta(pt, modifiers);
                maxThreat = std::max(delta, maxThreat);
                minThreat = std::min(delta, minThreat);
              }
          }
        outThreatMaxDeltaAcc += maxThreat;
        outThreatMinDeltaAcc += minThreat;

        // Check bonus action factories
        minThreat = maxThreat = 0.0;
        for(const auto &[_, factory] : combatant->getBonusActionFactories())
          {
            if((factory->getFlags() & factoryFlags) && !(factory->getFlags() & FactoryFlags::PREVENT_ENDLESS_RECURSION))
              {
                double delta = factory->calculateThreatToTargetDelta(pt, modifiers);
                maxThreat = std::max(delta, maxThreat);
                minThreat = std::min(delta, minThreat);
              }
          }
        outThreatMaxDeltaAcc += maxThreat;
        outThreatMinDeltaAcc += minThreat;

        // Check haste action factories
        minThreat = maxThreat = 0.0;
        for(const auto &[_, factory] : combatant->getHasteActionFactories())
          {
            if((factory->getFlags() & factoryFlags) && !(factory->getFlags() & FactoryFlags::PREVENT_ENDLESS_RECURSION))
              {
                double delta = factory->calculateThreatToTargetDelta(pt, modifiers);
                maxThreat = std::max(delta, maxThreat);
                minThreat = std::min(delta, minThreat);
              }
          }
        outThreatMaxDeltaAcc += maxThreat;
        outThreatMinDeltaAcc += minThreat;
      }
    return {outThreatMinDeltaAcc, outThreatMaxDeltaAcc};
  }

  double calculateAvgThreatIn(Combatant *combatant, int threatRadius, uint32_t factoryFlags)
  {
    auto &battleMap = BattleMap::get();
    auto potentialAttackers = battleMap.getNonSwallowedEnemiesWithinHopDistance(combatant, threatRadius);
    double incomingThreatAcc = 0.0;
    int counter = 0;

    for(auto *pa : potentialAttackers)
      {
        for(const auto &[_, factory] : pa->getActionFactories())
          {
            if(factory->getFlags() & factoryFlags)
              {
                incomingThreatAcc += factory->calculateThreatToTarget(combatant);
                ++counter;
              }
          }

        for(const auto &[_, factory] : pa->getBonusActionFactories())
          {
            if(factory->getFlags() & factoryFlags)
              {
                incomingThreatAcc += factory->calculateThreatToTarget(combatant);
                ++counter;
              }
          }

        for(const auto &[_, factory] : pa->getHasteActionFactories())
          {
            if(factory->getFlags() & factoryFlags)
              {
                incomingThreatAcc += factory->calculateThreatToTarget(combatant);
                ++counter;
              }
          }
      }

    return counter > 0 ? incomingThreatAcc / counter : 0.0;
  }

  double getSavingThrowSuccessProb(int dc, int stBonus) { return 1.0 - getSavingThrowFailProb(dc, stBonus); }

  double getSavingThrowFailProb(int dc, int stBonus) { return std::max(0.0, std::min(1.0, (dc - 1 - stBonus) / 20.0)); }

  double getDangerZoneThreat(const std::vector<Coord> &coords, Combatant *combatant, int delta)
  {
    auto &battleMap = BattleMap::get();
    auto enemies = battleMap.getNonSwallowedEnemies(combatant);
    double threatAcc = 0.0;

    for(auto *enemy : enemies)
      {
        auto enemyPos = battleMap.getCombatantPosition(enemy);
        auto &[dzAction, dzFactory] = enemy->getDangerZoneAttack();

        if(battleMap.getHopDistance(enemyPos, coords) + delta <= enemy->getSpeed() + dzFactory->getRange())
          {
            threatAcc += dzFactory->calculateThreatToTarget(combatant, false) * DZ_CONSTANT;
          }
      }

    return threatAcc;
  }

  double getThreatForStayingAtCoord(const std::vector<Coord> &coords, Combatant *combatant)
  {
    double threatAcc = 0.0;
    auto &battleMap = BattleMap::get();
    auto &effectTracker = battleMap.getEffectTracker();

    std::unordered_map<Effect *, std::vector<Coord>> effectToCoords;
    for(const auto &effect : effectTracker.getAoeEffects())
      {
        effectToCoords[effect.get()] = effect->getAffectedCoords();
      }

    // Process AoE effects
    for(const auto &[effect, affectedCoords] : effectToCoords)
      {
        if(battleMap.getHopDistance(affectedCoords, coords) == 0)
          {
            double startTurnThreat = effect->threatOnStartOfTurn(combatant);
            assert(startTurnThreat >= 0);
            threatAcc += startTurnThreat;

            double endTurnThreat = effect->threatOnEndOfTurn(combatant);
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

  double getAoeAndAooThreatForIncrement(const std::vector<Coord> &currCoordsData, const std::vector<int> &increment, Combatant *combatant,
                                        const std::unordered_map<Effect *, std::vector<Coord>> &effectToCoords, bool disengaged, bool dodged)
  {
    auto rollType = dodged ? RollType::DISADVANTAGE : RollType::STRAIGHT;
    double threatAcc = 0.0;
    auto &battleMap = BattleMap::get();

    auto withPosition = [&](const std::function<void()> &fn) { battleMap.withCombatantPosition(combatant, currCoordsData[0], fn); };

    withPosition([&]() {
      // Account for AoO
      if(!disengaged)
        {
          auto enemies = battleMap.getAooEligibleCombatants(combatant, increment);
          for(auto *enemy : enemies)
            {
              auto &[_, aooFactory] = enemy->getAooFactory();
              double threat = aooFactory->calculateThreatToTarget(combatant, rollType, /*considerDist=*/false);
              assert(threat >= 0);
              threatAcc -= threat;
            }
        }

      // Account for AoE
      std::vector<Coord> postIncrementCoords = currCoordsData;
      for(auto &coord : postIncrementCoords)
        {
          coord[0] += increment[0];
          coord[1] += increment[1];
        }

      for(const auto &[effect, affectedCoords] : effectToCoords)
        {
          int preIncrementDist = battleMap.getHopDistance(currCoordsData, affectedCoords);
          int postIncrementDist = battleMap.getHopDistance(postIncrementCoords, affectedCoords);

          if(preIncrementDist == 1 && postIncrementDist == 0)
            {
              double threat = effect->threatOnEnter(combatant);
              assert(threat >= 0);
              threatAcc -= threat;
            }
          else if(preIncrementDist == 0 && postIncrementDist == 0)
            {
              double threat = effect->threatOnMoveWithin(combatant);
              assert(threat >= 0);
              threatAcc -= threat;
            }
        }
    });

    return threatAcc;
  }

  std::vector<double> accumulateThreatAlongPath(const std::vector<std::vector<int>> &path, Combatant *combatant,
                                                const std::unordered_map<Effect *, std::vector<Coord>> &effectToCoords, bool disengaged, bool dodged)
  {
    double threatAcc = 0.0;
    auto &battleMap = BattleMap::get();
    auto currCoords = battleMap.getCombatantPosition(combatant);

    std::vector<double> threatAlongPath;
    threatAlongPath.push_back(-getThreatForStayingAtCoord({currCoords}, combatant));

    auto currCoordsData = currCoords;
    for(const auto &increment : path)
      {
        double t = getAoeAndAooThreatForIncrement({currCoordsData}, increment, combatant, effectToCoords, disengaged, dodged);
        assert(t <= 0);
        threatAcc += t;

        currCoordsData[0] += increment[0];
        currCoordsData[1] += increment[1];

        threatAlongPath.push_back(threatAcc - getThreatForStayingAtCoord({currCoordsData}, combatant));
      }

    return threatAlongPath;
  }

  std::pair<std::vector<double>, std::vector<std::string>>
  calcThreatForPathWithMistyStep(const std::vector<std::vector<int>> &path, Combatant *combatant,
                                 const std::unordered_map<Effect *, std::vector<Coord>> &effectToCoords)
  {
    double threatAcc = 0.0;
    std::vector<double> maxThreatPath;
    std::vector<std::string> bestPath;
    auto &battleMap = BattleMap::get();

    // No path case
    if(path.empty())
      {
        return {{-getThreatForStayingAtCoord({battleMap.getCombatantPosition(combatant)}, combatant)}, {}};
      }

    // Build the Misty Step DAG
    auto currCoords = battleMap.getCombatantPosition(combatant);
    std::vector<Coord> coords = {currCoords};

    // Create state machine for path analysis
    StateMachineTemplate msDAG;
    std::string initialStateName = coordToString(currCoords);
    msDAG.states.push_back(initialStateName);

    std::unordered_map<std::string, std::string> maxThreatBackwardsTransition;
    maxThreatBackwardsTransition[initialStateName] = "";
    std::unordered_map<std::string, double> transitionToThreat;

    // Build states and transitions along the path
    Coord currentPos = currCoords;
    std::string previousState = initialStateName;
    std::string previousMsState = initialStateName;

    for(const auto &increment : path)
      {
        currentPos[0] += increment[0];
        currentPos[1] += increment[1];
        coords.push_back(currentPos);

        std::string newStateName = coordToString(currentPos);
        std::string newMsStateName = "ms_" + newStateName;
        msDAG.states.push_back(newStateName);
        msDAG.states.push_back(newMsStateName);

        // Add regular movement transitions
        std::string transitionName = "m_to_" + newStateName;
        std::string msTransitionName = "m_to_" + newMsStateName;

        msDAG.addTransition(transitionName, previousState, newStateName);
        msDAG.addTransition(msTransitionName, previousMsState, newMsStateName);

        // Calculate threats for transitions
        double currThreat = getAoeAndAooThreatForIncrement({coords[coords.size() - 2]}, increment, combatant, effectToCoords, false, false);
        transitionToThreat[transitionName] = currThreat;
        transitionToThreat[msTransitionName] = currThreat;

        previousState = newStateName;
        previousMsState = newMsStateName;
      }

    // Add Misty Step connections between eligible positions
    for(size_t i = 0; i < coords.size() - 1; ++i)
      {
        for(size_t j = i + 1; j < coords.size(); ++j)
          {
            if(std::hypot(coords[i][0] - coords[j][0], coords[i][1] - coords[j][1]) <= MistyStepFactory::RANGE)
              {
                std::string destName = "ms_" + coordToString(coords[j]);
                std::string originName = coordToString(coords[i]);
                std::string transitionName = "ms_to_" + destName;
                msDAG.addTransition(transitionName, originName, destName);
              }
          }
      }

    // Perform topological sort and find the longest (best) path
    auto sortedStates = msDAG.toposort();
    assert(!sortedStates.empty() && sortedStates.back().find("ms_") != std::string::npos);

    std::unordered_map<std::string, double> stateThreat;
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
        for(const auto &transition : msDAG.getForwardTransitions(state))
          {
            const auto &[transitionName, targetState] = transition;

            double threatForTransition = transitionName.starts_with("ms") ? 0.0 : transitionToThreat[transitionName];
            double totalThreat = (stateThreat[state] > MINUS_INF) ? stateThreat[state] + threatForTransition : 0.0;

            if(totalThreat > stateThreat[targetState])
              {
                stateThreat[targetState] = totalThreat;
                maxThreatBackwardsTransition[targetState] = transitionName + "|" + state;
              }
          }
      }

    // Reconstruct the best path
    std::string currentState = sortedStates.back();
    while(!maxThreatBackwardsTransition[currentState].empty())
      {
        auto [transitionName, prevState] = [&]() {
          auto pos = maxThreatBackwardsTransition[currentState].find('|');
          return std::make_pair(maxThreatBackwardsTransition[currentState].substr(0, pos),
                                maxThreatBackwardsTransition[currentState].substr(pos + 1));
        }();

        bestPath.insert(bestPath.begin(), transitionName);
        currentState = prevState;
      }

    // Calculate final threat
    threatAcc += stateThreat[sortedStates.back()];
    Coord finalCoord = currentPos;
    threatAcc -= getThreatForStayingAtCoord({finalCoord}, combatant);

    return {{threatAcc}, bestPath};
  }

} // namespace enc