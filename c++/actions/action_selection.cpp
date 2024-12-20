#include "actions/action_selection.hpp"
#include "actions/movement.hpp"
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

std::pair<std::vector<std::string>, std::pair<std::vector<double>, double>>
getNearestAndMinimize(std::vector<std::vector<std::string>> &sequences, const std::vector<size_t> &sortedSequences,
                      const SequenceToThreat &sequenceToThreat, const blaze::DynamicVector<int> &distances,
                      const TransitionStepThreat &sequenceIdxToTransitionStepThreat,
                      const std::unordered_map<std::string, std::shared_ptr<Actoid>> &transitionNameToAction)
{
  if(sortedSequences.empty())
    {
      return {{}, {{}, 0.0}};
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
        return {{}, {{}, 0.0}};  // Only movement action or NOP
    }

    return {bestSequence, sequenceToThreat.at(shortestIdx)};
}

void decodeMsPathToActions(
    Combatant* combatant,
    const Coord& initialCoord,
    const std::vector<std::string>& msPath,
    std::vector<std::shared_ptr<Actoid>>& actions,
    std::shared_ptr<ActoidFactory>& msFactory
) {
    std::optional<size_t> beforeMsIdx;
    std::optional<size_t> msIdx;
    Coord msCoord;
    
    // Find indices
    for (size_t i = 0; i < msPath.size(); ++i) {
        if (msPath[i].substr(0, 2) == "m_") {
            beforeMsIdx = i;
        } else if (msPath[i].substr(0, 3) == "ms_") {
            msIdx = i;
            break;
        }
    }

    if (!msIdx.has_value()){
      throw std::runtime_error("No Misty Step found in a Misty Step sequence!");
    }
    
    std::optional<size_t> afterMsIdx = msIdx && msIdx < msPath.size() - 1 ? 
        std::optional<size_t>(msPath.size() - 1) : std::nullopt;

    // Handle pre-MS movement
    if(beforeMsIdx)
      {
        CoordVector beforePath = {initialCoord};
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
      std::smatch match;
      if (std::regex_search(msPath[*msIdx], match, REGEX_MS_MOVEMENT_PATTERN)) {
          msCoord = {std::stoi(match[1]), std::stoi(match[2])};
          actions.push_back(msFactory->create(&msCoord));
      }

    // Handle post-MS movement
    if(afterMsIdx)
      {
        CoordVector afterPath = {msCoord};
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
                    std::shared_ptr<ActoidFactory> msFactory = combatant->getActionFactory(AbilityType::MISTY_STEP).lock();
                    if(!msFactory)
                      {
                        std::cerr << "Could not find Misty Step factory\n";
                        continue;
                      }
                    decodeMsPathToActions(combatant, battleMap.getCombatantCoordinates(*combatant).getRoot(), transitionNameToMsPath.at(transition), actions,
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

// std::optional<DagBuildResult> buildActionDag(Combatant *combatant, const std::unique_ptr<StateMachine> &protoDag,
//                                              const std::unordered_map<std::string, std::shared_ptr<Actoid>> &transitionNameToAction,
//                                              const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
// {
//   auto &battleMap = BattleMap::getInstance();
//   battleMap.calcVisibilityDictForAllCoords(combatant, shortestPaths);

//   // Clear calculation caches
//   // for (const auto& [_, action] : transitionNameToAction) {
//   //     action->clearCache();
//   // }

//   auto protoTransitions = protoDag->getAllTransitions();

//   // Get post-transitions of priority actions
//   PostTransitions postPriorityActionTransitions;
//   PostTransitions postPriorityBonusActionTransitions;

//   // Handle Post Misty Step transitions
//   std::optional<std::vector<std::pair<std::string, StateId>>> postMistyStepTransitions;
//   if(std::find(protoTransitions.begin(), protoTransitions.end(), "Misty Step to 0, 0_1") != protoTransitions.end())
//     {
//       auto tempDag = std::make_unique<StateMachine>(*protoDag);
//       tempDag->triggerTransition("Misty Step to 0, 0_1");

//       std::vector<std::pair<std::string, StateId>> msTransitions;
//       try
//         {
//           for(const auto &trans : tempDag->getForwardTransitions(tempDag->getCurrentState()))
//             {
//               const auto &action = transitionNameToAction.at(trans.first);
//               if(!action->hasFlag(ActoidFlags::IS_PRIORITY))
//                 {
//                   msTransitions.push_back(trans);
//                 }
//             }
//             postMistyStepTransitions = msTransitions;
//         } catch (const std::out_of_range&) {
//             // No transitions available
//         }
        
//         // tempDag->reset();
//         // tempDag->removeTransition("Misty Step to 0, 0_1", 0);
//     }

//     // Create the main DAG
//     auto dag = std::make_unique<StateMachine>(*protoDag);

//     // Create transition to eligible coords mapping
//     TransitionToEligibleCoords transitionToEligibleCoords;
//     for (const auto& transitionName : protoTransitions) {
//         if (transitionName == "dummy") continue;
        
//         try {
//             const auto& action = transitionNameToAction.at(transitionName);
//             if (action->getFactory().getCombatant()->getCurrentForm() != 
//                 action->getFactory().getCombatant()->getOriginalForm()) {
//                 // Handle wildshape case
//                 auto tempCombatant = action->getFactory().getCombatant()->getOriginalForm();
//                 auto coords = action->getEligibleCoords(distances, shortestPaths);
//                 if (!coords.has_value()) {
//                     transitionToEligibleCoords[transitionName] = std::move(coords.value());
//                 }
//             } else {
//                 auto coords = action->getEligibleCoords(distances, shortestPaths);
//                 if (!coords.has_value()) {
//                     transitionToEligibleCoords[transitionName] = std::move(coords.value());
//                 }
//             }
//         } catch (const std::out_of_range&) {
//             continue;
//         }
//     }

//     // Remove transitions without eligible coords
//     for (const auto& transitionName : protoTransitions) {
//         if (transitionToEligibleCoords.find(transitionName) == transitionToEligibleCoords.end()) {
//             dag->removeTransition(transitionName, 0);
//         }
//     }

//     MovementTransitionMap movementTransitionToCoordAndType;
    
//     // Build movement transitions
//     std::vector<std::pair<std::string, StateId>> transitionsFromRoot = protoDag->getForwardTransitions(0); // @todo: consider using a set here
//     for (const auto& [transitionName, coords] : transitionToEligibleCoords) {
//         if(transitionName.find("Misty Step") == 0)
//           {
//             continue;
//           }
//         auto transition = std::find_if(transitionsFromRoot.begin(), transitionsFromRoot.end(), [&transitionName](const auto& pair) { return pair.first == transitionName; });
//         if (transition == transitionsFromRoot.end())
//           {
//             continue;
//           }

//         for (const auto& coord : coords) {
//             // std::string movementStateName = "m_state_" + std::to_string(coord[0]) + "_" + std::to_string(coord[1]);
//             int movementStateId = protoDag->getNextStateId();
//             std::string movementTransitionName = "m_(" + std::to_string(coord[0]) + ", " + std::to_string(coord[1]) + ")";
            
//             movementTransitionToCoordAndType[movementTransitionName] = {coord, MovementThreatType::STANDARD};
//             dag->addTransition(movementTransitionName, 0, movementStateId);
//             dag->addTransition(transitionName, movementStateId, transition->second);
//         }
        
//         dag->removeTransition(transitionName, 0);
//     }

//     // Handle special transitions (Misty Step, Dodge, Disengage)
//     if (postMistyStepTransitions) {
//         buildMistyStepTransitions(*dag, *postMistyStepTransitions, transitionToEligibleCoords, movementTransitionToCoordAndType);
//     }

//     if (!dag->getAllTransitions().empty() && dag->getAllTransitions()[0] != "None_0") {
//         return DagBuildResult{
//             std::move(dag),
//             std::move(movementTransitionToCoordAndType),
//             std::move(transitionToEligibleCoords)
//         };
//     }

//     return std::nullopt;
// }

std::pair<std::unordered_map<TransitionSet, StateId>, std::unordered_map<Coord, TransitionSet>>
createMovementStates(StateMachine &dag, const std::unordered_map<std::string, std::vector<Coord>> &transitionToEligibleCoords)
{
  // Maps coordinates to their eligible transitions
  std::unordered_map<Coord, TransitionSet> coordToEligibleTransitions;

  // Process each transition and its eligible coordinates
  for(const auto &[transitionName, coords] : transitionToEligibleCoords)
    {
      for(const auto &coord : coords)
        {
          coordToEligibleTransitions[coord].transitions.insert(transitionName);
        }
    }

  // Create unique states for each set of transitions
  std::unordered_map<TransitionSet, StateId> eligibleTransitionsToState;

  // Create new states for each unique set of transitions
  for(const auto &[coord, transitionSet] : coordToEligibleTransitions)
    {
      if(eligibleTransitionsToState.find(transitionSet) == eligibleTransitionsToState.end())
        {
          StateId newState = dag.getNextStateId();
          dag.addNewState(newState);
          eligibleTransitionsToState[transitionSet] = newState;
        }
    }

  return {eligibleTransitionsToState, coordToEligibleTransitions};
}

std::unordered_map<std::string, std::vector<std::pair<std::string, StateId>>>
getPostTransitionsOfPriorityTransitions(StateMachine &dag, const std::unordered_map<std::string, std::shared_ptr<Actoid>> &transitionNameToAction,
                                        const std::unordered_map<AbilityType, PriorityActionInfo> &prioActionDict)
{
  std::unordered_map<std::string, std::vector<std::pair<std::string, StateId>>> postPriorityTransitions;

  for(const auto &transition : dag.getAllTransitions())
    {
      if(transition == "None_0")
        {
          break;
        }

      auto actionIt = transitionNameToAction.find(transition);
      if(actionIt != transitionNameToAction.end() && prioActionDict.find(actionIt->second->getFactory().getAbilityType()) != prioActionDict.end())
        {
          std::vector<std::pair<std::string, StateId>> postTransitions;

          if(dag.triggerTransition(transition))
            {
              try
                {
                  auto forwardTransitions = dag.getForwardTransitions(dag.getCurrentState());
                  for(const auto &ft : forwardTransitions)
                    {
                      auto ftActionIt = transitionNameToAction.find(ft.first);
                      if(ftActionIt != transitionNameToAction.end() && !(static_cast<uint32_t>(ftActionIt->second->getFlags()) & static_cast<uint32_t>(ActoidFlags::IS_PRIORITY)))
                        {
                          postTransitions.push_back(ft);
                        }
                    }
                }
              catch(const std::exception &)
                {
                  // Handle case when target state is nop
                }
              dag.reset();
            }
          postPriorityTransitions[transition] = postTransitions;
        }
    }
  return postPriorityTransitions;
}

// Helper function to get post-transitions of all priority transitions
std::pair<std::unordered_map<std::string, std::vector<std::pair<std::string, StateId>>>,
          std::unordered_map<std::string, std::vector<std::pair<std::string, StateId>>>>
getPostTransitionsOfAllPriorityTransitions(
    StateMachine& protoDag,
    const std::unordered_map<std::string, std::shared_ptr<Actoid>>& transitionNameToAction)
{
    auto postPriorityActionTransitions = 
        getPostTransitionsOfPriorityTransitions(protoDag, transitionNameToAction, PRIORITY_ACTIONS);
    auto postPriorityBonusActionTransitions = 
        getPostTransitionsOfPriorityTransitions(protoDag, transitionNameToAction, PRIORITY_BONUS_ACTIONS);
    
    // Remove original transitions
    for (const auto& [priorityTransition, _] : postPriorityActionTransitions) {
        for (const auto& state : protoDag.getAllStates()) {
            protoDag.removeTransition(priorityTransition, state);
        }
    }
    
    for (const auto& [priorityTransition, _] : postPriorityBonusActionTransitions) {
        for (const auto& state : protoDag.getAllStates()) {
            protoDag.removeTransition(priorityTransition, state);
        }
    }
    
    return {postPriorityActionTransitions, postPriorityBonusActionTransitions};
}

// Helper function to get post misty step transitions
std::vector<std::pair<std::string, StateId>>
getPostMistyStepTransitions(
    StateMachine& dag,
    const std::unordered_map<std::string, std::shared_ptr<Actoid>>& transitionNameToAction)
{
    std::vector<std::pair<std::string, StateId>> msPostTransitions;
    
    dag.triggerTransition("Misty Step to 0, 0_1");  // It's the only MS we created
    try {
        auto forwardTransitions = dag.getForwardTransitions(dag.getCurrentState());
        for (const auto& ft : forwardTransitions) {
            auto actionIt = transitionNameToAction.find(ft.first);
            if (actionIt != transitionNameToAction.end() && 
                !(static_cast<uint32_t>(actionIt->second->getFlags()) & static_cast<uint32_t>(ActoidFlags::IS_PRIORITY))) {
                msPostTransitions.push_back(ft);
            }
        }
    } catch (const std::exception&) {
        // Handle case when target state is nop
    }
    
    dag.reset();
    dag.removeTransition("Misty Step to 0, 0_1", 0);
    return msPostTransitions;
}

// Helper function to create movement states
std::pair<std::unordered_map<TransitionSet, StateId>, 
          std::unordered_map<Coord, TransitionSet>>
createMovementStates(
    StateMachine& dag,
    const std::unordered_map<std::string, std::vector<Coord>>& transitionToEligibleCoords) 
{
    std::unordered_map<Coord, TransitionSet> coordToEligibleTransitions;
    
    for (const auto& [transitionName, coords] : transitionToEligibleCoords) {
        for (const auto& coord : coords) {
            coordToEligibleTransitions[coord].transitions.insert(transitionName);
        }
    }
    
    std::unordered_map<TransitionSet, StateId> eligibleTransitionsToState;
    
    for (const auto& [coord, transitionSet] : coordToEligibleTransitions) {
        if (eligibleTransitionsToState.find(transitionSet) == eligibleTransitionsToState.end()) {
            StateId newState = dag.getNextStateId();
            dag.addNewState(newState);
            eligibleTransitionsToState[transitionSet] = newState;
        }
    }
    
    return {eligibleTransitionsToState, coordToEligibleTransitions};
}

// Helper function to build misty step transitions
void buildMistyStepTransitions(
    StateMachine& dag,
    const std::vector<std::pair<std::string, StateId>>& msPostTransitions,
    const std::unordered_map<std::string, std::vector<Coord>>& transitionToEligibleCoords,
    std::unordered_map<std::string, std::pair<Coord, MovementThreatType>>& movementTransToCoordAndType)
{
    auto [eligibleTransitionsToState, coordToEligibleTransitions] = 
        createMovementStates(dag, transitionToEligibleCoords);
    
    for (const auto& mspt : msPostTransitions) {
        try {
            auto coordsIt = transitionToEligibleCoords.find(mspt.first);
            if (coordsIt != transitionToEligibleCoords.end()) {
                for (const auto& coord : coordsIt->second) {
                    auto transSetIt = coordToEligibleTransitions.find(coord);
                    if (transSetIt != coordToEligibleTransitions.end()) {
                        auto stateIt = eligibleTransitionsToState.find(transSetIt->second);
                        if (stateIt != eligibleTransitionsToState.end()) {
                            StateId postMsState = stateIt->second;
                            std::string movementTransitionName = "ms_" + std::to_string(coord[0]) + 
                                                               "_" + std::to_string(coord[1]);
                            
                            movementTransToCoordAndType[movementTransitionName] = 
                                {coord, MovementThreatType::MISTY_STEPPED};
                            
                            dag.addTransition(movementTransitionName, 0, postMsState);
                            dag.addTransition(mspt.first, postMsState, mspt.second);
                        }
                    }
                }
            }
        } catch (const std::exception&) {
            // Handle case when out of range
        }
    }
}

// Helper function to build priority transitions
void buildPriorityTransitions(
    StateMachine& dag,
    const std::unordered_map<std::string, std::vector<std::pair<std::string, StateId>>>& postPriorityTransitions,
    const std::unordered_map<std::string, std::vector<Coord>>& transitionToEligibleCoords,
    std::unordered_map<std::string, std::pair<Coord, MovementThreatType>>& movementTransToCoordAndType,
    const std::unordered_map<std::string, std::shared_ptr<Actoid>>& transitionNameToAction,
    const std::unordered_map<AbilityType, PriorityActionInfo>& prioActionDict)
{
    auto [eligibleTransitionsToState, coordToEligibleTransitions] = 
        createMovementStates(dag, transitionToEligibleCoords);
    
    std::vector<StateId> newlyAddedStates;
    
    for (const auto& [transition, postTransitions] : postPriorityTransitions) {
        if (postTransitions.empty()) {
            dag.addTransition(transition, 0, -1);  // -1 represents "nop" state
            continue;
        }
        
        auto actionIt = transitionNameToAction.find(transition);
        if (actionIt == transitionNameToAction.end()) continue;
        
        std::string actionType = transition.substr(0, transition.find(' '));
        StateId newPrioState = dag.getNextStateId();
        
        auto prioActionIt = prioActionDict.find(actionIt->second->getFactory().getAbilityType());
        if (prioActionIt == prioActionDict.end()) continue;
        
        const auto& [prefix, threatType] = prioActionIt->second;
        
        dag.addNewState(newPrioState);
        newlyAddedStates.push_back(newPrioState);
        dag.addTransition(transition, 0, newPrioState);
        
        for (const auto& postTransition : postTransitions) {
            try {
                auto coordsIt = transitionToEligibleCoords.find(postTransition.first);
                if (coordsIt != transitionToEligibleCoords.end()) {
                    for (const auto& coord : coordsIt->second) {
                        auto transSetIt = coordToEligibleTransitions.find(coord);
                        if (transSetIt != coordToEligibleTransitions.end()) {
                            auto stateIt = eligibleTransitionsToState.find(transSetIt->second);
                            if (stateIt != eligibleTransitionsToState.end()) {
                                StateId postPtState = stateIt->second;
                                std::string movementTransitionName = prefix + std::to_string(coord[0]) + 
                                                                   "_" + std::to_string(coord[1]);
                                
                                movementTransToCoordAndType[movementTransitionName] = {coord, threatType};
                                
                                dag.addTransition(movementTransitionName, newPrioState, postPtState);
                                dag.addTransition(postTransition.first, postPtState, postTransition.second);
                            }
                        }
                    }
                }
            } catch (const std::exception&) {
                // Handle case when not available for secondary plan
            }
        }
    }
    
    // Connect unconnected states to nop
    for (StateId newState : newlyAddedStates) {
        if (dag.getForwardTransitions(newState).empty()) {
            dag.addTransition("dummy", newState, -1);  // -1 represents "nop" state
        }
    }
}

std::optional<DagBuildResult> buildActionDag(
    Combatant* combatant,
    const std::unique_ptr<StateMachine>& protoDag,
    const std::unordered_map<std::string, std::shared_ptr<Actoid>>& transitionNameToAction,
    const blaze::DynamicVector<int>& distances,
    const blaze::DynamicMatrix<Coord>& shortestPaths)
{
    // Create a working copy of the proto DAG
    StateMachine dag = *protoDag;
    
    // Get post-transitions for priority actions
    auto [postPriorityActionTransitions, postPriorityBonusActionTransitions] = 
        getPostTransitionsOfAllPriorityTransitions(dag, transitionNameToAction);
    
    // Get post-transitions for Misty Step
    auto msPostTransitions = getPostMistyStepTransitions(dag, transitionNameToAction);
    
    // Create mappings for movement transitions
    std::unordered_map<std::string, std::vector<Coord>> transitionToEligibleCoords;
    std::unordered_map<std::string, std::pair<Coord, MovementThreatType>> movementTransToCoordAndType;
    
    // TODO: Populate transitionToEligibleCoords based on distances and shortestPaths
    
    // Build different types of transitions
    buildMistyStepTransitions(dag, msPostTransitions, transitionToEligibleCoords, movementTransToCoordAndType);
    buildPriorityTransitions(dag, postPriorityActionTransitions, transitionToEligibleCoords, 
                            movementTransToCoordAndType, transitionNameToAction, PRIORITY_ACTIONS);
    buildPriorityTransitions(dag, postPriorityBonusActionTransitions, transitionToEligibleCoords, 
                            movementTransToCoordAndType, transitionNameToAction, PRIORITY_BONUS_ACTIONS);
    
    return DagBuildResult{std::make_unique<StateMachine>(std::move(dag)), std::move(movementTransToCoordAndType)};
}

// PostTransitions getPostTransitionsOfPriorityTransitions(
//     const std::unique_ptr<StateMachine>& dag,
//     const std::unordered_map<std::string, std::shared_ptr<Actoid>>& transitionNameToAction,
//     const std::unordered_map<ActionType, PriorityAction>& prioActionDict)
// {
//     PostTransitions postPriorityTransitions;

//     // Get available transitions
//     auto availableTransitions = dag->getAvailableTransitions();
    
//     // Early exit if only None_0 transition exists
//     if (!availableTransitions.empty() && availableTransitions[0] == "None_0") {
//         return postPriorityTransitions;
//     }

//     // Process each transition
//     for (const auto& transition : availableTransitions) {
//         try {
//             const auto& action = transitionNameToAction.at(transition);
            
//             // Check if action is a priority action
//             if (prioActionDict.find(action->getFactory().getActionType()) != prioActionDict.end()) {
//                 std::vector<std::pair<std::string, StateId>> postTransitions;
                
//                 // Create temporary DAG copy for transition testing
//                 auto tempDag = std::make_unique<StateMachine>(*dag);
                
//                 if (tempDag->triggerTransition(transition)) {
//                     // Get forward transitions from current state
//                     auto currentState = tempDag->getCurrentState();
//                     auto forwardTransitions = tempDag->getForwardTransitions(currentState);
                    
//                     // Filter out priority transitions
//                     for (const auto& ft : forwardTransitions) {
//                         try {
//                             const auto& ftAction = transitionNameToAction.at(ft.first);
//                             if (!ftAction->hasFlag(ActoidFlags::IS_PRIORITY)) {
//                                 postTransitions.push_back(ft);
//                             }
//                         } catch (const std::out_of_range&) {
//                             continue;
//                         }
//                     }
//                 }
                
//                 postPriorityTransitions[transition] = std::move(postTransitions);
//             }
//         } catch (const std::out_of_range&) {
//             continue;
//         }
//     }

//     return postPriorityTransitions;
// }

// PriorityTransitionsResult getPostTransitionsOfAllPriorityTransitions(
//     const std::unique_ptr<StateMachine>& protoDag,
//     const std::unordered_map<std::string, std::shared_ptr<Actoid>>& transitionNameToAction)
// {
//     // Get transitions for regular priority actions and bonus actions
//     auto postPriorityActionTransitions = getPostTransitionsOfPriorityTransitions(
//         protoDag, 
//         transitionNameToAction, 
//         PRIORITY_ACTIONS
//     );

//     auto postPriorityBonusActionTransitions = getPostTransitionsOfPriorityTransitions(
//         protoDag, 
//         transitionNameToAction, 
//         PRIORITY_BONUS_ACTIONS
//     );

//     // Remove original transitions for priority actions
//     for (const auto& [priorityTransition, _] : postPriorityActionTransitions) {
//         for (const auto& state : protoDag->getStates()) {
//             protoDag->removeTransition(priorityTransition, state.first);
//         }
//     }

//     // Remove original transitions for priority bonus actions
//     for (const auto& [priorityTransition, _] : postPriorityBonusActionTransitions) {
//         for (const auto& state : protoDag->getStates()) {
//             protoDag->removeTransition(priorityTransition, state.first);
//         }
//     }

//     return PriorityTransitionsResult{
//         std::move(postPriorityActionTransitions),
//         std::move(postPriorityBonusActionTransitions)
//     };
// }

// std::optional<DagBuildResult> buildActionDag(Combatant *combatant, 
//                                            const std::unique_ptr<StateMachine> &protoDag,
//                                            const std::unordered_map<std::string, std::shared_ptr<Actoid>> &transitionNameToAction,
//                                            const blaze::DynamicVector<int> &distances, 
//                                            const blaze::DynamicMatrix<Coord> &shortestPaths)
// {
//     auto &battleMap = BattleMap::getInstance();
//     battleMap.calcVisibilityDictForAllCoords(combatant, shortestPaths);

//     // Clear calculation caches
//     // for (const auto& [_, action] : transitionNameToAction) {
//     //     action->clearCache();
//     // }

//     auto protoTransitions = protoDag->getAllTransitions();
    
//     // Get post-transitions mappings
//     auto [postPriorityActionTransitions, postPriorityBonusActionTransitions] = 
//         getPostTransitionsOfAllPriorityTransitions(protoDag, transitionNameToAction);

//     // Handle Post Misty Step transitions
//     std::optional<std::vector<std::pair<std::string, StateId>>> postMistyStepTransitions;
//     TransitionToEligibleCoords msTransitionToEligibleCoords;
    
//     if (std::find(protoTransitions.begin(), protoTransitions.end(), "Misty Step to 0, 0_1") != protoTransitions.end()) {
//         postMistyStepTransitions = getPostMistyStepTransitions(protoDag, transitionNameToAction);
//         if (postMistyStepTransitions) {
//             for (const auto& [transName, _] : *postMistyStepTransitions) {
//                 auto coords = transitionNameToAction.at(transName)->getEligibleCoords(distances, shortestPaths);
//                 if (coords) {
//                     msTransitionToEligibleCoords[transName] = std::move(*coords);
//                 }
//             }
//         }
//     }

//     auto dag = std::make_unique<StateMachine>(*protoDag);

//     // Process priority action transitions
//     TransitionToEligibleCoords priorityActionCoords;
//     TransitionToEligibleCoords priorityBonusActionCoords;

//     processPostPriorityTransitions(postPriorityActionTransitions, transitionNameToAction, 
//                                  distances, shortestPaths, priorityActionCoords);
//     processPostPriorityTransitions(postPriorityBonusActionTransitions, transitionNameToAction,
//                                  distances, shortestPaths, priorityBonusActionCoords);

//     // Create main transition to eligible coords mapping
//     TransitionToEligibleCoords transitionToEligibleCoords;
//     processMainTransitions(protoTransitions, transitionNameToAction, distances, 
//                          shortestPaths, transitionToEligibleCoords);

//     // Remove transitions without eligible coords
//     removeInvalidTransitions(dag.get(), protoTransitions, transitionToEligibleCoords);

//     MovementTransitionMap movementTransitionToCoordAndType;
//     buildMovementTransitions(dag.get(), protoDag.get(), transitionToEligibleCoords,
//                            movementTransitionToCoordAndType);

//     // Handle special transitions
//     if (postMistyStepTransitions) {
//         buildMistyStepTransitions(*dag, *postMistyStepTransitions, 
//                                 msTransitionToEligibleCoords, 
//                                 movementTransitionToCoordAndType);
//     }

//     buildPriorityTransitions(*dag, postPriorityActionTransitions, priorityActionCoords,
//                            movementTransitionToCoordAndType, transitionNameToAction, 
//                            PRIORITY_ACTIONS);
//     buildPriorityTransitions(*dag, postPriorityBonusActionTransitions, priorityBonusActionCoords,
//                            movementTransitionToCoordAndType, transitionNameToAction,
//                            PRIORITY_BONUS_ACTIONS);

//     if (!dag->getAllTransitions().empty() && dag->getAllTransitions()[0] != "None_0") {
//         return DagBuildResult{
//             std::move(dag),
//             std::move(movementTransitionToCoordAndType),
//             std::move(transitionToEligibleCoords)
//         };
//     }

//     return std::nullopt;
// }

std::optional<BestSequenceResult>
findBestSequence(Combatant *combatant, const StateMachine &dag, const std::unordered_map<std::string, std::shared_ptr<Actoid>> &transitionNameToAction,
                 const TransitionToEligibleCoords &transitionToEligibleCoords, const MovementTransitionMap &movementTransitionToCoordAndType,
                 const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths, double infeasibilityMultiplier)
{
  auto &battleMap = BattleMap::getInstance();
  auto &effectTracker = EffectTracker::getInstance();
  std::unordered_map<AoeEffect *,CoordVector> effectToCoords;
  for(const auto &effect : effectTracker.getAoeEffects())
    {
      effectToCoords[effect.get()] = effect->getAffectedCoords();
    }

    TransitionToMsPath transitionNameToMsPath;
    SequenceToThreat sequenceToThreat;
    TransitionStepThreat sequenceIdxToTransitionStepThreat;
    
    Coords currentCoords = battleMap.getCombatantCoordinates(*combatant);
    
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
    // ThreatUtils::clearAccumulateThreatCache();
    // ThreatUtils::clearAoeAndAooThreatCache();

    // Calculate movement threats
    for (const auto& [coordAndType, ids] : coordToSequenceIds) {
        if(coordAndType.first.empty())
          {
            continue;
          }

        const auto& [coord, movementType] = coordAndType;
        auto path = battleMap.getPathToCoord(*combatant, coord, distances, shortestPaths, true);
        if(!path.has_value())
          {
            continue;
          }

        std::vector<double> movementThreat;
        std::vector<std::string> mistyStepPath;
        switch (movementType) {
            case MovementThreatType::STANDARD:
                movementThreat = accumulateThreatAlongPath(path.value(), combatant, effectToCoords);
                break;

            case MovementThreatType::DISENGAGED:
                movementThreat = accumulateThreatAlongPath(path.value(), combatant, effectToCoords, true);
                break;

            case MovementThreatType::DODGED:
                movementThreat = accumulateThreatAlongPath(path.value(), combatant, effectToCoords, false, true);
                break;

            case MovementThreatType::MISTY_STEPPED: {
                auto [threat, msPath] = calcThreatForPathWithMistyStep(path.value(), combatant, effectToCoords);
                movementThreat = threat;
                mistyStepPath = msPath;
                std::string msKey = "ms_" + std::to_string(coord[0]) + "," + std::to_string(coord[1]);
                transitionNameToMsPath[msKey] = msPath;
                break;
            }

            default:
                std::cerr << "Unknown movement type " << static_cast<int>(movementType) << '\n';
                movementThreat = accumulateThreatAlongPath(path.value(), combatant, effectToCoords);
        }

        for (size_t idx : ids) {
            sequenceToThreat[idx] = {std::move(movementThreat), 0.0};
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

                            for (const auto& existingEffect : effectTracker.getAffectingCombatant(combatant)) {
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
        return GetUpFactory(combatant).create(nullptr);
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