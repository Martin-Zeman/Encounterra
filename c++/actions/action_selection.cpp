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

    // Streaming de-duplicator for DFS sequences. The dedup key is the SET of simplified-transition indices for a
    // sequence (movement coords and actions alike; movement coord names like "(x, y)" keep their own simplified
    // index). We encode that set as a fixed-size bitset (array<uint64_t, N>): bits are inherently sorted and
    // unique, so dedup needs no per-sequence heap allocation, no sort, and no unique pass — just a hash-set probe.
    // This is exactly equivalent to the previous frozenset-of-simplified-indices key but allocation-free.
    //
    // The escape hatch is preserved verbatim: a sequence whose footprint was already seen is still kept if it
    // contains an IS_ATTACK_MODIFIER actoid (threat is order-dependent once a modifier is present, so distinct
    // orderings must survive). Sequences are emitted in DFS order, identical to the previous batch pruner.
    //
    // PRUNER_MAX_WORDS * 64 bounds the simplified-index space handled by the fast path; anything larger falls back
    // to a sorted-vector footprint (same semantics, just slower) so correctness holds for arbitrarily large maps.
    constexpr int PRUNER_MAX_WORDS = 8; // up to 512 distinct simplified indices on the fast path

    class SequencePruner {
    public:
      SequencePruner(const std::vector<enc::Actoid *> &indexToActoid,
                     const std::vector<int> &transitionToSimplified, size_t reserveHint = 0)
          : _indexToActoid(indexToActoid), _transitionToSimplified(transitionToSimplified),
            _numTransitions(static_cast<int>(transitionToSimplified.size()))
      {
        int maxSimp = -1;
        for(int s : transitionToSimplified)
          {
            maxSimp = std::max(maxSimp, s);
          }
        _numWords = (maxSimp >= 0) ? (maxSimp / 64 + 1) : 1;
        _useBitset = (_numWords <= PRUNER_MAX_WORDS);
        if(reserveHint)
          {
            if(_useBitset)
              _bitsetSets.reserve(reserveHint);
            else
              _vecSets.reserve(reserveHint);
            _pruned.reserve(reserveHint);
          }
      }

      // Consider one DFS sequence; keeps it (moving or copying depending on the argument's value category) iff its
      // footprint is new or it carries an attack modifier.
      template <class Seq>
      void consider(Seq &&sequence)
      {
        if(keep(sequence))
          {
            _pruned.push_back(std::forward<Seq>(sequence));
          }
      }

      std::vector<std::vector<int>> take() { return std::move(_pruned); }

    private:
      using Key = std::array<uint64_t, PRUNER_MAX_WORDS>;

      struct KeyHash {
        size_t operator()(const Key &k) const
        {
          size_t h = 1469598103934665603ULL; // FNV-1a
          for(uint64_t w : k)
            {
              h ^= w;
              h *= 1099511628211ULL;
            }
          return h;
        }
      };

      struct VecHash {
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

      bool hasAttackModifier(const std::vector<int> &sequence) const
      {
        for(int tx : sequence)
          {
            if(tx >= 0 && tx < static_cast<int>(_indexToActoid.size()))
              {
                enc::Actoid *a = _indexToActoid[tx];
                if(a && a->hasFlag(enc::ActoidFlags::IS_ATTACK_MODIFIER))
                  {
                    return true;
                  }
              }
          }
        return false;
      }

      bool keep(const std::vector<int> &sequence)
      {
        if(_useBitset)
          {
            Key footprint{};
            for(int txIdx : sequence)
              {
                if(txIdx >= 0 && txIdx < _numTransitions)
                  {
                    int s = _transitionToSimplified[txIdx];
                    footprint[s >> 6] |= (uint64_t{1} << (s & 63));
                  }
              }
            return _bitsetSets.insert(footprint).second || hasAttackModifier(sequence);
          }

        _vecFootprint.clear();
        for(int txIdx : sequence)
          {
            if(txIdx >= 0 && txIdx < _numTransitions)
              {
                _vecFootprint.push_back(_transitionToSimplified[txIdx]);
              }
          }
        std::sort(_vecFootprint.begin(), _vecFootprint.end());
        _vecFootprint.erase(std::unique(_vecFootprint.begin(), _vecFootprint.end()), _vecFootprint.end());
        return _vecSets.insert(_vecFootprint).second || hasAttackModifier(sequence);
      }

      const std::vector<enc::Actoid *> &_indexToActoid;
      const std::vector<int> &_transitionToSimplified;
      int _numTransitions;
      int _numWords = 1;
      bool _useBitset = true;
      std::unordered_set<Key, KeyHash> _bitsetSets;
      std::unordered_set<std::vector<int>, VecHash> _vecSets;
      std::vector<int> _vecFootprint;
      std::vector<std::vector<int>> _pruned;
    };
}

std::vector<std::vector<int>> pruneSequences(std::vector<std::vector<int>> sequences,
                                             const std::vector<Actoid *> &indexToActoid,
                                             const std::vector<int> &transitionToSimplified)
{
  // Batch wrapper around the streaming SequencePruner: dedup by the set of simplified-transition indices,
  // preserving the attack-modifier escape hatch and DFS emission order. See SequencePruner for details.
  SequencePruner pruner(indexToActoid, transitionToSimplified, sequences.size());
  for(auto &sequence : sequences)
    {
      pruner.consider(std::move(sequence));
    }
  return pruner.take();
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

    // Deduplicate during the DFS itself: each complete path is handed to the pruner as it is discovered, so the
    // (potentially tens of millions of) raw sequences are never all materialized at once — only the survivors are
    // retained. Semantically identical to dfs() followed by pruneSequences(); see SequencePruner.
    SequencePruner pruner(indexToActoid, transitionToSimplified);
    dag.dfs(0, maxSequenceLength, [&pruner](const std::vector<int> &path) { pruner.consider(path); });
    auto prunedSequences = pruner.take();

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
