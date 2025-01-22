#include "actions/default_action_plan_strategy.hpp"
#include "actions/movement.hpp"
#include "actions/action_selection.hpp"
#include "actions/action_proto_fsm.hpp"
#include "actions/action_fsm.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"

namespace enc {

std::vector<std::shared_ptr<Actoid>> DefaultActionPlanStrategy::calculateActionPlan(
    const blaze::DynamicVector<int>& distances,
    const blaze::DynamicMatrix<Coord>& shortestPaths)
{
    auto protoFsm = generateProtoFSM(_combatant);
    auto [fsm, movementTransToCoordAndType, transitionToEligibleCoords] = 
        buildActionDag(_combatant, std::move(protoFsm), distances, shortestPaths);

    if (fsm.getNumStates() == 2U) {  // TODO: Check if this is the right proxy for an empty FSM
        std::vector<std::shared_ptr<Actoid>> movement;
        if (_combatant.getMovement() > 0) {
            auto [nextTurnMovement, _] = getMovementAndThreatForNextTurn(distances, shortestPaths);
            return nextTurnMovement;
        }
        return movement;
    }

    auto [bestSequence, maxThreat, msTransitionPaths] = 
        findBestSequence(_combatant, fsm, transitionToEligibleCoords,
                        movementTransToCoordAndType, distances, shortestPaths);

    if (bestSequence.empty()) {
        return {};
    }

    return bestSequence;
}

std::pair<std::vector<std::shared_ptr<Actoid>>, std::array<double, 2>>
DefaultActionPlanStrategy::getMovementAndThreatForNextTurn(const blaze::DynamicVector<int> &distances,
                                                           const blaze::DynamicMatrix<Coord> &shortestPaths, double infeasibilityMultiplier)
{
  std::vector<std::shared_ptr<Actoid>> bestSequence;
  std::array<double, 2> maxThreat{0.0, 0.0};

  _combatant.withHasAction([&]() {
    auto protoFsm = generateProtoFSM(_combatant);
    auto [fsm, movementTransToCoordAndType, transitionToEligibleCoords] = buildActionDag(_combatant, std::move(protoFsm), distances, shortestPaths);

    if(fsm.getNumStates() > 2U)
      {
        auto [sequence, threat, _] = findBestSequence(_combatant, fsm, transitionToEligibleCoords, movementTransToCoordAndType, distances,
                                                      shortestPaths, infeasibilityMultiplier);
        bestSequence = std::move(sequence);
        // Set movement threat to last element of the vector, and action threat
        if(!threat.first.empty())
          {
            maxThreat[0] = threat.first.back();
          }
        maxThreat[1] = threat.second;
      }
  });

  return std::make_pair(extractMovement(distances, shortestPaths, bestSequence), maxThreat);
}

std::vector<std::shared_ptr<Actoid>> DefaultActionPlanStrategy::extractMovement(
    const blaze::DynamicVector<int>& distances,
    const blaze::DynamicMatrix<Coord>& shortestPaths,
    const std::vector<std::shared_ptr<Actoid>>& sequence)
{
    std::vector<std::shared_ptr<Actoid>> actions;
    auto& battleMap = BattleMap::getInstance();

    for (const auto& action : sequence) {
        if (auto* movement = dynamic_cast<MovementIncrement*>(action.get())) {
            const Coord& targetCoord = movement->getIncrement();
            auto pathOpt = battleMap.getPathToCoord(_combatant, targetCoord, 
                                                  distances, shortestPaths, true);
            if (pathOpt) {
                MovementFactory generator(_combatant, *pathOpt, AbilityType::STANDARD_MOVEMENT);
                auto moveActions = generator.createAll();
                actions.insert(actions.end(), moveActions.begin(), moveActions.end());
            }
            break;  // Only process first movement action
        }
    }

    return actions;
}

} // namespace enc
