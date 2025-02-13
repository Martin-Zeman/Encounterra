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

  double dmgIncrementForToHitFlat(int toHit, const std::vector<Die> &dmgDice, int dmgBonus, int ac, int toHitIncrement, const Combatant &target,
                                  DamageType dmgType, int critRange)
  {
    return meanDmg(toHit + toHitIncrement, dmgDice, dmgBonus, ac, target.isImmuneTo(dmgType), target.isResistantTo(dmgType), critRange)
           - meanDmg(toHit, dmgDice, dmgBonus, ac, target.isImmuneTo(dmgType), target.isResistantTo(dmgType), critRange);
  }

  double dmgIncrementForDmgFlat(int toHit, const std::vector<Die> &dmgDice, int dmgBonus, int ac, int dmgIncrement, const Combatant &target,
                                DamageType dmgType)
  {
    return meanDmg(toHit, dmgDice, dmgBonus + dmgIncrement, ac, target.isImmuneTo(dmgType), target.isResistantTo(dmgType))
           - meanDmg(toHit, dmgDice, dmgBonus, ac, target.isImmuneTo(dmgType), target.isResistantTo(dmgType));
  }

  double dmgDecrementForAcFlat(int toHit, const std::vector<Die> &dmgDice, int dmgBonus, int ac, int acBonus, const Combatant &target,
                               DamageType dmgType, int critRange)
  {
    return meanDmg(toHit, dmgDice, dmgBonus, ac, target.isImmuneTo(dmgType), target.isResistantTo(dmgType), critRange)
           - meanDmg(toHit, dmgDice, dmgBonus, ac + acBonus, target.isImmuneTo(dmgType), target.isResistantTo(dmgType), critRange);
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

  std::pair<double, double>
  calculateThreatInDelta(const Combatant &combatant, int threatRadius, const ThreatModifiers &modifiers, uint32_t factoryFlags)
  {
    auto &battleMap = BattleMap::getInstance();
    auto potentialAttackers = battleMap.getNonSwallowedEnemiesWithinHopDistance(combatant, threatRadius);
    double minThreat = 0.0;
    double maxThreat = 0.0;

    for(Combatant *potentialAttacker : potentialAttackers)
      {
        for(ActoidFactory *factory : potentialAttacker->getActionFactoriesConst())
          {
            if(auto threatFactory = dynamic_cast<DirectThreatFactory *>(factory))
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

        for(const auto &factory : potentialAttacker->getBonusActionFactoriesConst())
          {
            if(auto threatFactory = dynamic_cast<DirectThreatFactory *>(factory))
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

        for(const auto &factory : potentialAttacker->getHasteActionFactoriesConst())
          {
            if(auto threatFactory = dynamic_cast<DirectThreatFactory *>(factory))
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

  std::pair<double, double>
  calculateThreatOutDelta(const Combatant &combatant, int threatRadius, const ThreatModifiers &modifiers, uint32_t factoryFlags)
  {
    auto &battleMap = BattleMap::getInstance();
    auto potentialTargets = battleMap.getNonSwallowedEnemiesWithinHopDistance(combatant, threatRadius);
    double outThreatMaxDeltaAcc = 0.0;
    double outThreatMinDeltaAcc = 0.0;

    for(Combatant *potentialTarget : potentialTargets)
      {
        double minThreat = 0.0;
        double maxThreat = 0.0;

        for(const auto &factory : combatant.getActionFactoriesConst())
          {
            if(auto threatFactory = dynamic_cast<DirectThreatFactory *>(factory))
              {
                if((threatFactory->getFlags() & factoryFlags)
                   && !(threatFactory->getFlags() & static_cast<uint32_t>(FactoryFlags::PREVENT_ENDLESS_RECURSION)))
                  {
                    double delta = threatFactory->calculateThreatToTargetDelta(*potentialTarget, modifiers);
                    maxThreat = std::max(delta, maxThreat);
                    minThreat = std::min(delta, minThreat);
                  }
              }
          }
        outThreatMaxDeltaAcc += maxThreat;
        outThreatMinDeltaAcc += minThreat;

        minThreat = maxThreat = 0.0;
        for(const auto &factory : combatant.getBonusActionFactoriesConst())
          {
            if(auto threatFactory = dynamic_cast<DirectThreatFactory *>(factory))
              {
                if((threatFactory->getFlags() & factoryFlags)
                   && !(threatFactory->getFlags() & static_cast<uint32_t>(FactoryFlags::PREVENT_ENDLESS_RECURSION)))
                  {
                    double delta = threatFactory->calculateThreatToTargetDelta(*potentialTarget, modifiers);
                    maxThreat = std::max(delta, maxThreat);
                    minThreat = std::min(delta, minThreat);
                  }
              }
          }
        outThreatMaxDeltaAcc += maxThreat;
        outThreatMinDeltaAcc += minThreat;

        minThreat = maxThreat = 0.0;
        for(const auto &factory : combatant.getHasteActionFactoriesConst())
          {
            if(auto threatFactory = dynamic_cast<DirectThreatFactory *>(factory))
              {
                if((threatFactory->getFlags() & factoryFlags)
                   && !(threatFactory->getFlags() & static_cast<uint32_t>(FactoryFlags::PREVENT_ENDLESS_RECURSION)))
                  {
                    double delta = threatFactory->calculateThreatToTargetDelta(*potentialTarget, modifiers);
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

  double calculateAvgThreatIn(const Combatant &combatant, int threatRadius, uint32_t factoryFlags)
  {
    auto &battleMap = BattleMap::getInstance();
    auto potentialAttackers = battleMap.getNonSwallowedEnemiesWithinHopDistance(combatant, threatRadius);
    double incomingThreatAcc = 0.0;
    int counter = 0;

    for(Combatant *potentialAttacker : potentialAttackers)
      {
        for(const auto &factory : potentialAttacker->getActionFactoriesConst())
          {
            if(auto threatFactory = dynamic_cast<DirectThreatFactory *>(factory))
              {
                if(threatFactory->getFlags() & factoryFlags)
                  {
                    incomingThreatAcc += threatFactory->calculateThreatToTarget(combatant, {});
                    ++counter;
                  }
              }
          }

        for(const auto &factory : potentialAttacker->getBonusActionFactoriesConst())
          {
            if(auto threatFactory = dynamic_cast<DirectThreatFactory *>(factory))
              {
                if(threatFactory->getFlags() & factoryFlags)
                  {
                    incomingThreatAcc += threatFactory->calculateThreatToTarget(combatant, {});
                    ++counter;
                  }
              }
          }

        for(const auto &factory : potentialAttacker->getHasteActionFactoriesConst())
          {
            if(auto threatFactory = dynamic_cast<DirectThreatFactory *>(factory))
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

  double getDangerZoneThreat(const Coords &coords, const Combatant &combatant, int delta)
  {
    auto &battleMap = BattleMap::getInstance();
    Teams &teams = Teams::getInstance();
    auto enemies = teams.getAliveNonSwallowedEnemies(combatant);
    double threatAcc = 0.0;

    for(Combatant *enemy : enemies)
      {
        const Coords &enemyPos = battleMap.getCombatantCoordinates(*enemy);
        DirectThreatFactory *dzFactory = enemy->getDangerZoneAttack();

        auto speed = enemy->getSpeed();
        auto range = dzFactory ? dzFactory->getRange() : 0;
        auto distance = getHopDistanceCoords(enemyPos, coords) + delta;

        if(dzFactory && getHopDistanceCoords(enemyPos, coords) + delta <= enemy->getSpeed() + dzFactory->getRange())
          {
            threatAcc += dzFactory->calculateThreatToTarget(combatant, {{"considerDist", false}}) * DZ_CONSTANT;
          }
      }
    return threatAcc;
  }

  double getThreatForStayingAtCoord(const Coords &coords, const Combatant &combatant)
  {
    double threatAcc = 0.0;
    auto &battleMap = BattleMap::getInstance();
    auto &effectTracker = EffectTracker::getInstance();

    std::unordered_map<AoeEffect *, Coords> effectToCoords;
    for(AoeEffect *effect : effectTracker.getAoeEffects())
      {
        effectToCoords.emplace(effect, effect->getAffectedCoords());
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

  double
  getAoeAndAooThreatForIncrement(const Coords &currCoordsData, const Coord &increment, const Combatant &combatant,
                                 const std::unordered_map<AoeEffect*, CoordVector> &effectToCoords, bool disengaged, bool dodged)
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
          for(Combatant *enemy : enemies)
            {
              DirectThreatFactory *aooFactory = enemy->getAoOFactory();
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

  std::vector<double> accumulateThreatAlongPath(const CoordVector &path, Combatant &combatant,
                                                const std::unordered_map<AoeEffect *, CoordVector> &effectToCoords, bool disengaged, bool dodged)
  {
    double threatAcc = 0.0;
    auto &battleMap = BattleMap::getInstance();
    auto currCoords = battleMap.getCombatantCoordinates(combatant);

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

  PathSearchResult
  calcThreatForPathWithMistyStep(const CoordVector &path, Combatant &combatant, const std::unordered_map<AoeEffect *, CoordVector> &effectToCoords)
  {
    auto &battleMap = BattleMap::getInstance();
    auto currCoords = battleMap.getCombatantCoordinates(combatant);

    // Handle empty path case
    if(path.empty())
      {
        return {{-getThreatForStayingAtCoord(currCoords, combatant)}, {}};
      }

    StateMachine msDAG;

    // Maps to track states and threats
    std::unordered_map<StateId, Coord> stateIdToCoord;
    std::unordered_map<std::pair<StateId, StateId>, double, PairHash> transitionThreat;
    std::unordered_map<StateId, std::pair<StateId, Actoid *>> maxThreatPredecessor;

    // Track path waypoints
    CoordVector waypoints;
    Coord currentPos = currCoords.get()[0];
    waypoints.push_back(currentPos);

    // Build states and transitions along the path
    StateId previousState = 0;
    StateId previousMsState = 0;

    stateIdToCoord[0] = currentPos;

    // Create movement factories once for the entire path
    MovementFactory moveFactory(&combatant, path, AbilityType::STANDARD_MOVEMENT);
    MovementFactory postMsMoveFactory(&combatant, path, AbilityType::STANDARD_MOVEMENT);

    for(const auto &increment : path)
      {
        double currThreat = getAoeAndAooThreatForIncrement(currCoords, increment, combatant, effectToCoords, false, false);
        currCoords += increment;
        currentPos[0] += increment[0];
        currentPos[1] += increment[1];
        waypoints.push_back(currentPos);

        // Create states for both regular and post-MS versions
        StateId newState = msDAG.getNextStateId();   // 2, 4, 6, ...
        StateId newPostMsState = msDAG.getNextStateId(); // 3, 5, 7, ...

        msDAG.addNewState(newState);
        msDAG.addNewState(newPostMsState);

        stateIdToCoord[newState] = currentPos;
        stateIdToCoord[newPostMsState] = currentPos;

        // Create individual movement actions
        Actoid *moveAction = moveFactory.create(nullptr);
        Actoid *msMoveAction = postMsMoveFactory.create(nullptr);

        if(moveAction && msMoveAction)
          {
            msDAG.addTransition(moveAction, previousState, newState);
            msDAG.addTransition(msMoveAction, previousMsState, newPostMsState);

            transitionThreat[{previousState, newState}] = currThreat;
            transitionThreat[{previousMsState, newPostMsState}] = currThreat;
          }

        previousState = newState;
        previousMsState = newPostMsState;
      }

    // Add Misty Step connections
    MistyStepFactory msFactory(&combatant, nullptr);
    for(size_t i = 0; i < waypoints.size() - 1; ++i)
      {
        for(size_t j = i + 1; j < waypoints.size(); ++j)
          {
            if(std::hypot(waypoints[j][0] - waypoints[i][0], waypoints[j][1] - waypoints[i][1]) <= static_cast<double>(MistyStepFactory::range))
              {
                auto msAction = msFactory.create(&waypoints[j]);

                if(msAction)
                  {
                    // For i=0, use state 0 (root), otherwise use pre-MS state (2i)
                    StateId originState = (i == 0) ? 0 : (2 * i);
                    // For j=0, use state 0 (root), otherwise use post-MS state (2j + 1)
                    StateId destMsState = (j == 0) ? 0 : (2 * j + 1);
                    msDAG.addTransition(msAction, originState, destMsState);
                  }
              }
          }
      }

    // Find best path using dynamic programming
    auto sortedStates = msDAG.toposort();
    std::unordered_map<StateId, double> stateToThreat;
    const double MINUS_INF = -std::numeric_limits<double>::infinity();

    // Initialize threats
    for(const auto &state : sortedStates)
      {
        stateToThreat[state] = MINUS_INF;
      }
    stateToThreat[0] = 0.0;

    // Calculate maximum threat path
    for(const auto &state : sortedStates)
      {
        for(const auto &[action, targetState] : msDAG.getForwardTransitions(state))
          {
            double threatForTransition = (action->getAbilityType() == AbilityType::MISTY_STEP) ? 0.0 : transitionThreat[{state, targetState}];

            double totalThreat = (stateToThreat[state] > MINUS_INF) ? stateToThreat[state] + threatForTransition : 0.0;

            if(totalThreat > stateToThreat[targetState])
              {
                stateToThreat[targetState] = totalThreat;
                maxThreatPredecessor[targetState] = {state, action};
              }
          }
      }

    // Reconstruct the best path
    CoordVector bestPath;
    std::vector<Actoid*> bestActoids;
    StateId currentState = sortedStates.back();

    while(maxThreatPredecessor.contains(currentState))
      {
        auto [prevState, action] = maxThreatPredecessor[currentState];
        bestPath.insert(bestPath.begin(), stateIdToCoord[currentState]);
        bestActoids.insert(bestActoids.begin(), action); 
        currentState = prevState;
      }

    // Calculate final threat
    double threatAcc = stateToThreat[sortedStates.back()];
    threatAcc -= getThreatForStayingAtCoord({currentPos}, combatant);

    msDAG.releaseActoidOwnership(bestActoids);

    return {{threatAcc}, bestPath, bestActoids};
  }

} // namespace enc