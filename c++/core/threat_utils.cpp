#include "core/threat_utils.hpp"
#include "core/geometry.hpp"
#include "core/misc.hpp"
#include "core/teams.hpp"
#include "core/state_machine.hpp"
#include "core/combatant.hpp"
#include "actions/movement.hpp"
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
        for(const auto &factory : pa->getActionFactoriesConst())
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

        for(const auto &factory : pa->getBonusActionFactoriesConst())
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

        for(const auto &factory : pa->getHasteActionFactoriesConst())
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

        for(const auto &factory : combatant->getActionFactoriesConst())
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
        for(const auto &factory : combatant->getBonusActionFactoriesConst())
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
        for(const auto &factory : combatant->getHasteActionFactoriesConst())
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
        for(const auto &factory : pa->getActionFactoriesConst())
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

        for(const auto &factory : pa->getBonusActionFactoriesConst())
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

        for(const auto &factory : pa->getHasteActionFactoriesConst())
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
        const Coords &enemyPos = battleMap.getCombatantCoordinates(*enemy);
        DirectThreatFactory *dzFactory = enemy->getDangerZoneAttack();

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
    for(const auto &weakEffect : effectTracker.getAoeEffects())
      {
        if(auto effect = weakEffect.lock())
          {
            effectToCoords.at(effect.get()) = Coords(effect->getAffectedCoords());
          }
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
                                        const std::unordered_map<std::shared_ptr<AoeEffect>, Coords> &effectToCoords, bool disengaged, bool dodged)
  {
    auto rollType = dodged ? RollType::DISADVANTAGE : RollType::STRAIGHT;
    double threatAcc = 0.0;
    auto &battleMap = BattleMap::getInstance();

    auto withPosition = [&](const std::function<void()> &fn) { battleMap.withCombatantPosition(combatant, currCoordsData.getRoot(), fn); };

    withPosition([&]() {
      // Account for AoO
      if(!disengaged)
        {
          auto enemies = battleMap.getAooEligibleCombatants(combatant, increment);
          for(auto *enemy : enemies)
            {
              AttackFactory *aooFactory = enemy->getAoOFactory();
              if(!aooFactory)
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

  std::vector<double>
  accumulateThreatAlongPath(const CoordVector &path, Combatant *combatant,
                            const std::unordered_map<std::shared_ptr<AoeEffect>, Coords> &effectToCoords, bool disengaged, bool dodged)
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

  PathSearchResult calcThreatForPathWithMistyStep(const CoordVector &path, Combatant *combatant,
                                                  const std::unordered_map<std::shared_ptr<AoeEffect>, CoordVector> &effectToCoords)
  {
    auto &battleMap = BattleMap::getInstance();
    auto currCoords = battleMap.getCombatantCoordinates(*combatant);

    // No path case
    if(path.empty())
      {
        return {{-getThreatForStayingAtCoord(currCoords, combatant)}, {}};
      }

    // Build the Misty Step DAG
    CoordVector coords = currCoords.get();
    StateMachine msDAG;

    // Create initial state
    StateId initialState = msDAG.getNextStateId();
    msDAG.addNewState(initialState);

    // Maps to track states and threats
    std::unordered_map<Coord, StateId> coordToStateId;
    std::unordered_map<StateId, Coord> stateIdToCoord;
    std::unordered_map<std::pair<StateId, StateId>, double, StateIdPairHash> transitionThreat;
    std::unordered_map<StateId, std::pair<StateId, std::shared_ptr<Actoid>>> maxThreatPredecessor;

    // Build states and transitions along the path
    Coord currentPos = coords[0];
    StateId previousState = initialState;
    StateId previousMsState = initialState;

    coordToStateId[currentPos] = initialState;
    stateIdToCoord[initialState] = currentPos;

    // Build two branches: pre-MS movement and post-MS movement
    CoordVector preMsPath;
    CoordVector postMsPath;
    for(const auto &increment : path)
      {
        currentPos[0] += increment[0];
        currentPos[1] += increment[1];
        coords.push_back(currentPos);
        preMsPath.push_back(increment);
        postMsPath.push_back(increment);

        // Create states for both regular and post-MS versions
        StateId newState = msDAG.getNextStateId();
        StateId newMsState = msDAG.getNextStateId();

        msDAG.addNewState(newState);
        msDAG.addNewState(newMsState);

        coordToStateId[currentPos] = newState;
        stateIdToCoord[newState] = currentPos;
        stateIdToCoord[newMsState] = currentPos;

        // Create factories with their respective paths
        auto moveFactory = std::make_shared<MovementFactory>(combatant, preMsPath, AbilityType::STANDARD_MOVEMENT);
        auto msMoveFactory = std::make_shared<MovementFactory>(combatant, postMsPath, AbilityType::STANDARD_MOVEMENT);

        // Add movement transitions
        auto moveActions = moveFactory->createAll();
        auto msMoveActions = msMoveFactory->createAll();

        if(!moveActions.empty() && !msMoveActions.empty())
          {
            msDAG.addTransition(moveActions.back(), previousState, newState);
            msDAG.addTransition(msMoveActions.back(), previousMsState, newMsState);

            // Calculate threats for transitions
            double currThreat = getAoeAndAooThreatForIncrement({coords[coords.size() - 2]}, increment, combatant, effectToCoords, false, false);
            transitionThreat[{previousState, newState}] = currThreat;
            transitionThreat[{previousMsState, newMsState}] = currThreat;
          }

        previousState = newState;
        previousMsState = newMsState;
      }

    // Add Misty Step connections
    for(size_t i = 0; i < coords.size() - 1; ++i)
      {
        for(size_t j = i + 1; j < coords.size(); ++j)
          {
            if(std::hypot(coords[i][0] - coords[j][0], coords[i][1] - coords[j][1]) <= static_cast<double>(MistyStepFactory::range))
              {
                auto msFactory = std::make_shared<MistyStepFactory>(combatant, nullptr);
                auto msAction = msFactory->create(&coords[j]); // Pass target coordinate directly

                if(msAction)
                  {
                    StateId originState = coordToStateId[coords[i]];
                    StateId destState = coordToStateId[coords[j]];
                    msDAG.addTransition(msAction, originState, destState);
                  }
              }
          }
      }

    // Find best path using dynamic programming
    auto sortedStates = msDAG.toposort();
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
        for(const auto &[action, targetState] : msDAG.getForwardTransitions(state))
          {
            double threatForTransition = action->getAbilityType() == AbilityType::MISTY_STEP ? 0.0 : transitionThreat[{state, targetState}];
            double totalThreat = (stateThreat[state] > MINUS_INF) ? stateThreat[state] + threatForTransition : 0.0;

            if(totalThreat > stateThreat[targetState])
              {
                stateThreat[targetState] = totalThreat;
                maxThreatPredecessor[targetState] = {state, action};
              }
          }
      }

    // Reconstruct the best path
    CoordVector bestPath;
    StateId currentState = sortedStates.back();
    while(maxThreatPredecessor.contains(currentState))
      {
        auto [prevState, action] = maxThreatPredecessor[currentState];
        bestPath.insert(bestPath.begin(), stateIdToCoord[currentState]);
        currentState = prevState;
      }

    // Calculate final threat
    double threatAcc = stateThreat[sortedStates.back()];
    threatAcc -= getThreatForStayingAtCoord({currentPos}, combatant);

    return {{threatAcc}, bestPath};
  }

} // namespace enc