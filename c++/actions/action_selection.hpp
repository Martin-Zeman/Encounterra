#pragma once

#include <vector>
#include <memory>
#include <unordered_map>
#include <optional>
#include <array>
#include <string>
#include <functional>
#include <set>
#include <blaze/Math.h>
#include "core/interfaces.hpp"
// #include "combat/action_fsm.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include "core/threat_utils.hpp"
#include "core/state_machine.hpp"

struct TransitionSet
{
  std::set<std::string> transitions;

  bool operator==(const TransitionSet &other) const { return transitions == other.transitions; }
};

namespace std
{
  template <> struct hash<TransitionSet>
  {
    size_t operator()(const TransitionSet &ts) const
    {
      size_t hash = 0;
      for(const auto &str : ts.transitions)
        {
          hash ^= std::hash<std::string>{}(str) + 0x9e3779b9 + (hash << 6) + (hash >> 2);
        }
      return hash;
    }
  };

  template <> struct hash<std::pair<std::array<int, 2>, enc::MovementThreatType>>
  {
    size_t operator()(const std::pair<std::array<int, 2>, enc::MovementThreatType> &p) const
    {
      size_t seed = 0;
      // Hash the array elements
      seed ^= hash<int>()(p.first[0]) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
      seed ^= hash<int>()(p.first[1]) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
      // Hash the enum
      seed ^= hash<int>()(static_cast<int>(p.second)) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
      return seed;
    }
  };
}

namespace enc
{
  using ThreatScore = std::pair<std::vector<double>, double>; // [movement threat, action threat]

  struct SequenceSearchResult
  {
    std::vector<Actoid *> sequence;
    ThreatScore threat;
    std::unordered_map<Actoid *, CoordVector> msTransitionPaths;
  };

  struct ActoidVectorHash
  {
    size_t operator()(const std::vector<Actoid *> &vec) const
    {
      size_t hash = 0;
      for(const auto &actoid : vec)
        {
          hash ^= actoid->getHash() + 0x9e3779b9 + (hash << 6) + (hash >> 2);
        }
      return hash;
    }
  };

  // struct ActoidVectorEqual
  // {
  //   bool operator()(const std::vector<Actoid *> &lhs, const std::vector<Actoid *> &rhs) const
  //   {
  //     return lhs.size() == rhs.size() && std::equal(lhs.begin(), lhs.end(), rhs.begin(), [](const auto &l, const auto &r) { return l == r; });
  //   }
  // };

  struct ActionSequence
  {
    std::vector<Actoid *> actions;
    double threatScore;

    bool operator==(const ActionSequence &other) const
    {
      if(actions.size() != other.actions.size())
        {
          return false;
        }
      for(size_t i = 0; i < actions.size(); ++i)
        {
          if(actions[i] != other.actions[i])
            return false;
        }
      return true;
    }
  };

  struct ActionSequenceHash
  {
    size_t operator()(const ActionSequence &seq) const
    {
      size_t hash = 0;
      for(const auto &action : seq.actions)
        {
          // Combine hashes using FNV-1a inspired approach
          hash ^= std::hash<void *>{}(action) + 0x9e3779b9 + (hash << 6) + (hash >> 2);
        }
      return hash;
    }
  };

  double getDistToActionSequenceCoord(const std::vector<Actoid *> &sequence, const blaze::DynamicVector<int> &distances);

  /**
   *  Filters, minimizes, and sorts action sequences to find the one with maximum threat while maintaining minimum distance.
   *
   *   This function takes a list of action sequences and performs the following steps:
   *   1. Filter: It filters the sequences to only include those with the maximum threat (if there are multiple sequences with the same maximum
   *    threat).
   *   2. Minimize: It minimizes the length of each sequence while ensuring the total threat remains the same. This step discards actions that
   *   do not add any additional threat.
   *   3. Sort: It sorts the sequences by their length in ascending order.
   *
   *   The function is designed to be used in the context of the `get_movement_and_threat_for_next_turn` function. It helps in selecting the most
   *   optimal action sequence among sets of actions with equal threat but different orders.
   *
   *   @param sequences: List of all action sequences in no particular order.
   *   @param sortedSequences: Indices of sequences sorted by threat in descending order.
   *   @param sequenceToThreat: A dictionary mapping sequence index to its threat value.
   *   @param distances: A pre-computed dictionary of distances to all coordinates.
   *   @param sequenceIdxToTransitionStepThreat: A dictionary of dictionaries.  Maps for each sequence index to a dict
   *   of individual transition indices -> threat contributions.
   *   @return: A pair of the action sequence with maximum threat and more distant coordinate requirement after
   *   minimization and the maximum threat.
   */
  std::pair<std::vector<Actoid *>, ThreatScore>
  getNearestAndMinimize(std::vector<std::vector<Actoid *>> &sequences, const std::vector<size_t> &sortedSequences,
                        const std::unordered_map<size_t, ThreatScore> &sequenceToThreat, const blaze::DynamicVector<int> &distances,
                        const std::unordered_map<size_t, std::unordered_map<size_t, double>> &sequenceIdxToTransitionStepThreat);

  /**
   * Finds the path through the FSM which represents the movement and actions with the highest calculated threat.
   * We take advantage of the fact that as a result of the DFS traversal the coordinates in generated sequences
   * are block-wise. Therefore, we can process the sequences by these coord-wise blocks and only call
   * withCombatantPosition once per block.
   */
  SequenceSearchResult
  findBestSequence(Combatant &combatant, const StateMachine &fsm,
                   const std::unordered_map<Actoid *, std::vector<Coord>> &transitionToEligibleCoords,
                   std::unordered_map<Actoid *, std::pair<Coord, MovementThreatType>> &movementTransToCoordAndType,
                   const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths,
                   double infeasibilityMultiplier = 0.5);

  /**
   *  Calculates the next best action. The algorithm works in two phases. In the first phase when the combatant still has movement left,
   *  it follows the steps described above. In the second phase, once the combatant reaches the target destination or runs out of movement
   *  the best action is recalculated every time to react to any possible changes on the battle_map.
   *  @return: the next best actoid
   */
  Actoid * getAction(Combatant &combatant);

} // namespace enc