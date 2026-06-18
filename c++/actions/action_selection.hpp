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
// #include "combat/action_dag.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include "core/threat_utils.hpp"
#include "core/state_machine.hpp"

namespace enc
{

  // Action/movement transitions are identified by their owning Actoid* (pointer identity into the proto/synthetic
  // actoid pools), replacing the legacy string transition names.
  using MovementTransitionMap = std::unordered_map<Actoid *, std::pair<Coord, MovementThreatType>>;
  using TransitionToEligibleCoords = std::unordered_map<Actoid *, CoordVector>;
  using SequenceToThreat = std::unordered_map<size_t, std::pair<std::vector<double>, double>>; // first part is the movement component of the threat, second is the action component
  using TransitionStepThreat = std::unordered_map<size_t, std::unordered_map<size_t, double>>;
  using CoordToSequenceIds = std::unordered_map<std::pair<Coord, MovementThreatType>, std::vector<size_t>>;
  // Maps a Misty Step movement transition (by actoid identity) to its serialized movement path.
  using TransitionToMsPath = std::unordered_map<Actoid *, std::vector<std::string>>;

//   struct DagBuildResult
//   {
//     std::unique_ptr<StateMachine> dag;
//     MovementTransitionMap movementMap;
//     TransitionToEligibleCoords eligibleCoords;
//   };

  struct DagBuildResult
  {
    std::unique_ptr<StateMachine> dag;
    std::unordered_map<std::string, std::pair<Coord, MovementThreatType>> movementTransToCoordAndType;
  };

  struct BestSequenceResult
  {
    std::vector<Actoid *> sequence;
    TransitionToMsPath msPathMap;
    std::array<double, 2> maxThreat;
  };

  std::vector<std::vector<std::string>> pruneSequences(const std::vector<std::vector<std::string>> &sequences,
                                                       const std::unordered_map<size_t, Actoid *> &indexToActoid,
                                                       const std::unordered_map<std::string, std::string> &transitionToSimplified);

  CoordToSequenceIds
  createCoordToSequenceMapping(const std::vector<std::vector<Actoid *>> &sequences, const MovementTransitionMap &movementTransitionToCoordAndType);

  double getDistToActionSequenceCoord(const std::vector<Actoid *> &sequence, const blaze::DynamicVector<int> &distances);

  /**
   *  Filters, minimizes, and sorts action sequences to find the one with maximum threat while maintaining minimum distance.

      This function takes a list of action sequences and performs the following steps:
      1. Filter: It filters the sequences to only include those with the maximum threat (if there are multiple sequences with the same maximum
       threat).
      2. Minimize: It minimizes the length of each sequence while ensuring the total threat remains the same. This step discards actions that
      do not add any additional threat.
      3. Sort: It sorts the sequences by their length in ascending order.

      The function is designed to be used in the context of the `get_movement_and_threat_for_next_turn` function. It helps in selecting the most
   optimal action sequence among sets of actions with equal threat but different orders.

      :param sequences: List of all action sequences in no particular order.
      :param sorted_sequences: Indices of sequences sorted by threat in descending order.
      :param sequence_to_threat: A dictionary mapping sequence index to its threat value.
      :param distances: A pre-computed dictionary of distances to all coordinates.
      :param sequence_idx_to_transition_step_threat: A dictionary of dictionaries.  Maps for each sequence index to a dict
      of individual transition indices -> threat contributions.
      :param transition_name_to_action: dict mapping action names -> actions
      :return: A tuple of the action sequence with maximum threat and more distant coordinate requirement after
      minimization and the maximum threat.
   */
  std::pair<std::vector<Actoid *>, std::pair<std::vector<double>, double>>
  getNearestAndMinimize(std::vector<std::vector<Actoid *>> &sequences, const std::vector<size_t> &sortedSequences,
                        const SequenceToThreat &sequenceToThreat, const blaze::DynamicVector<int> &distances,
                        const TransitionStepThreat &sequenceIdxToTransitionStepThreat);

  /**
   *     A helper function which decodes an action which represents movement with the possibility of including Misty Step into a sequence of
      actions which look like: regular movement (optional), Misty Step, regular movement (optional)
      :param combatant: the combatant for whom the actions are translated
      :param initial_coord: the initial coordinate of the combatant
      :param ms_path: name of the current action to be decoded
      :param actions: the list of actions to which we add the resulting sequence
      :param ms_factory: Optimization to avoid reallocation: Misty Step factory instance
      :return: None but actions shall be modified
   */
  void decodeMsPathToActions(Combatant *combatant, const Coord &initialCoord, const std::vector<std::string> &msPath,
                             std::vector<std::shared_ptr<Actoid>> &actions, std::shared_ptr<ActoidFactory>& msFactory);

  /**
   *  Translates the string form of the longest path back to action objects
      :param combatant: the combatant for whom the actions are translated
      :param distances: potentially already pre-computed distances to all coords
      :param shortest_paths: potentially already pre-computed shortest paths to all coords
      :param transition_name_to_action: dictionary mapping of non-movement types to actions
      :param movement_trans_to_coord_and_type: mapping from movement transition -> coord, MovementThreatType
      :param sequence: list of best actions as strings
      :param transition_name_to_ms_path: dictionary mapping of transition names to paths that may include a Misty Step (can be empty)
      :return: list of the following types: np.array, action, bonus action
   */
  std::vector<std::shared_ptr<Actoid>>
  translateSequenceToActions(Combatant *combatant, const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths,
                             const std::unordered_map<std::string, std::shared_ptr<Actoid>> &transitionNameToActoid,
                             const MovementTransitionMap &movementTransitionToCoordAndType, const std::vector<Actoid *> &sequence,
                             const TransitionToMsPath &transitionNameToMsPath);

  // PriorityTransitionsResult
  // getPostTransitionsOfAllPriorityTransitions(const std::unique_ptr<StateMachine> &protoDag,
  //                                            const std::unordered_map<std::string, std::shared_ptr<Actoid>> &transitionNameToAction);

  /**
   *  Builds action DAG for a combatant given the combatant's proto_dag. It determines eligible coords for each
      action. Then the coords are pre-pended into the proto_dag to form the final DAG. However, Misty Step, Dodge and
      Disengage require special treatment. Misty Step generates a special form of movement which is added as a transition
      to all post-Misty-Step states. Dodge and Disengage always make sense to be taken before any movement, therefore
      in their case coords are also pre-pended to their follow-up actions.
      :param combatant: the combatant for whom the DAG is modeled
      :param proto_dag: DAG (finite state machine) representing all possible actions for combatant. Doesn't model movement.
      :param transition_name_to_action: dict mapping action names -> actions
      :param distances: the distances to all squares (result of Dijkstra)
      :param shortest_paths: the shortest paths to all squares (result of Dijkstra)
      :return: Tuple of:
          - dict which maps threat -> (start_index, end_index) and a mapping from state name -> coord
          - dict which maps a movement transition -> to target coord
   */
  // std::optional<DagBuildResult> buildActionDag(Combatant *combatant, const std::unique_ptr<StateMachine> &protoDag,
  //                                              const std::unordered_map<std::string, std::shared_ptr<Actoid>> &transitionNameToAction,
  //                                              const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths);

  /**
   *  Finds the path through the DAG which represents the movement and actions with the highest calculated threat.
      We're taking advantage of the fact that as a result of the DFS traversal the coordinates in generated sequences are block-wise.
      Therefore, we can process the sequences by these coord-wise blocks and only call as_if_combatant_position once per block.
      To achieve this, coord_to_sequence_ids needs mapping between a target coordinate to all sequence ids which contain it, needs to be
      built.
      :param combatant: the combatant for whom the DAG is modeled
      :param dag: finite state machine representing all possible actions for combatant
      :param transition_name_to_action: dict mapping non-movement transition names -> action objects
      :param transition_to_eligible_coords: dict mapping non-movement transition names -> their eligible coordinates
      :param movement_transition_to_coord_and_type: dict mapping movement transition names -> target coord, MovementThreatType
      :param distances: potentially already pre-computed distances to all coords
      :param shortest_paths: potentially already pre-computed shortest paths to all coords
      :return: the longest path in the DAG as per the threat along its edges and nodes and a mapping of transitions names
      to special Misty Step paths
   */
  std::optional<BestSequenceResult>
  findBestSequence(Combatant *combatant, const StateMachine &dag,
                   const std::unordered_map<std::string, std::shared_ptr<Actoid>> &transitionNameToActoid,
                   const TransitionToEligibleCoords &transitionToEligibleCoords, const MovementTransitionMap &movementTransitionToCoordAndType,
                   const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths,
                   double infeasibilityMultiplier = 0.5);

  /**
   *     Calculates the next best action. The algorithm works in two phases. In the first phase when the combatant still has movement left,
      it follows the steps described above. In the second phase, once the combatant reaches the target destination or runs out of movement
      the best action is recalculated every time to react to any possible changes on the battle_map.
      :return: the next best actoid
   */
  std::shared_ptr<Actoid> getAction(Combatant *combatant);

} // namespace enc