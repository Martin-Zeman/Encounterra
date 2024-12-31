#include "actions/action_selection.hpp"
#include "actions/movement.hpp"
#include "actions/action_proto_fsm.hpp"
#include "actions/break_grapple.hpp"
#include "core/battle_map.hpp"
#include "core/geometry.hpp"
#include "effects/effect_tracker.hpp"
// #include "combat/actions/movement.hpp"
#include <regex>
#include <limits>
#include <algorithm>
#include <iostream>

// Hash for CoordToSequenceIds
namespace std {
    template<>
    struct hash<std::pair<std::array<int, 2>, enc::MovementThreatType>> {
        size_t operator()(const std::pair<std::array<int, 2>, enc::MovementThreatType>& p) const {
            size_t h1 = std::hash<int>{}(p.first[0]);
            size_t h2 = std::hash<int>{}(p.first[1]);
            size_t h3 = std::hash<std::underlying_type_t<enc::MovementThreatType>>{}(
                static_cast<std::underlying_type_t<enc::MovementThreatType>>(p.second)
            );
            
            return h1 ^ (h2 << 1) ^ (h3 << 2);
        }
    };
}

namespace enc {

namespace {
    const std::regex REGEX_MOVEMENT_PATTERN(R"(([msdchio]+)_\((\d+), (\d+)\))");
    const std::regex REGEX_MS_MOVEMENT_PATTERN(R"([mschdio_]+\((\d+), (\d+)\))");
}

std::vector<std::vector<std::string>> pruneSequences(const std::vector<std::vector<std::string>> &sequences,
                                                     const std::unordered_map<std::string, std::shared_ptr<Actoid>> &transitionNameToAction,
                                                     const std::unordered_map<size_t, std::string> &indexToTransition,
                                                     const std::unordered_map<std::string, std::string> &transitionToSimplified)
{
  std::set<std::string> sequenceSets;
  std::vector<std::vector<std::string>> prunedSequences;

  for(const auto &sequence : sequences)
    {
      std::set<std::string> currentSequenceSet;
      for(const auto &txIdx : sequence)
        {
          auto it = transitionToSimplified.find(txIdx);
          if(it != transitionToSimplified.end())
            {
              currentSequenceSet.insert(it->second);
            }
        }

      std::string setKey = std::accumulate(currentSequenceSet.begin(), currentSequenceSet.end(), std::string{},
                                           [](const std::string &a, const std::string &b) { return a + "," + b; });

      if(sequenceSets.find(setKey) == sequenceSets.end())
        {
          prunedSequences.push_back(sequence);
          sequenceSets.insert(setKey);
        }
      else
        {
          bool hasAttackModifier = false;
          for(const auto &tx : sequence)
            {
              try
                {
                  const auto &action = transitionNameToAction.at(indexToTransition.at(std::stoul(tx)));
                  if(action->hasFlag(ActoidFlags::IS_ATTACK_MODIFIER))
                    {
                      hasAttackModifier = true;
                      break;
                    }
                }
              catch(const std::exception &)
                {
                  continue;
                }
            }
          if(hasAttackModifier)
            {
              prunedSequences.push_back(sequence);
            }
        }
    }
  return prunedSequences;
}


double getDistToActionSequenceCoord(const std::vector<std::shared_ptr<Actoid>> &sequence, const blaze::DynamicVector<int> &distances)
{
  auto &battleMap = BattleMap::getInstance();

  for(const auto &action : sequence)
    {
      if(action->hasFlag(ActoidFlags::IS_MOVEMENT))
        {
          // Using dynamic_cast since we know it's a movement action
          if(auto *movement = dynamic_cast<MovementIncrement *>(action.get()))
            {
              const Coord &increment = movement->getIncrement();
              return distances[increment[0] * battleMap.getGridSize() + increment[1]];
            }
        }
    }
  return 0.0; // No movement found, or sequence is at current position
}

std::pair<std::vector<std::shared_ptr<Actoid>>, ThreatScore>
getNearestAndMinimize(
    std::vector<std::vector<std::shared_ptr<Actoid>>>& sequences,
    const std::vector<size_t>& sortedSequences,
    const std::unordered_map<size_t, ThreatScore>& sequenceToThreat,
    const blaze::DynamicVector<int>& distances,
    const std::unordered_map<size_t, std::unordered_map<size_t, double>>& sequenceIdxToTransitionStepThreat)
{
    if (sortedSequences.empty()) {
        return {{}, ThreatScore{{}, 0.0}};
    }

    // Find max threat
    double maxThreat = 0.0;
    const auto& firstThreat = sequenceToThreat.at(sortedSequences[0]);
    maxThreat = firstThreat.first.back() + firstThreat.second;

    // Find sequences with max threat
    std::vector<size_t> maxThreatSequences;
    for (size_t idx : sortedSequences) {
        const auto& threat = sequenceToThreat.at(idx);
        if (std::abs((threat.first.back() + threat.second) - maxThreat) < 1e-6) {
            maxThreatSequences.push_back(idx);
        } else {
            break;
        }
    }

    // Find minimum distance among max threat sequences
    double minDist = std::numeric_limits<double>::max();
    for (size_t idx : maxThreatSequences) {
        double dist = getDistToActionSequenceCoord(sequences[idx], distances);
        minDist = std::min(minDist, dist);
    }

    // Filter sequences by min distance
    std::vector<size_t> minDistSequences;
    for (size_t idx : maxThreatSequences) {
        if (std::abs(getDistToActionSequenceCoord(sequences[idx], distances) - minDist) < 1e-6) {
            minDistSequences.push_back(idx);
        }
    }

    // Filter out transitions that contribute nothing
    for (size_t idx : minDistSequences) {
        auto& sequence = sequences[idx];
        std::vector<std::shared_ptr<Actoid>> newSequence;
        
        for (size_t tIdx = 0; tIdx < sequence.size(); ++tIdx) {
            bool shouldKeep = false;
            try {
                auto stepThreatIt = sequenceIdxToTransitionStepThreat.at(idx).find(tIdx);
                if (stepThreatIt != sequenceIdxToTransitionStepThreat.at(idx).end() && 
                    stepThreatIt->second > 0) {
                    shouldKeep = true;
                } else if (sequence[tIdx]->hasFlag(ActoidFlags::IS_PRIORITY)) {
                    shouldKeep = true;
                }
            } catch (const std::out_of_range&) {
                shouldKeep = true;  // Keep movement transitions
            }
            
            if (shouldKeep) {
                newSequence.push_back(sequence[tIdx]);
            }
        }
        sequence = std::move(newSequence);
    }

    // Sort by sequence length and get shortest
    auto shortestIdx = *std::min_element(minDistSequences.begin(), minDistSequences.end(),
        [&sequences](size_t a, size_t b) {
            return sequences[a].size() < sequences[b].size();
        });

    const auto& bestSequence = sequences[shortestIdx];
    if (bestSequence.size() == 1) {
        return {{}, ThreatScore{{}, 0.0}};  // Only movement action or NOP
    }

    return {bestSequence, sequenceToThreat.at(shortestIdx)};
}


SequenceSearchResult
findBestSequence(Combatant *combatant, const StateMachine &fsm,
                 const std::unordered_map<std::shared_ptr<Actoid>, std::vector<Coord>> &transitionToEligibleCoords,
                 std::unordered_map<std::shared_ptr<Actoid>, std::pair<Coord, MovementThreatType>> &movementTransToCoordAndMovementType,
                 const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths, double infeasibilityMultiplier)
{
  auto &battleMap = BattleMap::getInstance();

  // Get effect to coords mapping
  std::unordered_map<std::shared_ptr<AoeEffect>, std::vector<Coord>> effectToCoords;
  auto &effectTracker = EffectTracker::getInstance();
  for(const auto &effect : effectTracker.getAoeEffects())
    {
      effectToCoords[effect] = effect->getAffectedCoords();
    }

  // We'll need these for tracking sequences and their threats
  std::vector<std::vector<std::shared_ptr<Actoid>>> sequences;
  std::unordered_set<std::vector<std::shared_ptr<Actoid>>, ActoidVectorHash> sequenceSet;
  std::unordered_map<std::shared_ptr<Actoid>, CoordVector> transitionToMsPath;

  // Track threats
  std::unordered_map<size_t, ThreatScore> sequenceToThreat;
  std::unordered_map<size_t, std::unordered_map<size_t, double>> sequenceIdxToTransitionStepThreat;

  // Track coordinate mappings
  using CoordAndMovementType = std::pair<Coord, MovementThreatType>;
  std::unordered_map<CoordAndMovementType, std::vector<size_t>> coordToSequenceIds;
  // Remove Misty Step to current coordinate if it exists
  Coord currentCoords = battleMap.getCombatantCoordinates(*combatant).getRoot();
  for(auto it = movementTransToCoordAndMovementType.begin(); it != movementTransToCoordAndMovementType.end();)
    {
      if(it->second.first == currentCoords && it->first->getAbilityType() == AbilityType::MISTY_STEP)
        {
          it = movementTransToCoordAndMovementType.erase(it);
        }
      else
        {
          ++it;
        }
    }

  // DFS helper function
  std::function<void(StateId, std::vector<std::shared_ptr<Actoid>> &, const CoordAndMovementType *)> dfs;
  dfs = [&](StateId currentState, std::vector<std::shared_ptr<Actoid>> &currentSequence, const CoordAndMovementType *coord) {
    if(currentState == -1)
      { // NOP state
        // Create sequence set without depth indicators
        std::vector<std::shared_ptr<Actoid>> strippedSequence;
        bool containsThreatModifier = false;

        for(const auto &action : currentSequence)
          {
            if(!dynamic_cast<DummyActoid *>(action.get()))
              { // Skip dummy actions used for depth
                strippedSequence.push_back(action);
                if(action->hasFlag(ActoidFlags::IS_ATTACK_MODIFIER))
                  {
                    containsThreatModifier = true;
                  }
              }
          }

        if(containsThreatModifier || !sequenceSet.contains(strippedSequence))
          {
            sequences.push_back(currentSequence);
            sequenceSet.insert(strippedSequence);

            if(coord)
              {
                coordToSequenceIds[*coord].push_back(sequences.size() - 1);
              }
          }
        return;
      }

    for(const auto &[action, nextState] : fsm.getForwardTransitions(currentState))
      {
        currentSequence.push_back(action);

        auto it = movementTransToCoordAndMovementType.find(action);
        const CoordAndMovementType *newCoord = coord;
        if(it != movementTransToCoordAndMovementType.end())
          {
            newCoord = &it->second;
          }

        dfs(nextState, currentSequence, newCoord);
        currentSequence.pop_back();
      }
  };

  // Start DFS from initial state
  std::vector<std::shared_ptr<Actoid>> currentSequence;
  dfs(0, currentSequence, nullptr);
  // Clear threat calculation caches
  // TODO: Add cache clearing mechanism for C++

  // Movement transitions
  for(const auto &[coordAndType, ids] : coordToSequenceIds)
    {
      if(!ids.empty())
        {
          const auto &[coord, movementType] = coordAndType;

          auto pathOpt = battleMap.getPathToCoord(*combatant, coord, distances, shortestPaths, true);
          if(!pathOpt)
            continue; // Note that an empty path is still valid

          std::vector<double> movementThreat;
          switch(movementType)
            {
            case MovementThreatType::STANDARD: movementThreat = accumulateThreatAlongPath(*pathOpt, combatant, effectToCoords); break;

            case MovementThreatType::DISENGAGED: movementThreat = accumulateThreatAlongPath(*pathOpt, combatant, effectToCoords, true, false); break;

            case MovementThreatType::DODGED: movementThreat = accumulateThreatAlongPath(*pathOpt, combatant, effectToCoords, false, true); break;

              case MovementThreatType::MISTY_STEPPED: {
                auto [threat, msPath] = calcThreatForPathWithMistyStep(*pathOpt, combatant, effectToCoords);
                movementThreat = std::move(threat);
                // Find corresponding Misty Step action
                for(const auto &[action, nextState] : fsm.getForwardTransitions(0))
                  {
                    if(action->getAbilityType() == AbilityType::MISTY_STEP)
                      {
                        transitionToMsPath[action] = std::move(msPath);
                        break;
                      }
                  }
                break;
              }

            default:
              std::cerr << "Unknown movement type " << static_cast<int>(movementType) << "\n";
              movementThreat = accumulateThreatAlongPath(*pathOpt, combatant, effectToCoords);
              break;
            }

          // Initialize sequence threats with movement threat
          for(size_t idx : ids)
            {
              sequenceToThreat[idx].first = movementThreat;
            }
        }
    }

  // (Bonus) action transitions
  for(const auto &[coordAndType, ids] : coordToSequenceIds)
    {
      if(!ids.empty())
        {
          const auto &[coord, _] = coordAndType;
          // battleMap.clearCaches();

          battleMap.withCombatantPosition(combatant, coord, [&]() {
            for(size_t idx : ids)
              {
                std::shared_ptr<Actoid> deltaActionInSequence;
                double threatAcc = 0.0;
                bool firstFeasibilityCheckDone = false;
                double feasibilityMultiplier = 1.0;
                size_t deltaActionTIdx = 0;

                for(size_t tIdx = 0; tIdx < sequences[idx].size(); ++tIdx)
                  {
                    const auto &action = sequences[idx][tIdx];
                    if(auto *dummy = dynamic_cast<DummyActoid *>(action.get()))
                      {
                        break;
                      }

                    // Skip movement transitions
                    if(movementTransToCoordAndMovementType.contains(action))
                      {
                        continue;
                      }

                    battleMap.withCombatantWildshapeReplacement(*action, combatant, coord, [&](Combatant *transformedCombatant) {
                      if(!action->hasFlag(ActoidFlags::LOCATION_INDEPENDENT))
                        {
                          if(tIdx == 1)
                            {
                              // First location-dependent action after movement
                              feasibilityMultiplier = distances[coord[0] * battleMap.getGridSize() + coord[1]] <= combatant->getMovement()
                                                        ? 1.0
                                                        : infeasibilityMultiplier;
                              firstFeasibilityCheckDone = true;
                            }
                          else
                            {
                              auto eligibleCoordsOpt = action->getEligibleCoords(distances, shortestPaths);
                              if(!eligibleCoordsOpt || eligibleCoordsOpt->empty())
                                {
                                  return; // e.g. when there's no place to hide
                                }

                              if(!firstFeasibilityCheckDone)
                                {
                                  // Location-dependent action follows location-independent action
                                  feasibilityMultiplier
                                    = (std::find(eligibleCoordsOpt->begin(), eligibleCoordsOpt->end(), coord) != eligibleCoordsOpt->end()
                                       && distances[coord[0] * battleMap.getGridSize() + coord[1]] <= combatant->getMovement())
                                        ? 1.0
                                        : infeasibilityMultiplier;
                                  firstFeasibilityCheckDone = true;
                                }
                              else
                                {
                                  // Two location-dependent actions in succession
                                  int remainingDist = getHopDistanceCoords(*eligibleCoordsOpt, std::vector<Coord>{coord});
                                  feasibilityMultiplier
                                    = remainingDist <= combatant->getMovement() - distances[coord[0] * battleMap.getGridSize() + coord[1]]
                                        ? 1.0
                                        : infeasibilityMultiplier;
                                }
                            }
                        }

                      double threat = action->calculateThreat(
                        {{"consider_dist", transformedCombatant != combatant}, {"movement_threat", sequenceToThreat[idx].first}});
                      threatAcc += threat;

                      if(deltaActionInSequence)
                        {
                          double deltaThreat = deltaActionInSequence->calculateThreatForAttack(combatant, action.get(), {});
                          threatAcc += deltaThreat;
                          sequenceIdxToTransitionStepThreat[idx][deltaActionTIdx] += deltaThreat;
                        }

                      if(action->hasFlag(ActoidFlags::IS_ATTACK_MODIFIER))
                        {
                          deltaActionInSequence = action;
                          deltaActionTIdx = tIdx;
                        }

                      // Add threats from existing modifiers
                      for(const auto& existingDeltaEffect : effectTracker.getAffectingCombatant(combatant))
                        {
                          if(auto modifier = std::dynamic_pointer_cast<AttackThreatModifier>(existingDeltaEffect))
                            {
                              threatAcc += modifier->calculateThreatForAttack(combatant, action.get(), {});
                            }
                        }

                      // Store individual transition threats
                      try
                        {
                          sequenceIdxToTransitionStepThreat[idx][tIdx] = threat;
                        }
                      catch(const std::out_of_range &)
                        {
                          sequenceIdxToTransitionStepThreat[idx] = {{tIdx, threat}};
                        }
                    });
                  }

                // Update final threat
                sequenceToThreat[idx].second = threatAcc * feasibilityMultiplier;

                // Add small bias for current position
                if(coord == currentCoords)
                  {
                    sequenceToThreat[idx].first.back() += 0.01;
                  }
              }
          });
        }
    }

  // Sort sequences by total threat
  std::vector<size_t> sortedSequences;
  sortedSequences.reserve(sequenceToThreat.size());
  for(const auto &[idx, _] : sequenceToThreat)
    {
      sortedSequences.push_back(idx);
    }

  std::sort(sortedSequences.begin(), sortedSequences.end(), [&](size_t a, size_t b) {
    const auto &threatA = sequenceToThreat[a];
    const auto &threatB = sequenceToThreat[b];
    double totalA = threatA.second > 0 ? (threatA.first.back() + threatA.second) : -std::numeric_limits<double>::infinity();
    double totalB = threatB.second > 0 ? (threatB.first.back() + threatB.second) : -std::numeric_limits<double>::infinity();
    return totalA > totalB;
  });

  auto [nearestSequence, maxThreat]
    = getNearestAndMinimize(sequences, sortedSequences, sequenceToThreat, distances, sequenceIdxToTransitionStepThreat);

  return {std::move(nearestSequence), std::move(maxThreat), std::move(transitionToMsPath)};
}

std::shared_ptr<Actoid> getAction(Combatant *combatant)
{
  auto &battleMap = BattleMap::getInstance();
  // battleMap.clearCaches();

  // Get current form (handles possible wildshape)
  combatant = combatant->getCurrentForm();

  // Handle grapple condition
  if(auto grappleCondition = combatant->needsToBreakOutOfGrapple())
    {
      if(combatant->hasAction())
        {
          auto factory = std::make_unique<BreakGrappleFactory>(grappleCondition);
          return factory->create(nullptr);
        }
    }

  // Handle prone condition
  if(combatant->isAffectedBy(Conditions::PRONE) && combatant->getMovement() >= combatant->getSpeed() / 2)
    {
      auto factory = std::make_unique<GetUpFactory>(combatant);
      return factory->create(nullptr);
    }

  // Calculate paths
  auto [distances, shortestPaths] = battleMap.calcDijkstra(*combatant);
  combatant->setShortestPathsCache(shortestPaths);

  // Check existing action plan
  if(!combatant->getActionPlan().empty())
    {
      auto firstAction = combatant->getActionPlan().front();
      if(auto *movement = dynamic_cast<MovementIncrement *>(firstAction.get()))
        {
          if(combatant->getMovement() > 0)
            {
              combatant->popActionPlan();
              return firstAction;
            }
        }
    }

  // Calculate new action plan
  auto newPlan = combatant->calculateActionPlan(distances, shortestPaths);
  combatant->setActionPlan(std::move(newPlan));

  if(combatant->getActionPlan().empty())
    {
      return nullptr; // Either no action possible or all actions already used
    }

  return combatant->popActionPlan();
}

} // namespace enc
