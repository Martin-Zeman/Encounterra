#pragma once

#include <memory>
#include <unordered_map>
#include <unordered_set>
#include <optional>
#include <vector>
#include <utility>
#include <blaze/Blaze.h>
#include "core/types.hpp"
#include "core/state_machine.hpp"
#include "core/threat_utils.hpp"
#include "core/interfaces.hpp"
#include "actions/action_constants.hpp"

namespace enc {

// Ownership pool for the proto-DAG actoids (produced by generateProtoDag). The StateMachine stores raw Actoid*
// pointing into the shared_ptr instances kept alive here. Keyed by Actoid identity (the raw pointer), which both
// keeps every actoid alive and doubles as the identity->shared_ptr lookup the DAG/selection pipeline needs. Keying
// by pointer (instead of the old toString()-derived name) avoids the string construction and the name-collision
// hazard where two distinct actoids sharing a name would drop one shared_ptr and dangle its raw pointer.
using ActoidOwnershipPool = std::unordered_map<Actoid *, std::shared_ptr<Actoid>>;

// Transition identity -> eligible coordinates for that action.
using TransitionToEligibleCoords = std::unordered_map<Actoid *, CoordVector>;

// Synthetic movement transition identity -> (target coordinate, movement threat type).
using MovementTransToCoordAndType = std::unordered_map<Actoid *, std::pair<Coord, MovementThreatType>>;

// Hash/equality for sets of actoid identities (used to merge movement states that share eligible transitions).
struct ActoidSetHash
{
  std::size_t operator()(const std::unordered_set<Actoid *> &set) const
  {
    std::size_t h = 0;
    for(const auto *actoid : set)
      {
        h ^= actoid->getHash() + 0x9e3779b9 + (h << 6) + (h >> 2);
      }
    return h;
  }
};

struct ActoidSetEqual
{
  bool operator()(const std::unordered_set<Actoid *> &lhs, const std::unordered_set<Actoid *> &rhs) const { return lhs == rhs; }
};

struct PostTransitionResult {
    std::unordered_map<Actoid *, std::vector<std::pair<Actoid *, StateId>>> postPriorityTransitions;
    std::unordered_map<Actoid *, std::vector<std::pair<Actoid *, StateId>>> postPriorityBonusTransitions;
};

struct MovementStatesResult {
    std::unordered_map<std::unordered_set<Actoid *>, StateId, ActoidSetHash, ActoidSetEqual> eligibleTransitionsToState;
    std::unordered_map<Coord, std::unordered_set<Actoid *>> coordToEligibleTransitions;
};

struct ActionStateMachineResult {
    std::unique_ptr<StateMachine> stateMachine;
    std::unique_ptr<MovementTransToCoordAndType> movementTransToCoordAndType;
    std::unique_ptr<TransitionToEligibleCoords> transitionToEligibleCoords;
    // Ownership for the synthetic movement / sentinel actoids created while expanding the DAG. The StateMachine and
    // the maps above only store raw Actoid* into these; this keeps them alive for the whole selection pipeline.
    std::vector<std::shared_ptr<Actoid>> syntheticActoids;
    std::shared_ptr<ActoidFactory> movementFactory;
};

std::unordered_map<Actoid *, std::vector<std::pair<Actoid *, StateId>>>
getPostTransitionsOfPriorityTransitions(
    StateMachine& stateMachine,
    const std::unordered_map<AbilityType, PriorityActionInfo>& priorityActions);

PostTransitionResult getPostTransitionsOfAllPriorityTransitions(StateMachine& protoStateMachine);

std::vector<std::pair<Actoid *, StateId>>
getPostMistyStepTransitions(StateMachine& stateMachine);

MovementStatesResult createMovementStates(
    StateMachine& stateMachine,
    const TransitionToEligibleCoords& transitionToEligibleCoords);

void buildMistyStepTransitions(
    StateMachine& stateMachine,
    const std::vector<std::pair<Actoid *, StateId>>& msPostTransitions,
    const TransitionToEligibleCoords& transitionToEligibleCoords,
    MovementTransToCoordAndType& movementTransToCoordAndType,
    std::vector<std::shared_ptr<Actoid>>& syntheticActoids,
    ActoidFactory& movementFactory);

void buildPriorityTransitions(
    StateMachine& stateMachine,
    const std::unordered_map<Actoid *, std::vector<std::pair<Actoid *, StateId>>>& postPriorityTransitions,
    const TransitionToEligibleCoords& transitionToEligibleCoords,
    MovementTransToCoordAndType& movementTransToCoordAndType,
    const std::unordered_map<AbilityType, PriorityActionInfo>& priorityActionDict,
    std::vector<std::shared_ptr<Actoid>>& syntheticActoids,
    ActoidFactory& movementFactory);

ActionStateMachineResult buildActionStateMachine(
    Combatant* combatant,
    const StateMachine& protoStateMachine,
    const blaze::DynamicVector<int>& distances,
    const blaze::DynamicMatrix<Coord>& shortestPaths);

} // namespace enc
