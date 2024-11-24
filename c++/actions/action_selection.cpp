#include "actions/action_selection.hpp"
#include "actions/movement.hpp"
#include "core/battle_map.hpp"
#include "core/threat_utils.hpp"
#include "core/geometry.hpp"
// #include "combat/actions/movement.hpp"
#include <regex>
#include <limits>
#include <algorithm>
#include <iostream>

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

CoordToSequenceIds createCoordToSequenceMapping(
    const std::vector<std::vector<std::string>>& sequences,
    const MovementTransitionMap& movementTransitionToCoordAndType
) {
    CoordToSequenceIds coordToSequenceIds;
    
    for (size_t idx = 0; idx < sequences.size(); ++idx) {
        std::optional<std::pair<Coord, MovementThreatType>> coord;
        
        for (const auto& tx : sequences[idx]) {
            auto it = movementTransitionToCoordAndType.find(tx);
            if (it != movementTransitionToCoordAndType.end()) {
                coord = it->second;
                break;
            }
        }
        
        if (coord) {
            coordToSequenceIds[*coord].push_back(idx);
        }
    }
    
    return coordToSequenceIds;
}

double getDistToActionSequenceCoord(const std::vector<std::string> &sequence, const blaze::DynamicVector<int> &distances)
{
  std::smatch match;
  for(const auto &transition : sequence)
    {
      if(transition == "dummy")
        continue;

      if(std::regex_search(transition, match, REGEX_MOVEMENT_PATTERN))
        {
          int x = std::stoi(match[2]);
          int y = std::stoi(match[3]);
          auto &battleMap = BattleMap::getInstance();
          return distances[x * battleMap.getGridSize() + y];
        }
    }
    return 0.0;
}

std::pair<std::vector<std::string>, std::array<double, 2>>
getNearestAndMinimize(std::vector<std::vector<std::string>> &sequences, const std::vector<size_t> &sortedSequences,
                      const SequenceToThreat &sequenceToThreat, const blaze::DynamicVector<int> &distances,
                      const TransitionStepThreat &sequenceIdxToTransitionStepThreat,
                      const std::unordered_map<std::string, std::shared_ptr<Actoid>> &transitionNameToAction)
{
  if(sortedSequences.empty())
    {
      return {{}, {0.0, 0.0}};
    }

    // Find max threat
    double maxThreat = 0.0;
    const auto& firstThreat = sequenceToThreat.at(sortedSequences[0]);
    maxThreat = firstThreat[0] + firstThreat[1];

    // Find sequences with max threat
    std::vector<size_t> maxThreatSequences;
    for (size_t idx : sortedSequences) {
        const auto& threat = sequenceToThreat.at(idx);
        if (std::abs((threat[0] + threat[1]) - maxThreat) < 1e-6) {
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
        std::vector<std::string> newSequence;
        
        for (size_t tIdx = 0; tIdx < sequence.size(); ++tIdx) {
            bool shouldKeep = false;
            try {
                auto stepThreatIt = sequenceIdxToTransitionStepThreat.at(idx).find(tIdx);
                if (stepThreatIt != sequenceIdxToTransitionStepThreat.at(idx).end() && 
                    stepThreatIt->second > 0) {
                    shouldKeep = true;
                } else {
                    auto actionIt = transitionNameToAction.find(sequence[tIdx]);
                    if (actionIt != transitionNameToAction.end() && 
                        actionIt->second->hasFlag(ActoidFlags::IS_PRIORITY)) {
                        shouldKeep = true;
                    }
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
        return {{}, {0.0, 0.0}};  // Only movement action or NOP
    }

    return {bestSequence, sequenceToThreat.at(shortestIdx)};
}

void decodeMsPathToActions(
    Combatant* combatant,
    const Coord& initialCoord,
    const std::vector<std::string>& msPath,
    std::vector<std::shared_ptr<Actoid>>& actions,
    std::shared_ptr<ActoidFactory> msFactory
) {
    std::optional<size_t> beforeMsIdx;
    std::optional<size_t> msIdx;
    
    // Find indices
    for (size_t i = 0; i < msPath.size(); ++i) {
        if (msPath[i].substr(0, 2) == "m_") {
            beforeMsIdx = i;
        } else if (msPath[i].substr(0, 3) == "ms_") {
            msIdx = i;
            break;
        }
    }
    
    std::optional<size_t> afterMsIdx = msIdx && msIdx < msPath.size() - 1 ? 
        std::optional<size_t>(msPath.size() - 1) : std::nullopt;

    // Handle pre-MS movement
    if(beforeMsIdx)
      {
        std::vector<Coord> beforePath = {initialCoord};
        for(size_t i = 0; i <= *beforeMsIdx; ++i)
          {
            std::smatch match;
            if(std::regex_search(msPath[i], match, REGEX_MS_MOVEMENT_PATTERN))
              {
                beforePath.push_back({std::stoi(match[1]), std::stoi(match[2])});
              }
          }

        auto incrementPath = convertPathToIncrements(beforePath);
        auto movementFactory = std::make_unique<MovementFactory>(combatant, incrementPath, AbilityType::STANDARD_MOVEMENT);
        auto moveActions = movementFactory->createAll();
        actions.insert(actions.end(), moveActions.begin(), moveActions.end());
      }

    // Handle MS
    if (msIdx) {
        std::smatch match;
        if (std::regex_search(msPath[*msIdx], match, REGEX_MS_MOVEMENT_PATTERN)) {
            Coord msCoord = {std::stoi(match[1]), std::stoi(match[2])};
            actions.push_back(msFactory->create(&msCoord));
        }
    }

    // Handle post-MS movement
    if(afterMsIdx)
      {
        std::vector<Coord> afterPath = {actions.back()->getCoord()};
        for(size_t i = *msIdx + 1; i <= *afterMsIdx; ++i)
          {
            std::smatch match;
            if(std::regex_search(msPath[i], match, REGEX_MS_MOVEMENT_PATTERN))
              {
                afterPath.push_back({std::stoi(match[1]), std::stoi(match[2])});
              }
          }

        auto incrementPath = convertPathToIncrements(afterPath);
        auto movementFactory = std::make_unique<MovementFactory>(combatant, incrementPath, AbilityType::STANDARD_MOVEMENT);
        auto moveActions = movementFactory->createAll();
        actions.insert(actions.end(), moveActions.begin(), moveActions.end());
      }
}

std::vector<std::shared_ptr<Actoid>>
translateSequenceToActions(Combatant *combatant, const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths,
                           const std::unordered_map<std::string, std::shared_ptr<Actoid>> &transitionNameToAction,
                           const MovementTransitionMap &movementTransitionToCoordAndType, const std::vector<std::string> &sequence,
                           const TransitionToMsPath &transitionNameToMsPath)
{
  std::vector<std::shared_ptr<Actoid>> actions;
  auto &battleMap = BattleMap::getInstance();

  for(const auto &transition : sequence)
    {
      if(transition == "dummy")
        continue;

      try
        {
          actions.push_back(transitionNameToAction.at(transition));
        }
      catch(const std::out_of_range &)
        {
          try
            {
              const auto &[coord, movementType] = movementTransitionToCoordAndType.at(transition);

              switch(movementType)
                {
                case MovementThreatType::STANDARD:
                  case MovementThreatType::DODGED: {
                    auto pathOpt = battleMap.getPathToCoord(*combatant, coord, distances, shortestPaths, true);
                    if(!pathOpt)
                      {
                        std::cerr << "Could not find path for standard movement\n";
                        continue;
                      }
                    auto movementFactory = std::make_unique<MovementFactory>(combatant, *pathOpt, AbilityType::STANDARD_MOVEMENT);
                    auto moveActions = movementFactory->createAll();
                    actions.insert(actions.end(), moveActions.begin(), moveActions.end());
                    break;
                  }
                  case MovementThreatType::DISENGAGED: {
                    auto pathOpt = battleMap.getPathToCoord(*combatant, coord, distances, shortestPaths, false);
                    if(!pathOpt)
                      {
                        std::cerr << "Could not find path for disengage movement\n";
                        continue;
                      }
                    auto movementFactory = std::make_unique<MovementFactory>(combatant, *pathOpt, AbilityType::DISENGAGED_MOVEMENT);
                    auto moveActions = movementFactory->createAll();
                    actions.insert(actions.end(), moveActions.begin(), moveActions.end());
                    break;
                  }
                  case MovementThreatType::MISTY_STEPPED: {
                    auto msFactory = getFactoryOfType(combatant->getBonusActionFactoriesConst(), AbilityType::MISTY_STEP);
                    if(!msFactory)
                      {
                        std::cerr << "Could not find Misty Step factory\n";
                        continue;
                      }
                    decodeMsPathToActions(combatant, battleMap.getCombatantCoordinates(combatant), transitionNameToMsPath.at(transition), actions,
                                          msFactory);
                    break;
                  }
                default: std::cerr << "Unknown movement type: " << static_cast<int>(movementType) << '\n';
                }
            }
          catch(const std::out_of_range &)
            {
              std::cerr << "Unknown transition type: " << transition << '\n';
            }
        }
    }

  return actions;
}

std::optional<DagBuildResult> buildActionDag(Combatant *combatant, const std::unique_ptr<ActionDag> &protoDag,
                                             const std::unordered_map<std::string, std::shared_ptr<Actoid>> &transitionNameToAction,
                                             const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
{
  auto &battleMap = BattleMap::getInstance();
  battleMap.calcVisibilityDictForAllCoords(combatant, shortestPaths);

  // Clear calculation caches
  // for (const auto& [_, action] : transitionNameToAction) {
  //     action->clearCache();
  // }

  // Get post-transitions of priority actions
  PostTransitions postPriorityActionTransitions;
  PostTransitions postPriorityBonusActionTransitions;
  auto protoTransitions = protoDag->getAllTransitions();

  // Handle Misty Step related transitions
  std::optional<std::vector<std::pair<std::string, std::string>>> postMistyStepTransitions;
  if(std::find(protoTransitions.begin(), protoTransitions.end(), "Misty Step to 0, 0_1") != protoTransitions.end())
    {
      auto tempDag = std::make_unique<ActionDag>(*protoDag);
      tempDag->trigger("Misty Step to 0, 0_1");

      std::vector<std::pair<std::string, std::string>> msTransitions;
      try
        {
          for(const auto &trans : tempDag->getForwardTransitions(tempDag->getState()))
            {
              const auto &action = transitionNameToAction.at(trans.first);
              if(!action->hasFlag(ActoidFlags::IS_PRIORITY))
                {
                  msTransitions.push_back(trans);
                }
            }
            postMistyStepTransitions = msTransitions;
        } catch (const std::out_of_range&) {
            // No transitions available
        }
        
        tempDag->reset();
        tempDag->removeTransition("Misty Step to 0, 0_1", "0");
    }

    // Create the main DAG
    auto dag = std::make_unique<ActionDag>(*protoDag);

    // Create transition to eligible coords mapping
    TransitionToEligibleCoords transitionToEligibleCoords;
    for (const auto& transitionName : protoTransitions) {
        if (transitionName == "dummy") continue;
        
        try {
            const auto& action = transitionNameToAction.at(transitionName);
            if (action->getFactory().getCombatant()->getCurrentForm() != 
                action->getFactory().getCombatant()->getOriginalForm()) {
                // Handle wildshape case
                auto tempCombatant = action->getFactory().getCombatant()->getOriginalForm();
                auto coords = action->getEligibleCoords(distances, shortestPaths);
                if (!coords.empty()) {
                    transitionToEligibleCoords[transitionName] = std::move(coords);
                }
            } else {
                auto coords = action->getEligibleCoords(distances, shortestPaths);
                if (!coords.empty()) {
                    transitionToEligibleCoords[transitionName] = std::move(coords);
                }
            }
        } catch (const std::out_of_range&) {
            continue;
        }
    }

    // Remove transitions without eligible coords
    for (const auto& transitionName : protoTransitions) {
        if (transitionToEligibleCoords.find(transitionName) == transitionToEligibleCoords.end()) {
            dag->removeTransition(transitionName, "0");
        }
    }

    MovementTransitionMap movementTransitionToCoordAndType;
    
    // Build movement transitions
    for (const auto& [transitionName, coords] : transitionToEligibleCoords) {
        if (transitionName.find("Misty Step") == 0) continue;
        
        auto transitions = protoDag->getTransitionsFromSource(transitionName, "0");
        if (transitions.empty()) continue;

        auto transition = transitions[0];
        for (const auto& coord : coords) {
            std::string movementStateName = "m_state_" + std::to_string(coord[0]) + "_" + std::to_string(coord[1]);
            std::string movementTransitionName = "m_(" + std::to_string(coord[0]) + ", " + std::to_string(coord[1]) + ")";
            
            movementTransitionToCoordAndType[movementTransitionName] = {coord, MovementThreatType::STANDARD};
            dag->addTransition(movementTransitionName, "0", movementStateName);
            dag->addTransition(transitionName, movementStateName, transition.second);
        }
        
        dag->removeTransition(transitionName, "0");
    }

    // Handle special transitions (Misty Step, Dodge, Disengage)
    if (postMistyStepTransitions) {
        buildMistyStepTransitions(*dag, *postMistyStepTransitions, transitionToEligibleCoords, movementTransitionToCoordAndType);
    }

    if (!dag->getAllTransitions().empty() && dag->getAllTransitions()[0] != "None_0") {
        return DagBuildResult{
            std::move(dag),
            std::move(movementTransitionToCoordAndType),
            std::move(transitionToEligibleCoords)
        };
    }

    return std::nullopt;
}

std::optional<BestSequenceResult>
findBestSequence(Combatant *combatant, const ActionDag &dag, const std::unordered_map<std::string, std::shared_ptr<Actoid>> &transitionNameToAction,
                 const TransitionToEligibleCoords &transitionToEligibleCoords, const MovementTransitionMap &movementTransitionToCoordAndType,
                 const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths, double infeasibilityMultiplier)
{
  auto &battleMap = BattleMap::getInstance();
  auto &effectTracker = EffectTracker::getInstance();
  std::unordered_map<Effect *, std::vector<Coord>> effectToCoords;
  for(const auto &effect : effectTracker.getAoeEffects())
    {
      effectToCoords[effect.get()] = effect->getAffectedCoords();
    }

    TransitionToMsPath transitionNameToMsPath;
    SequenceToThreat sequenceToThreat;
    TransitionStepThreat sequenceIdxToTransitionStepThreat;
    
    Coord currentCoords = battleMap.getCombatantCoordinates(combatant);
    
    // Remove Misty Step to current coordinate if it exists
    auto msCurrentCoordKey = "ms_(" + std::to_string(currentCoords[0]) + ", " + std::to_string(currentCoords[1]) + ")";
    if (auto mtcIt = movementTransitionToCoordAndType.find(msCurrentCoordKey); 
        mtcIt != movementTransitionToCoordAndType.end()) {
        const_cast<MovementTransitionMap&>(movementTransitionToCoordAndType).erase(mtcIt);
    }

    // Get all sequences
    auto [dagForward, numStates, indexToState, indexToTransition, transitionToSimplified] = dag.getNumbaCompatibleData();
    size_t maxSequenceLength = numStates * 2;
    
    auto allSequences = dag.dfs(0, maxSequenceLength);
    auto prunedSequences = pruneSequences(allSequences, transitionNameToAction, indexToTransition, transitionToSimplified);
    
    std::vector<std::vector<std::string>> sequences;
    for (const auto& arr : prunedSequences) {
        std::vector<std::string> sequence;
        for (const auto& item : arr) {
            auto it = indexToTransition.find(std::stoul(item));
            sequence.push_back(it != indexToTransition.end() ? it->second : "Unknown_" + item);
        }
        sequences.push_back(sequence);
    }

    auto coordToSequenceIds = createCoordToSequenceMapping(sequences, movementTransitionToCoordAndType);

    // Clear threat calculation caches
    ThreatUtils::clearAccumulateThreatCache();
    ThreatUtils::clearAoeAndAooThreatCache();

    // Calculate movement threats
    for (const auto& [coordAndType, ids] : coordToSequenceIds) {
        if (coordAndType.first.empty()) continue;
        
        const auto& [coord, movementType] = coordAndType;
        auto path = battleMap.getPathToCoord(combatant, coord, distances, shortestPaths, true);
        if (path.empty() || path[0] != currentCoords) continue;

        double movementThreat = 0.0;
        std::vector<std::string> mistyStepPath;

        switch (movementType) {
            case MovementThreatType::STANDARD:
                movementThreat = ThreatUtils::accumulateThreatAlongPath(path, combatant, effectToCoords);
                break;

            case MovementThreatType::DISENGAGED:
                movementThreat = ThreatUtils::accumulateThreatAlongPath(path, combatant, effectToCoords, true);
                break;

            case MovementThreatType::DODGED:
                movementThreat = ThreatUtils::accumulateThreatAlongPath(path, combatant, effectToCoords, false, true);
                break;

            case MovementThreatType::MISTY_STEPPED: {
                auto [threat, msPath] = ThreatUtils::calcThreatForPathWithMistyStep(path, combatant, effectToCoords);
                movementThreat = threat;
                mistyStepPath = msPath;
                std::string msKey = "ms_" + std::to_string(coord[0]) + "," + std::to_string(coord[1]);
                transitionNameToMsPath[msKey] = msPath;
                break;
            }

            default:
                std::cerr << "Unknown movement type " << static_cast<int>(movementType) << '\n';
                movementThreat = ThreatUtils::accumulateThreatAlongPath(path, combatant, effectToCoords);
        }

        for (size_t idx : ids) {
            sequenceToThreat[idx] = {movementThreat, 0.0};
        }
    }

    // Calculate action threats
    for (const auto& [coordAndType, ids] : coordToSequenceIds) {
        if (coordAndType.first.empty()) continue;
        
        const auto& [coord, _] = coordAndType;
        // battleMap.clearCaches();
        
        auto withPosition = [&](const std::function<void()>& fn) {
            battleMap.withCombatantPosition(combatant, coord, fn);
        };

        withPosition([&]() {
            for (size_t idx : ids) {
                std::shared_ptr<AttackThreatModifier> deltaAction;
                double threatAcc = 0.0;
                bool firstFeasibilityCheckDone = false;
                double feasibilityMultiplier = 1.0;
                size_t deltaActionTIdx = 0;

                for (size_t tIdx = 0; tIdx < sequences[idx].size(); ++tIdx) {
                    const auto& transition = sequences[idx][tIdx];
                    if (transition == "dummy") break;

                    try {
                        const auto& action = transitionNameToAction.at(transition);
                        
                        battleMap.withWildshapeIfNeeded(action, combatant, coord, [&]() {
                            if (!action->hasFlag(ActoidFlags::LOCATION_INDEPENDENT)) {
                                if (tIdx == 1) {
                                    feasibilityMultiplier = distances[coord[0] * battleMap.getGridSize() + coord[1]] <= 
                                        combatant->getMovement() ? 1.0 : infeasibilityMultiplier;
                                    firstFeasibilityCheckDone = true;
                                } else if (tIdx > 1) {
                                    const auto& eligibleCoords = transitionToEligibleCoords.at(transition);
                                    if (eligibleCoords.empty()) return;

                                    if (!firstFeasibilityCheckDone) {
                                        feasibilityMultiplier = (std::find(eligibleCoords.begin(), eligibleCoords.end(), coord) != 
                                            eligibleCoords.end() && distances[coord[0] * battleMap.getGridSize() + coord[1]] <= 
                                            combatant->getMovement()) ? 1.0 : infeasibilityMultiplier;
                                        firstFeasibilityCheckDone = true;
                                    } else {
                                        auto remainingDist = ThreatUtils::getHopDistanceCoords(eligibleCoords, {coord});
                                        feasibilityMultiplier = remainingDist <= combatant->getMovement() - 
                                            distances[coord[0] * battleMap.getGridSize() + coord[1]] ? 1.0 : infeasibilityMultiplier;
                                    }
                                }
                            }

                            double threat = action->calculateThreat(!battleMap.isWildshapeActive(), sequenceToThreat[idx][0]);
                            threatAcc += threat;

                            if (deltaAction) {
                                double deltaThreat = deltaAction->calculateThreatForAttack(combatant, action);
                                threatAcc += deltaThreat;
                                sequenceIdxToTransitionStepThreat[idx][deltaActionTIdx] += deltaThreat;
                            }

                            if (auto attackMod = std::dynamic_pointer_cast<AttackThreatModifier>(action)) {
                                deltaAction = attackMod;
                                deltaActionTIdx = tIdx;
                            }

                            for (const auto& existingEffect : battleMap.getEffectTracker().getAffectingCombatant(combatant)) {
                                if (auto existingMod = std::dynamic_pointer_cast<AttackThreatModifier>(existingEffect)) {
                                    threatAcc += existingMod->calculateThreatForAttack(combatant, action);
                                }
                            }

                            try {
                                sequenceIdxToTransitionStepThreat[idx][tIdx] = threat;
                            } catch (...) {
                                sequenceIdxToTransitionStepThreat[idx] = {{tIdx, threat}};
                            }
                        });

                    } catch (const std::out_of_range&) {
                        continue;  // Skip movement transitions
                    }
                }

                auto& threat = sequenceToThreat[idx];
                threat[1] = threatAcc * feasibilityMultiplier;
                // Small bias towards current position prevents oscillations
                threat[0] += (coord == currentCoords) ? 0.01 : 0.0;
            }
        });
    }

    // Sort sequences by total threat
    std::vector<size_t> sortedSequences(sequences.size());
    std::iota(sortedSequences.begin(), sortedSequences.end(), 0);
    
    std::sort(sortedSequences.begin(), sortedSequences.end(),
        [&](size_t a, size_t b) {
            const auto& threatA = sequenceToThreat[a];
            const auto& threatB = sequenceToThreat[b];
            return (threatA[1] > 0 ? threatA[0] + threatA[1] : -std::numeric_limits<double>::infinity()) >
                   (threatB[1] > 0 ? threatB[0] + threatB[1] : -std::numeric_limits<double>::infinity());
        });

    auto [nearestAndMinimizedSequence, maxThreat] = getNearestAndMinimize(
        sequences, sortedSequences, sequenceToThreat, distances,
        sequenceIdxToTransitionStepThreat, transitionNameToAction);

    if (nearestAndMinimizedSequence.empty()) {
        return std::nullopt;
    }

    return BestSequenceResult{
        std::move(nearestAndMinimizedSequence),
        std::move(transitionNameToMsPath),
        maxThreat
    };
}

// Main action selector function
std::shared_ptr<Actoid> getAction(Combatant* combatant) {
    auto& battleMap = BattleMap::getInstance();
    // battleMap.clearCaches();
    
    // Handle wildshape
    combatant = combatant->getCurrentForm();

    // Check if we need to break grapple
    if (auto grappleCond = needsToBreakOutOfGrapple(combatant)) {
        if (combatant->hasAction()) {
            return BreakGrappleFactory(grappleCond).create();
        }
    }

    // Check if we need to get up from prone
    if (combatant->isAffectedBy(Conditions::PRONE) && 
        combatant->getMovement() >= combatant->getSpeed() / 2) {
        return GetUpFactory().create();
    }

    // Calculate distances and paths
    auto [distances, shortestPaths] = battleMap.calcDijkstra(*combatant);
    combatant->setShortestPathsCache(shortestPaths);

    // Check existing action plan
    if (!combatant->getActionPlan().empty()) {
        auto firstAction = combatant->getActionPlan().front();
        if (auto movementIncrement = std::dynamic_pointer_cast<MovementIncrement>(firstAction)) {
            if (combatant->getMovement() > 0) {
                combatant->getActionPlan().pop_front();
                return movementIncrement;
            }
        }
    }

    // Calculate new action plan if needed
    combatant->setActionPlan(combatant->calculateActionPlan(distances, shortestPaths));
    
    // Return first action from plan or nullptr if no actions possible
    if (combatant->getActionPlan().empty()) {
        return nullptr;
    }
    
    auto action = combatant->getActionPlan().front();
    combatant->getActionPlan().pop_front();
    return action;
}

} // namespace enc