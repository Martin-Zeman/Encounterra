#pragma once

#include <regex>
#include <memory>
#include <unordered_map>
#include <optional>
#include <blaze/Blaze.h>
#include "core/types.hpp"
#include "core/state_machine.hpp"
#include "core/threat_utils.hpp"
#include "core/interfaces.hpp"
#include "actions/action_constants.hpp"

namespace enc {

struct PriorityActionInfo
{
    std::string prefix;
    MovementThreatType threatType;
};

// Regular expressions for movement patterns
extern const std::regex regexMovementPattern;
extern const std::regex regexMsMovementPattern;

// extern const std::unordered_map<AbilityType, PriorityActionInfo> PRIORITY_ACTIONS;
// extern const std::unordered_map<AbilityType, PriorityActionInfo> PRIORITY_BONUS_ACTIONS;

using TransitionNameToActoid = std::unordered_map<std::string, std::shared_ptr<Actoid>>;
using TransitionToEligibleCoords = std::unordered_map<std::string, CoordVector>;
using MovementTransToCoordAndType = std::unordered_map<std::string, std::pair<Coord, MovementThreatType>>;

struct PostTransitionResult {
    std::unordered_map<std::string, std::vector<std::pair<std::string, StateId>>> postPriorityTransitions;
    std::unordered_map<std::string, std::vector<std::pair<std::string, StateId>>> postPriorityBonusTransitions;
};

struct MovementStatesResult {
    std::unordered_map<std::string, StateId> eligibleTransitionsToState;
    std::unordered_map<Coord, std::string> coordToEligibleTransitions;
};

struct ActionStateMachineResult {
    std::unique_ptr<StateMachine> stateMachine;
    std::unique_ptr<MovementTransToCoordAndType> movementTransToCoordAndType;
    std::unique_ptr<TransitionToEligibleCoords> transitionToEligibleCoords;
};

std::unordered_map<std::string, std::vector<std::pair<std::string, StateId>>> 
getPostTransitionsOfPriorityTransitions(
    StateMachine& stateMachine,
    const TransitionNameToActoid& transitionNameToActoid,
    const std::unordered_map<AbilityType, PriorityActionInfo>& priorityActions);

PostTransitionResult getPostTransitionsOfAllPriorityTransitions(
    StateMachine& protoStateMachine,
    const TransitionNameToActoid& transitionNameToActoid);

std::vector<std::pair<std::string, StateId>>
getPostMistyStepTransitions(
    StateMachine& stateMachine,
    const TransitionNameToActoid& transitionNameToActoid);

MovementStatesResult createMovementStates(
    StateMachine& stateMachine,
    const TransitionToEligibleCoords& transitionToEligibleCoords);

void buildMistyStepTransitions(
    StateMachine& stateMachine,
    const std::vector<std::pair<std::string, StateId>>& msPostTransitions,
    const TransitionToEligibleCoords& transitionToEligibleCoords,
    MovementTransToCoordAndType& movementTransToCoordAndType);

void buildPriorityTransitions(
    StateMachine& stateMachine,
    const std::unordered_map<std::string, std::vector<std::pair<std::string, StateId>>>& postPriorityTransitions,
    const TransitionToEligibleCoords& transitionToEligibleCoords,
    MovementTransToCoordAndType& movementTransToCoordAndType,
    const TransitionNameToActoid& transitionNameToActoid,
    const std::unordered_map<AbilityType, PriorityActionInfo>& priorityActionDict);

ActionStateMachineResult buildActionStateMachine(
    Combatant* combatant,
    const StateMachine& protoStateMachine,
    const TransitionNameToActoid& transitionNameToActoid,
    const blaze::DynamicVector<int>& distances,
    const blaze::DynamicMatrix<Coord>& shortestPaths);

} // namespace enc
