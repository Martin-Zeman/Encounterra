#include "actions/action_selection.hpp"
#include "actions/movement.hpp"
#include "actions/dummy_actoid.hpp"
#include "actions/break_grapple.hpp"
#include "abilities/on_hit_divine_smite.hpp"
#include "core/battle_map.hpp"
#include "core/geometry.hpp"
#include "effects/effect_tracker.hpp"
// #include "combat/actions/movement.hpp"
#include <regex>
#include <numeric>
#include <limits>
#include <algorithm>
#include <cstdint>
#include <cstdlib>
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

        // sequenceIdxToTransitionStepThreat[idx] is the flat-vector slot for this sequence. A sequence that
        // produced no step threats has an empty inner map here, which behaves identically to the old missing
        // outer key (find below simply returns end() for every tIdx).
        const auto& stepThreatMap = sequenceIdxToTransitionStepThreat[idx];
        for (size_t tIdx = 0; tIdx < sequence.size(); ++tIdx) {
            bool shouldKeep = false;
            bool hasStepThreat = false;
            double stepThreat = 0.0;
            auto innerIt = stepThreatMap.find(tIdx);
            if (innerIt != stepThreatMap.end()) {
                hasStepThreat = true;
                stepThreat = innerIt->second;
            }

            if (!hasStepThreat) {
                // Movement / dummy transitions are never scored; Python keeps these via a KeyError -> append.
                shouldKeep = true;
            } else if (stepThreat > 0) {
                shouldKeep = true;
            } else if (sequence[tIdx] && sequence[tIdx]->hasFlag(ActoidFlags::IS_PRIORITY)) {
                shouldKeep = true;
            } else if (sequence[tIdx] && sequence[tIdx]->hasFlag(ActoidFlags::IS_ACTION_ENABLER)) {
                // An action enabler (e.g. Action Surge) contributes no threat of its own — its value is the extra
                // attacks it unlocks. Dropping it here would leave those follow-up attacks in the emitted sequence
                // with no granted action, so they would be infeasible at execution. Always keep enablers.
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
  bool pendingDivineSmite = false;

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
          if(action->getAbilityType() == AbilityType::DIVINE_SMITE)
            {
              pendingDivineSmite = true;
            }
          else if(pendingDivineSmite)
            {
              if(auto *attack = dynamic_cast<Attack *>(action))
                {
                  if(attack->getAttackFactory().hasFlag(FactoryFlags::IS_MELEE))
                    {
                      actions.push_back(OnHitDivineSmite::createPendingSmiteMarker());
                      pendingDivineSmite = false;
                    }
                }
            }
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


namespace {
  // Hop (Chebyshev) distance from the eligible coord that is Euclidean-closest to `target`. This is an allocation-free
  // inlining of getHopDistanceCoords(Coords(eligible), Coords({target})) for the single-target case that dominates the
  // feasibility check in findBestSequence's scoring loop: the original builds two Coords objects and a
  // blaze::DynamicMatrix<double> (with sqrt/pow) on EVERY call, which perf attributed ~14% of total runtime to
  // distanceMatrix + Coords::operator() + getHopDistanceCoords. The argmin and returned value are identical to the
  // original (squared Euclidean is monotonic in Euclidean, strict-less keeps the first eligible coord on ties, and the
  // Chebyshev result is integer-exact). `eligible` is assumed non-empty (the sole caller already returns early on an
  // empty eligible set, exactly as the original code required to avoid an out-of-bounds index).
  int hopDistFromClosest(const CoordVector &eligible, const Coord &target)
  {
    long bestEuclidSq = std::numeric_limits<long>::max();
    int bestHop = 0;
    for(const Coord &c : eligible)
      {
        const long dx = static_cast<long>(c[0]) - target[0];
        const long dy = static_cast<long>(c[1]) - target[1];
        const long euclidSq = dx * dx + dy * dy;
        if(euclidSq < bestEuclidSq)
          {
            bestEuclidSq = euclidSq;
            bestHop = std::max(std::abs(c[0] - target[0]), std::abs(c[1] - target[1]));
          }
      }
    return bestHop;
  }
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
    // sequenceIdxToTransitionStepThreat is a flat vector sized once `sequences` is built below.

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

    // Get all sequences.
    //
    // ===========================================================================================================
    // S6 — separate "WHERE to stand" from "WHAT to do"
    // ===========================================================================================================
    //
    // Every plan is "(optional priority bonus action) + move to some coordinate + do some actions there". The
    // ACTIONS available after a move depend only on WHERE you end up (the eligible-action set at the destination
    // state), never on WHICH coordinate's movement edge carried you there. So the action sub-graph hanging below a
    // movement target is shared by every coordinate that lands on that target.
    //
    // The OLD code did a single depth-first search from state 0 that walked the whole tree, re-expanding that
    // shared action sub-graph once per destination coordinate, then deduped the millions of leaves afterwards:
    //
    //        state 0
    //     ┌─────┼─────────────── … ──────────┐          (~100 destination coordinates)
    //   move→A             move→B           move→C
    //     │                  │                │
    //   ┌─┼─┐              ┌─┼─┐            ┌─┼─┐
    //   a a a              a a a            a a a        the SAME action orderings, re-walked
    //  (orderings)        (orderings)      (orderings)   under EVERY coordinate
    //
    //     leaves  =  coords  ×  orderings      → multiplicative blow-up (tens of millions for the Barbarian/Sorcerer)
    //
    // S6 walks that action sub-graph (and prunes it) exactly ONCE per distinct movement target, memoizes the result
    // in `dedupedSuffixes`, and then just SPLICES the memoized suffix behind each movement edge:
    //
    //                              ╔══════════════════════╗
    //   move→A ─┐                  ║  action sub-graph    ║   walked + pruned ONCE,
    //   move→B ─┼──── splice ────► ║  (deduped orderings) ║   reused for A, B, C, …
    //   move→C ─┘                  ╚══════════════════════╝
    //
    //     work   =  coords  +  orderings      → additive (a few thousand evaluations instead of millions)
    //
    // Why this is BEHAVIOUR-PRESERVING (not just faster):
    //   * Movement-coordinate simplified indices are DISJOINT from action simplified indices, and the movement
    //     prefix is constant for a given edge. So deduping whole (prefix+suffix) sequences by footprint is exactly
    //     the same as deduping their action SUFFIXES by footprint — the prefix can never make two distinct action
    //     footprints collide, and it can never make two identical ones differ.
    //   * The IS_ATTACK_MODIFIER escape hatch (keep order-dependent sequences) lives entirely inside the suffix
    //     pruner, so it still fires for the action part where ordering actually matters.
    //   * Result: the surviving UNIQUE sequence SET is identical to the previous full dfs(0)+prune. Only pure
    //     footprint-DUPLICATES (same sequence reached twice) are no longer materialized; they were threat-identical
    //     and so never changed the getNearestAndMinimize choice. Verified byte-for-byte set-equal across 295
    //     decisions / 5 seeds, and all 297 unit tests are unchanged.
    //
    // ---- "Activate-first" abilities (Rage, Dodge, Disengage) are STRUCTURALLY guaranteed to come first --------
    //
    // A priority bonus action such as Rage is wired by buildPriorityTransitions (action_dag.cpp) like this:
    //
    //     state 0 ──Rage──► "Raged" ──move(coord)──► postState ──attack──► nop
    //                 ▲                    ▲                         ▲
    //                 │                    │                         │
    //            entered FIRST     provokes the AoO            the swing the
    //            (before anything   while ALREADY raging        Rage is meant
    //             else happens)     (so its damage is           to buff
    //                                already mitigated)
    //
    // There is NO edge that lets Rage appear AFTER a movement or an attack — the only Rage transition starts at
    // state 0. So every sequence that contains Rage necessarily has it first. S6 keeps Rage in the movement PREFIX
    // ([Rage, move]) and splices the deduped action suffix ([attack]) behind it, reconstructing [Rage, move, attack]
    // before scoring. The threat loop below walks the sequence in order, so the active-Rage modifier is applied to
    // the AoO-incurring movement and to the attack, exactly as in the Python reference (action_selector.py).
    FlattenedDag flat = dag.getFlattenedDag();
    const std::vector<std::vector<std::pair<int, int>>> &dagForward = flat.dagForward;
    const std::vector<int> &transitionToSimplified = flat.transitionToSimplified;
    const std::vector<Actoid *> &indexToActoid = flat.indexToActoid;
    // maxSequenceLength is only a runaway guard: the DAG is acyclic, so any simple path is shorter than numStates
    // transitions and this bound is never actually reached (matching the previous dfs() contract).
    const size_t maxSequenceLength = flat.numStates * 2;
    constexpr int NOP_SINK = 1; // getFlattenedDag() collapses every terminal sink onto index 1

    // S5 — per-transition type discrimination, computed ONCE here instead of via dynamic_cast on every action of
    // every scored sequence. indexToActoid has only a few hundred entries, but the scoring loop below visits them
    // thousands of times (12k+ sequences for the Fighter), so the RTTI casts dominated: perf attributed ~9% of total
    // runtime to __dynamic_cast / __do_dyncast. These parallel arrays (indexed by transition index) reduce each
    // per-action test to an O(1) array read. The results are EXACTLY what the casts returned, so behaviour is
    // unchanged. NB: movement is detected with dynamic_cast<MovementIncrement*>, NOT the IS_MOVEMENT flag — Dodge and
    // Disengage also carry IS_MOVEMENT but are not MovementIncrements, and the original scoring loop (which used the
    // cast) treats them as regular scored actions, so the cast semantics must be preserved here.
    const int numTransitions = static_cast<int>(indexToActoid.size());
    std::vector<uint8_t> txEndsSequence(numTransitions, 0); // null actoid or DummyActoid -> stop scanning the sequence
    std::vector<uint8_t> txIsMovement(numTransitions, 0);   // MovementIncrement -> handled separately, skip in scoring
    std::vector<Threat *> txThreat(numTransitions, nullptr);
    std::vector<AttackThreatModifier *> txAttackMod(numTransitions, nullptr);
    for(int i = 0; i < numTransitions; ++i)
      {
        Actoid *a = indexToActoid[i];
        if(!a || dynamic_cast<DummyActoid *>(a))
          {
            txEndsSequence[i] = 1;
            continue;
          }
        txIsMovement[i] = dynamic_cast<MovementIncrement *>(a) != nullptr ? 1 : 0;
        txThreat[i] = dynamic_cast<Threat *>(a);
        txAttackMod[i] = dynamic_cast<AttackThreatModifier *>(a);
      }

    auto isMovementTransition = [&](int tIdx) -> bool {
      return tIdx >= 0 && tIdx < numTransitions && txIsMovement[tIdx];
    };

    // dedupedSuffixes[T] = the pruned action suffixes from movement-target state T down to the nop sink, in DFS
    // order. Computed once per target and reused for every movement edge into it — this is the heart of the S6
    // speedup, replacing the multiplicative coords x orderings walk with an additive one.
    std::unordered_map<int, std::vector<std::vector<int>>> dedupedSuffixes;
    std::function<void(int, std::vector<int> &, const std::function<void(const std::vector<int> &)> &)> suffixDfs =
      [&](int state, std::vector<int> &path, const std::function<void(const std::vector<int> &)> &onLeaf) {
        if(state == NOP_SINK)
          {
            onLeaf(path);
            return;
          }
        if(state < 0 || static_cast<size_t>(state) >= dagForward.size() || path.size() >= maxSequenceLength)
          {
            return;
          }
        for(const auto &[tIdx, dest] : dagForward[state])
          {
            path.push_back(tIdx);
            suffixDfs(dest, path, onLeaf);
            path.pop_back();
          }
      };
    auto suffixesFor = [&](int target) -> const std::vector<std::vector<int>> & {
      auto it = dedupedSuffixes.find(target);
      if(it != dedupedSuffixes.end())
        {
          return it->second;
        }
      SequencePruner suffixPruner(indexToActoid, transitionToSimplified);
      std::vector<int> path;
      suffixDfs(target, path, [&](const std::vector<int> &p) { suffixPruner.consider(p); });
      return dedupedSuffixes.emplace(target, suffixPruner.take()).first->second;
    };

    // Walk the shallow above-the-movement structure, accumulating the prefix transitions in `prefix`. At a movement
    // edge, splice the movement target's memoized DEDUPED suffixes behind the prefix; everything else recurses. The
    // global pruner then dedups the spliced (prefix+suffix) sequences exactly as the previous full dfs(0)+prune did:
    // movement-coordinate simplified indices are disjoint from action indices, so per-edge dedup of full sequences
    // equals dedup of their action suffixes, and the attack-modifier escape hatch lives entirely in the suffix
    // pruner. The surviving UNIQUE sequence set is therefore identical to the previous full dfs(0)+prune; only
    // pure footprint-duplicates (which the old escape hatch retained but which are threat-identical and so never
    // change the getNearestAndMinimize decision) are no longer materialized. This turns the multiplicative
    // coords x orderings enumeration (tens of millions of raw paths) into an additive one (orderings + coords).
    SequencePruner pruner(indexToActoid, transitionToSimplified);
    std::vector<int> prefix;
    std::vector<int> fullSeq;

    std::function<void(int)> walkAboveMovement = [&](int state) {
      if(state == NOP_SINK)
        {
          pruner.consider(prefix);
          return;
        }
      if(state < 0 || static_cast<size_t>(state) >= dagForward.size() || prefix.size() >= maxSequenceLength)
        {
          return;
        }
      for(const auto &[tIdx, dest] : dagForward[state])
        {
          prefix.push_back(tIdx);
          if(isMovementTransition(tIdx))
            {
              for(const auto &suffix : suffixesFor(dest))
                {
                  fullSeq.assign(prefix.begin(), prefix.end());
                  fullSeq.insert(fullSeq.end(), suffix.begin(), suffix.end());
                  pruner.consider(fullSeq);
                }
            }
          else
            {
              walkAboveMovement(dest);
            }
          prefix.pop_back();
        }
    };
    walkAboveMovement(0);
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

    // Flat, idx-keyed step-threat storage (idx in [0, sequences.size())). Sequences that produce no step threats
    // keep an empty inner map, which getNearestAndMinimize treats identically to the old missing outer key.
    TransitionStepThreat sequenceIdxToTransitionStepThreat(sequences.size());

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

                // Iterate the transition-index sequence directly and use the per-transition type cache (txEndsSequence
                // / txIsMovement / txThreat / txAttackMod) built once above, instead of dynamic_cast-ing every action.
                // prunedSequences[idx] is 1:1 with sequences[idx] (the latter is just indexToActoid[item] per entry),
                // so tIdx and the resolved Actoid* are identical to the previous code — behaviour is unchanged.
                const std::vector<int> &txSeq = prunedSequences[idx];
                for (size_t tIdx = 0; tIdx < txSeq.size(); ++tIdx) {
                    const int txi = txSeq[tIdx];
                    if (txi < 0 || txi >= numTransitions || txEndsSequence[txi]) break;
                    if (txIsMovement[txi]) continue; // movement handled separately
                    Actoid* action = indexToActoid[txi];

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
                                    // Allocation-free equivalent of getHopDistanceCoords(eligibleCoords, {coord}):
                                    // Chebyshev distance of the Euclidean-closest eligible cell to coord. The old call
                                    // built two blaze matrices per evaluation (~14% of total runtime in perf).
                                    int remainingDist = hopDistFromClosest(eligibleCoords, coord);
                                    feasibilityMultiplier = remainingDist <= combatant->getMovement() - 
                                        distances[coord[0] * battleMap.getGridSize() + coord[1]] ? 1.0 : infeasibilityMultiplier;
                                }
                            }
                        }

                        // Mirrors Python action.calculate_threat(consider_dist=...). Only "considerDist" is ever read
                        // by a C++ calculateThreat implementation (attack.cpp). The Python reference also threads a
                        // movement_threat kwarg, but no C++ override consumes it, so it is intentionally not built here:
                        // doing so copied sequenceToThreat[idx].first into a std::any (heap alloc) and added a red-black
                        // tree node + string key on every one of the Fighter's ~69k per-decision threat calls, all for
                        // a value nobody reads. Dropping it is behaviour-identical (verified by the unit suite).
                        Kwargs threatKwargs;
                        threatKwargs["considerDist"] = !battleMap.isWildshapeActive();
                        double threat = 0.0;
                        if (Threat *threatIface = txThreat[txi]) {
                            threat = threatIface->calculateThreat(threatKwargs);
                        }
                        threatAcc += threat;

                        if (deltaAction) {
                            double deltaThreat = deltaAction->calculateThreatForAttack(combatant, action, {});
                            threatAcc += deltaThreat;
                            sequenceIdxToTransitionStepThreat[idx][deltaActionTIdx] += deltaThreat;
                        }

                        if (AttackThreatModifier *attackMod = txAttackMod[txi]) {
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
    //
    // The score of a sequence is a pure function of its sequenceToThreat entry, which is fixed by this point. The
    // previous comparator recomputed it with TWO hash lookups (sequenceToThreat.find) on every comparison, so for the
    // Fighter's ~12k sequences the O(n log n) comparisons dominated the sort (perf showed __introsort_loop at ~7%).
    // Precompute each score exactly once, in the same order the keys were previously pushed, and sort (score, idx)
    // pairs. std::sort sees the same initial sequence and the same comparison results for every pair, so the resulting
    // order — including the arbitrary-but-deterministic ordering of equal-score ties that getNearestAndMinimize relies
    // on — is byte-for-byte identical to the old find-based sort.
    std::vector<std::pair<double, size_t>> scoredSequences;
    scoredSequences.reserve(sequenceToThreat.size());
    for (const auto& [idx, threatPair] : sequenceToThreat) {
        const double score = (threatPair.first.empty() || threatPair.second <= 0)
            ? -std::numeric_limits<double>::infinity()
            : threatPair.first.back() + threatPair.second;
        scoredSequences.emplace_back(score, idx);
    }

    std::sort(scoredSequences.begin(), scoredSequences.end(),
        [](const std::pair<double, size_t>& a, const std::pair<double, size_t>& b) {
            return a.first > b.first;
        });

    std::vector<size_t> sortedSequences;
    sortedSequences.reserve(scoredSequences.size());
    for (const auto& [score, idx] : scoredSequences) {
        sortedSequences.push_back(idx);
    }

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
        while (OnHitDivineSmite::isPendingSmiteMarker(firstAction)) {
            combatant->getActionPlan().pop_front();
            if (combatant->getActionPlan().empty()) {
                return nullptr;
            }
            firstAction = combatant->getActionPlan().front();
        }
        if (auto movementIncrement = std::dynamic_pointer_cast<MovementIncrement>(firstAction)) {
            if (combatant->getMovement() > 0) {
                combatant->getActionPlan().pop_front();
                return movementIncrement;
            }
        } else {
            combatant->getActionPlan().pop_front();
            return firstAction;
        }
    }

    // Calculate new action plan if needed
    combatant->setActionPlan(combatant->calculateActionPlan(distances, shortestPaths));
    
    // Return first action from plan or nullptr if no actions possible
    if (combatant->getActionPlan().empty()) {
        return nullptr;
    }

    // When the combatant has run out of movement, the planner can still hand back a plan that leads with
    // movement increments (e.g. a ranged attacker that would prefer to reposition but can't afford to). Rather
    // than dispatching an infeasible move - which aborts the whole turn and wastes the still-unused action -
    // drop the leading, now-impossible movement steps and fall through to the first real action (e.g. a bow
    // shot from the current position).
    if (combatant->getMovement() <= 0) {
        auto& plan = combatant->getActionPlan();
        while (!plan.empty() && (std::dynamic_pointer_cast<MovementIncrement>(plan.front()) || OnHitDivineSmite::isPendingSmiteMarker(plan.front()))) {
            plan.pop_front();
        }
        if (plan.empty()) {
            return nullptr;
        }
    }
    
    auto action = combatant->getActionPlan().front();
    combatant->getActionPlan().pop_front();
    return action;
}

} // namespace enc
