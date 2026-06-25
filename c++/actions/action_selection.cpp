#include "actions/action_selection.hpp"
#include "actions/movement.hpp"
#include "actions/dummy_actoid.hpp"
#include "actions/break_grapple.hpp"
#include "core/battle_map.hpp"
#include "core/geometry.hpp"
#include "effects/effect_tracker.hpp"
// #include "combat/actions/movement.hpp"
#include <regex>
#include <numeric>
#include <limits>
#include <algorithm>
#include <cstdint>
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
    // Serialization of a Misty Step movement path (produced by calcThreatForPathWithMistyStep), e.g. "ms_(3, 4)".
    const std::regex REGEX_MS_MOVEMENT_PATTERN(R"([mschdio_]+\((\d+), (\d+)\))");
}

std::vector<std::vector<int>> pruneSequences(std::vector<std::vector<int>> sequences,
                                             const std::vector<Actoid *> &indexToActoid,
                                             const std::vector<int> &transitionToSimplified)
{
  // Dedup key is the set of simplified-transition indices (drops trailing level designators). When the
  // simplified-index space fits in 64 entries (the overwhelmingly common case for a single combatant's
  // turn DAG) we encode each footprint as a uint64_t bitmask: dedup then needs no per-sequence vector
  // allocation, no sort/unique, no memcmp on keys — just an unordered_set<uint64_t>. We fall back to a
  // sorted+uniqued std::vector<int> footprint only when an index >= 64 is present.
  // transitionToSimplified and indexToActoid are dense vectors indexed by transition index (O(1) lookup).
  const int numTransitions = static_cast<int>(transitionToSimplified.size());
  int maxSimp = -1;
  for(int s : transitionToSimplified)
    {
      maxSimp = std::max(maxSimp, s);
    }

  auto hasAttackModifier = [&](const std::vector<int> &sequence) {
    for(int tx : sequence)
      {
        if(tx >= 0 && tx < static_cast<int>(indexToActoid.size()))
          {
            Actoid *a = indexToActoid[tx];
            if(a && a->hasFlag(ActoidFlags::IS_ATTACK_MODIFIER))
              {
                return true;
              }
          }
      }
    return false;
  };

  std::vector<std::vector<int>> prunedSequences;
  prunedSequences.reserve(sequences.size());

  if(maxSimp < 64)
    {
      std::unordered_set<uint64_t> sequenceSets;
      sequenceSets.reserve(sequences.size() * 2);
      for(auto &sequence : sequences)
        {
          uint64_t footprint = 0;
          for(int txIdx : sequence)
            {
              if(txIdx >= 0 && txIdx < numTransitions)
                {
                  footprint |= (uint64_t{1} << transitionToSimplified[txIdx]);
                }
            }

          if(sequenceSets.insert(footprint).second || hasAttackModifier(sequence))
            {
              prunedSequences.push_back(std::move(sequence));
            }
        }
      return prunedSequences;
    }

  // Fallback: simplified-index space exceeds 64; use a sorted+uniqued vector footprint.
  struct VectorHash {
    size_t operator()(const std::vector<int> &v) const
    {
      size_t h = v.size();
      for(int x : v)
        {
          h ^= std::hash<int>{}(x) + 0x9e3779b97f4a7c15ULL + (h << 6) + (h >> 2);
        }
      return h;
    }
  };

  std::unordered_set<std::vector<int>, VectorHash> sequenceSets;
  sequenceSets.reserve(sequences.size());

  std::vector<int> footprint;
  for(auto &sequence : sequences)
    {
      footprint.clear();
      for(int txIdx : sequence)
        {
          if(txIdx >= 0 && txIdx < numTransitions)
            {
              footprint.push_back(transitionToSimplified[txIdx]);
            }
        }
      std::sort(footprint.begin(), footprint.end());
      footprint.erase(std::unique(footprint.begin(), footprint.end()), footprint.end());

      if(sequenceSets.insert(footprint).second || hasAttackModifier(sequence))
        {
          prunedSequences.push_back(std::move(sequence));
        }
    }
  return prunedSequences;
}

CoordToSequenceIds createCoordToSequenceMapping(
    const std::vector<std::vector<Actoid *>>& sequences,
    const MovementTransitionMap& movementTransitionToCoordAndType
) {
    CoordToSequenceIds coordToSequenceIds;
    
    for (size_t idx = 0; idx < sequences.size(); ++idx) {
        std::optional<std::pair<Coord, MovementThreatType>> coord;
        
        for (Actoid* action : sequences[idx]) {
            auto it = movementTransitionToCoordAndType.find(action);
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

double getDistToActionSequenceCoord(const std::vector<Actoid *> &sequence, const blaze::DynamicVector<int> &distances)
{
  auto &battleMap = BattleMap::getInstance();
  for(Actoid *action : sequence)
    {
      if(!action)
        {
          continue;
        }
      if(auto *movement = dynamic_cast<MovementIncrement *>(action))
        {
          const Coord &coord = movement->getIncrement();
          return distances[coord[0] * battleMap.getGridSize() + coord[1]];
        }
    }
  return 0.0;
}

std::pair<std::vector<Actoid *>, std::pair<std::vector<double>, double>>
getNearestAndMinimize(std::vector<std::vector<Actoid *>> &sequences, const std::vector<size_t> &sortedSequences,
                      const SequenceToThreat &sequenceToThreat, const blaze::DynamicVector<int> &distances,
                      const TransitionStepThreat &sequenceIdxToTransitionStepThreat)
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
        std::vector<Actoid *> newSequence;

        auto outerIt = sequenceIdxToTransitionStepThreat.find(idx);
        for (size_t tIdx = 0; tIdx < sequence.size(); ++tIdx) {
            bool shouldKeep = false;
            bool hasStepThreat = false;
            double stepThreat = 0.0;
            if (outerIt != sequenceIdxToTransitionStepThreat.end()) {
                auto innerIt = outerIt->second.find(tIdx);
                if (innerIt != outerIt->second.end()) {
                    hasStepThreat = true;
                    stepThreat = innerIt->second;
                }
            }

            if (!hasStepThreat) {
                // Movement / dummy transitions are never scored; Python keeps these via a KeyError -> append.
                shouldKeep = true;
            } else if (stepThreat > 0) {
                shouldKeep = true;
            } else if (sequence[tIdx] && sequence[tIdx]->hasFlag(ActoidFlags::IS_PRIORITY)) {
                shouldKeep = true;
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
                           const ActoidOwnershipPool &actoidPool,
                           const MovementTransitionMap &movementTransitionToCoordAndType, const std::vector<Actoid *> &sequence,
                           const TransitionToMsPath &transitionNameToMsPath)
{
  std::vector<std::shared_ptr<Actoid>> actions;
  auto &battleMap = BattleMap::getInstance();

  // The ownership pool is already keyed by actoid identity (Actoid* -> shared_ptr), so it doubles as the reverse
  // lookup used to recover the owning shared_ptr for each proto / non-movement action in the chosen sequence.
  const std::unordered_map<Actoid *, std::shared_ptr<Actoid>> &actoidToShared = actoidPool;

  for(Actoid *action : sequence)
    {
      if(!action || dynamic_cast<DummyActoid *>(action))
        {
          continue;
        }

      auto sharedIt = actoidToShared.find(action);
      if(sharedIt != actoidToShared.end())
        {
          actions.push_back(sharedIt->second);
          continue;
        }

      auto movementIt = movementTransitionToCoordAndType.find(action);
      if(movementIt == movementTransitionToCoordAndType.end())
        {
          std::cerr << "Unknown transition type: " << action->toString() << '\n';
          continue;
        }

      const auto &[coord, movementType] = movementIt->second;
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
            decodeMsPathToActions(combatant, battleMap.getCombatantCoordinates(*combatant).getRoot(), transitionNameToMsPath.at(action), actions,
                                  msFactory);
            break;
          }
        default: std::cerr << "Unknown movement type: " << static_cast<int>(movementType) << '\n';
        }
    }

  return actions;
}


std::optional<BestSequenceResult>
findBestSequence(Combatant *combatant, const StateMachine &dag,
                 const ActoidOwnershipPool &actoidPool,
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

    // The ownership pool is already keyed by actoid identity (Actoid* -> shared_ptr); reuse it directly as the reverse
    // lookup needed for wildshape handling below.
    const std::unordered_map<Actoid *, std::shared_ptr<Actoid>> &actoidToShared = actoidPool;

    // Remove a Misty Step transition that targets the current coordinate (a no-op move) if it exists.
    {
      Coord rootCoord = currentCoords.getRoot();
      auto &mutableMovementMap = const_cast<MovementTransitionMap &>(movementTransitionToCoordAndType);
      for(auto it = mutableMovementMap.begin(); it != mutableMovementMap.end();)
        {
          if(it->second.second == MovementThreatType::MISTY_STEPPED && it->second.first == rootCoord)
            {
              it = mutableMovementMap.erase(it);
            }
          else
            {
              ++it;
            }
        }
    }

    // Reverse map (coord, type) -> movement actoid, used to key the Misty Step path map by actoid identity.
    std::unordered_map<std::pair<Coord, MovementThreatType>, Actoid *> coordAndTypeToActoid;
    for(const auto &[actoid, coordAndType] : movementTransitionToCoordAndType)
      {
        coordAndTypeToActoid[coordAndType] = actoid;
      }

    // Get all sequences
    auto [dagForward, numStates, indexToState, indexToTransition, transitionToSimplified, indexToActoid] = dag.getFlattenedDag();
    size_t maxSequenceLength = numStates * 2;
    
    auto allSequences = dag.dfs(0, maxSequenceLength);
    auto prunedSequences = pruneSequences(std::move(allSequences), indexToActoid, transitionToSimplified);

    std::vector<std::vector<Actoid *>> sequences;
    for (const auto& arr : prunedSequences) {
        std::vector<Actoid *> sequence;
        for (int item : arr) {
            Actoid *a = (item >= 0 && item < static_cast<int>(indexToActoid.size())) ? indexToActoid[item] : nullptr;
            sequence.push_back(a);
        }
        sequences.push_back(std::move(sequence));
    }

    auto coordToSequenceIds = createCoordToSequenceMapping(sequences, movementTransitionToCoordAndType);

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
                auto actoidIt = coordAndTypeToActoid.find(coordAndType);
                if(actoidIt != coordAndTypeToActoid.end())
                  {
                    transitionNameToMsPath[actoidIt->second] = msPath;
                  }
                break;
            }

            default:
                std::cerr << "Unknown movement type " << static_cast<int>(movementType) << '\n';
                movementThreat = accumulateThreatAlongPath(path.value(), combatant, effectToCoords);
        }

        for (size_t idx : ids) {
            sequenceToThreat[idx] = {movementThreat, 0.0};
        }
    }

    // Calculate action threats
    for (const auto& [coordAndType, ids] : coordToSequenceIds) {
        if (coordAndType.first.empty()) continue;
        
        const auto& [coord, _] = coordAndType;
        
        auto withPosition = [&](const std::function<void()>& fn) {
            battleMap.withCombatantPosition(combatant, coord, fn);
        };

        withPosition([&]() {
            for (size_t idx : ids) {
                // The movement loop skips sequences whose path to this coord is None,
                // leaving them out of sequenceToThreat. Such sequences are not viable
                // plans, so skip them here too (mirrors Python, which only overwrites
                // an existing sequence_to_threat entry). This also avoids creating an
                // entry with an empty movement-threat vector, which would later crash
                // getNearestAndMinimize's `.first.back()`.
                if (sequenceToThreat.find(idx) == sequenceToThreat.end()) continue;

                AttackThreatModifier *deltaAction = nullptr;
                double threatAcc = 0.0;
                bool firstFeasibilityCheckDone = false;
                double feasibilityMultiplier = 1.0;
                size_t deltaActionTIdx = 0;

                for (size_t tIdx = 0; tIdx < sequences[idx].size(); ++tIdx) {
                    Actoid* action = sequences[idx][tIdx];
                    if (!action || dynamic_cast<DummyActoid *>(action)) break;
                    if (dynamic_cast<MovementIncrement *>(action)) continue; // movement handled separately

                    auto sharedIt = actoidToShared.find(action);
                    std::shared_ptr<Actoid> actionShared = sharedIt != actoidToShared.end() ? sharedIt->second : std::shared_ptr<Actoid>(action, [](Actoid*) {});

                    battleMap.withWildshapeIfNeeded(actionShared, combatant, coord, [&]() {
                        if (!action->hasFlag(ActoidFlags::LOCATION_INDEPENDENT)) {
                            if (tIdx == 1) {
                                feasibilityMultiplier = distances[coord[0] * battleMap.getGridSize() + coord[1]] <= 
                                    combatant->getMovement() ? 1.0 : infeasibilityMultiplier;
                                firstFeasibilityCheckDone = true;
                            } else if (tIdx > 1) {
                                auto eligIt = transitionToEligibleCoords.find(action);
                                if (eligIt == transitionToEligibleCoords.end() || eligIt->second.empty()) return;
                                const auto& eligibleCoords = eligIt->second;

                                if (!firstFeasibilityCheckDone) {
                                    feasibilityMultiplier = (std::find(eligibleCoords.begin(), eligibleCoords.end(), coord) != 
                                        eligibleCoords.end() && distances[coord[0] * battleMap.getGridSize() + coord[1]] <= 
                                        combatant->getMovement()) ? 1.0 : infeasibilityMultiplier;
                                    firstFeasibilityCheckDone = true;
                                } else {
                                    auto remainingDist = getHopDistanceCoords(Coords(eligibleCoords), Coords(CoordVector{coord}));
                                    feasibilityMultiplier = remainingDist <= combatant->getMovement() - 
                                        distances[coord[0] * battleMap.getGridSize() + coord[1]] ? 1.0 : infeasibilityMultiplier;
                                }
                            }
                        }

                        // Mirrors Python action.calculate_threat(consider_dist=..., movement_threat=...).
                        Kwargs threatKwargs;
                        threatKwargs["considerDist"] = !battleMap.isWildshapeActive();
                        threatKwargs["movement_threat"] = sequenceToThreat[idx].first;
                        double threat = 0.0;
                        if (auto *threatIface = dynamic_cast<Threat *>(action)) {
                            threat = threatIface->calculateThreat(threatKwargs);
                        }
                        threatAcc += threat;

                        if (deltaAction) {
                            double deltaThreat = deltaAction->calculateThreatForAttack(combatant, action, {});
                            threatAcc += deltaThreat;
                            sequenceIdxToTransitionStepThreat[idx][deltaActionTIdx] += deltaThreat;
                        }

                        if (auto *attackMod = dynamic_cast<AttackThreatModifier *>(action)) {
                            deltaAction = attackMod;
                            deltaActionTIdx = tIdx;
                        }

                        for (const auto& existingEffect : effectTracker.getAffectingCombatant(combatant)) {
                            if (auto existingMod = std::dynamic_pointer_cast<AttackThreatModifier>(existingEffect)) {
                                threatAcc += existingMod->calculateThreatForAttack(combatant, action, {});
                            }
                        }

                        sequenceIdxToTransitionStepThreat[idx][tIdx] = threat;
                    });
                }

                auto& threat = sequenceToThreat[idx];
                threat.second = threatAcc * feasibilityMultiplier;
                // Small bias towards current position prevents oscillations
                if (!threat.first.empty()) {
                    threat.first.back() += (coord == currentCoords.getRoot()) ? 0.01 : 0.0;
                }
            }
        });
    }

    // Sort sequences by total threat. Only sequences that received a threat score are considered
    // (mirrors Python's `sorted(sequence_to_threat, ...)`, which iterates the dict's keys).
    std::vector<size_t> sortedSequences;
    sortedSequences.reserve(sequenceToThreat.size());
    for (const auto& [idx, _] : sequenceToThreat) {
        sortedSequences.push_back(idx);
    }

    auto sequenceScore = [&](size_t idx) {
        auto it = sequenceToThreat.find(idx);
        if (it == sequenceToThreat.end() || it->second.first.empty() || it->second.second <= 0) {
            return -std::numeric_limits<double>::infinity();
        }
        return it->second.first.back() + it->second.second;
    };

    std::sort(sortedSequences.begin(), sortedSequences.end(),
        [&](size_t a, size_t b) {
            return sequenceScore(a) > sequenceScore(b);
        });

    auto [nearestAndMinimizedSequence, maxThreat] = getNearestAndMinimize(
        sequences, sortedSequences, sequenceToThreat, distances,
        sequenceIdxToTransitionStepThreat);

    if (nearestAndMinimizedSequence.empty()) {
        return std::nullopt;
    }

    std::array<double, 2> maxThreatArr{
        maxThreat.first.empty() ? 0.0 : maxThreat.first.back(),
        maxThreat.second
    };

    return BestSequenceResult{
        std::move(nearestAndMinimizedSequence),
        std::move(transitionNameToMsPath),
        maxThreatArr
    };
}

// Main action selector function
std::shared_ptr<Actoid> getAction(Combatant* combatant) {
    auto& battleMap = BattleMap::getInstance();
    // battleMap.clearCaches();
    
    // Handle wildshape
    combatant = combatant->getCurrentForm();

    // Check if we need to break grapple
    if (auto grappleCond = combatant->needsToBreakOutOfGrapple()) {
        if (combatant->hasAction()) {
            return BreakGrappleFactory(*grappleCond).create();
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
