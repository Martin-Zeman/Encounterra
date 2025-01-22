#pragma once

#include <regex>
#include <memory>
#include <unordered_map>
#include <unordered_set>
#include <algorithm>
#include <optional>
#include <blaze/Blaze.h>
#include "core/types.hpp"
#include "core/state_machine.hpp"
#include "core/threat_utils.hpp"
#include "core/interfaces.hpp"
#include "actions/action_constants.hpp"

namespace enc
{

  struct ActoidSetHash
  {
    size_t operator()(const std::unordered_set<std::shared_ptr<Actoid>> &set) const
    {
      size_t hash = 0;
      for(const auto &actoid : set)
        {
          hash ^= actoid->getHash() + 0x9e3779b9 + (hash << 6) + (hash >> 2);
        }
      return hash;
    }
  };

  struct ActoidSetEqual
  {
    bool operator()(const std::unordered_set<std::shared_ptr<Actoid>> &lhs, const std::unordered_set<std::shared_ptr<Actoid>> &rhs) const
    {
      if(lhs.size() != rhs.size())
        return false;
      return std::all_of(lhs.begin(), lhs.end(), [&rhs](const auto &actoid) { return rhs.contains(actoid); });
    }
  };

  struct ActionDagResult
  {
    StateMachine fsm;
    std::unordered_map<std::shared_ptr<Actoid>, std::pair<Coord, MovementThreatType>> movementTransToCoordAndType;
    std::unordered_map<std::shared_ptr<Actoid>, std::vector<Coord>> transitionToEligibleCoords;
  };
  // Regular expressions for movement patterns
  extern const std::regex regexMovementPattern;
  extern const std::regex regexMsMovementPattern;

  /**
   * Gets eligible follow-up actions to priority actions of the given dict present in the DAG.
   *
   * @param fsm The FSM on which we operate
   * @param prioActionDict Either PRIORITY_ACTIONS or PRIORITY_BONUS_ACTIONS
   * @return Dict mapping priority action -> list of eligible follow-up transitions
   */
  std::unordered_map<std::shared_ptr<Actoid>, std::vector<std::pair<std::shared_ptr<Actoid>, StateId>>>
  getPostTransitionsOfPriorityTransitions(StateMachine &fsm, const std::unordered_map<AbilityType, PriorityActionInfo> &prioActionDict);

  /**
   * Retrieves eligible follow-up actions for all priority actions present in the action finite state machine (FSM).
   *
   * @param protoFsm The action finite state machine (FSM) on which the operation is performed
   * @return A tuple of two dictionaries:
   *     1. Priority action -> list of eligible follow-up transitions
   *     2. Priority bonus action -> list of eligible follow-up transitions
   */
  std::pair<std::unordered_map<std::shared_ptr<Actoid>, std::vector<std::pair<std::shared_ptr<Actoid>, StateId>>>,
            std::unordered_map<std::shared_ptr<Actoid>, std::vector<std::pair<std::shared_ptr<Actoid>, StateId>>>>
  getPostTransitionsOfAllPriorityTransitions(StateMachine &protoFsm);

  /**
   * Gets all transitions that are available after Misty Step.
   *
   * @param fsm The FSM to analyze
   * @return Vector of transitions available after Misty Step
   */
  std::vector<std::pair<std::shared_ptr<Actoid>, StateId>> getPostMistyStepTransitions(StateMachine &fsm);

  /**
   * Movement states that share eligible transitions can be merged. Create new states for them.
   *
   * @param fsm The FSM to add states to
   * @param transitionToEligibleCoords Mapping from transitions to their eligible coordinates
   * @return Pair of:
   *     1. Map from eligible transitions set to newly created state
   *     2. Map from coordinate to set of eligible transitions
   */
  std::pair<std::unordered_map<std::unordered_set<std::shared_ptr<Actoid>>, StateId, ActoidSetHash, ActoidSetEqual>,
            std::unordered_map<Coord, std::unordered_set<std::shared_ptr<Actoid>>>>
  createMovementStates(StateMachine &fsm, const std::unordered_map<std::shared_ptr<Actoid>, std::vector<Coord>> &transitionToEligibleCoords);

  /**
   * Builds the Misty Step transitions of the FSM.
   *
   * @param fsm The FSM we're building
   * @param msPostTransitions Vector of transitions available after Misty Step
   * @param transitionToEligibleCoords Mapping from action names to their eligible coordinates
   * @param movementTransToCoordAndType Mapping from movement transition -> (coord, MovementThreatType)
   */
  void buildMistyStepTransitions(StateMachine &fsm, const std::vector<std::pair<std::shared_ptr<Actoid>, StateId>> &msPostTransitions,
                                 const std::unordered_map<std::shared_ptr<Actoid>, std::vector<Coord>> &transitionToEligibleCoords,
                                 std::unordered_map<std::shared_ptr<Actoid>, std::pair<Coord, MovementThreatType>> &movementTransToCoordAndType);

  /**
   * Builds the priority part of the FSM such as Dodge or Disengage.
   *
   * @param fsm The FSM we're building
   * @param postPriorityTransitions Map from action -> list of follow-up transitions
   * @param transitionToEligibleCoords Mapping from actions to their eligible coordinates
   * @param movementTransToCoordAndType Mapping from movement transition -> (coord, MovementThreatType)
   * @param prioActionDict Either PRIORITY_ACTIONS or PRIORITY_BONUS_ACTIONS
   */
  void buildPriorityTransitions(
    StateMachine &fsm,
    const std::unordered_map<std::shared_ptr<Actoid>, std::vector<std::pair<std::shared_ptr<Actoid>, StateId>>> &postPriorityTransitions,
    const std::unordered_map<std::shared_ptr<Actoid>, std::vector<Coord>> &transitionToEligibleCoords,
    std::unordered_map<std::shared_ptr<Actoid>, std::pair<Coord, MovementThreatType>> &movementTransToCoordAndType,
    const std::unordered_map<AbilityType, PriorityActionInfo> &prioActionDict);

  /**
   * Builds action FSM for a combatant given the combatant's proto_fsm. It determines eligible coords for each
   * action. Then the coords are pre-pended into the proto_fsm to form the final FSM. However, Misty Step, Dodge and
   * Disengage require special treatment. Misty Step generates a special form of movement which is added as a transition
   * to all post-Misty-Step states. Dodge and Disengage always make sense to be taken before any movement, therefore
   * in their case coords are also pre-pended to their follow-up actions.
   *
   * @param combatant The combatant for whom the FSM is modeled
   * @param protoFsm FSM representing all possible actions for combatant (doesn't model movement)
   * @param distances The distances to all squares (result of Dijkstra)
   * @param shortestPaths The shortest paths to all squares (result of Dijkstra)
   * @return Tuple of final FSM and mapping from movement actions to (coord, MovementThreatType)
   */
  ActionDagResult buildActionDag(Combatant &combatant, StateMachine protoFsm, const blaze::DynamicVector<int> &distances,
                                 const blaze::DynamicMatrix<Coord> &shortestPaths);

} // namespace enc
