#include <set>
#include "actions/action_fsm.hpp"
#include "actions/movement.hpp"
#include "actions/action_proto_fsm.hpp"
#include "actions/dummy_actoid_factory.hpp"
#include "core/state_machine.hpp"

namespace enc
{

  const std::regex regexMovementPattern("([msdchio]+)_\\((\\d+), (\\d+)\\)");
  const std::regex regexMsMovementPattern("[mschdio_]+\\((\\d+), (\\d+)\\)");

  const std::unordered_map<AbilityType, PriorityActionInfo> PRIORITY_ACTIONS
    = {{AbilityType::DODGE, {"do_", MovementThreatType::DODGED}}, {AbilityType::DISENGAGE, {"di_", MovementThreatType::DISENGAGED}}};

  const std::unordered_map<AbilityType, PriorityActionInfo> PRIORITY_BONUS_ACTIONS
    = {{AbilityType::CUNNING_DISENGAGE, {"cdi_", MovementThreatType::DISENGAGED}},
       {AbilityType::TOTEM_RAGE, {"m_", MovementThreatType::STANDARD}},
       {AbilityType::RAGE, {"m_", MovementThreatType::STANDARD}},
       {AbilityType::AGGRESSIVE, {"m_", MovementThreatType::STANDARD}}};

  std::unordered_map<Actoid *, std::vector<std::pair<Actoid *, StateId>>>
  getPostTransitionsOfPriorityTransitions(StateMachine &fsm, const std::unordered_map<AbilityType, PriorityActionInfo> &prioActionDict)
  {
    std::unordered_map<Actoid *, std::vector<std::pair<Actoid *, StateId>>> postPriorityTransitions;

    auto transitions = fsm.getForwardTransitions(0); // Get transitions from initial state
    for(const auto &transition : transitions)
      {
        /* TODO: Do I need to somehow reflect this from the original?
        if transition == 'None_0':
          break
        */
        auto action = transition.first;
        if(prioActionDict.contains(action->getAbilityType()))
          {
            std::vector<std::pair<Actoid *, StateId>> postTransitions;

            // Try to trigger the transition
            if(fsm.triggerTransition(action))
              {
                // We're now in the state after the priority action
                auto forwardTrans = fsm.getCurrentForwardTransitions();

                // Copy non-priority transitions
                std::copy_if(forwardTrans.begin(), forwardTrans.end(), std::back_inserter(postTransitions),
                             [](const auto &trans) { return !trans.first->hasFlag(ActoidFlags::IS_PRIORITY); });

                fsm.reset();
              }
            postPriorityTransitions[action] = postTransitions;
          }
      }
    return postPriorityTransitions;
  }

  std::pair<std::unordered_map<Actoid *, std::vector<std::pair<Actoid *, StateId>>>,
            std::unordered_map<Actoid *, std::vector<std::pair<Actoid *, StateId>>>>
  getPostTransitionsOfAllPriorityTransitions(StateMachine &protoFsm)
  {
    auto postPriorityActionTransitions = getPostTransitionsOfPriorityTransitions(protoFsm, PRIORITY_ACTIONS);
    auto postPriorityBonusActionTransitions = getPostTransitionsOfPriorityTransitions(protoFsm, PRIORITY_BONUS_ACTIONS);

    // Remove the original priority transitions, we don't want to have them pre-pended with coords
    // TODO: Shouldn't removing from state 0 be enough? The original is removing it from all states
    for(const auto &[priorityAction, _] : postPriorityActionTransitions)
      {
        protoFsm.removeTransitionFromAllStates(priorityAction);
      }

    for(const auto &[priorityBonusAction, _] : postPriorityBonusActionTransitions)
      {
        protoFsm.removeTransitionFromAllStates(priorityBonusAction);
      }

    return {postPriorityActionTransitions, postPriorityBonusActionTransitions};
  }

  std::vector<std::pair<Actoid *, StateId>> getPostMistyStepTransitions(StateMachine &fsm)
  {
    // Find Misty Step action in initial state transitions
    auto initialTransitions = fsm.getForwardTransitions(0);
    auto msIt = std::find_if(initialTransitions.begin(), initialTransitions.end(),
                             [](const auto &trans) { return trans.first->getAbilityType() == AbilityType::MISTY_STEP; });

    if(msIt == initialTransitions.end())
      {
        return {};
      }

    std::vector<std::pair<Actoid *, StateId>> msPostTransitions;
    if(fsm.triggerTransition(msIt->first))
      {
        auto forwardTrans = fsm.getCurrentForwardTransitions();

        // Filter out priority transitions
        std::copy_if(forwardTrans.begin(), forwardTrans.end(), std::back_inserter(msPostTransitions),
                     [](const auto &trans) { return !trans.first->hasFlag(ActoidFlags::IS_PRIORITY); });

        fsm.reset();
      }

    // Remove the original Misty Step transition
    fsm.removeTransition(msIt->first, 0);

    return msPostTransitions;
  }

  std::pair<std::unordered_map<std::unordered_set<Actoid *>, StateId, ActoidSetHash, ActoidSetEqual>,
            std::unordered_map<Coord, std::unordered_set<Actoid *>>>
  createMovementStates(StateMachine &fsm, const std::unordered_map<Actoid *, std::vector<Coord>> &transitionToEligibleCoords)
  {
    // Build coordinate to transitions mapping
    std::unordered_map<Coord, std::unordered_set<Actoid *>> coordToEligibleTransitions;

    for(const auto &[transition, coords] : transitionToEligibleCoords)
      {
        for(const auto &coord : coords)
          {
            coordToEligibleTransitions[coord].insert(transition);
          }
      }

    // Create states for unique sets of transitions
    std::unordered_map<std::unordered_set<Actoid *>, StateId, ActoidSetHash, ActoidSetEqual> eligibleTransitionsToState;

    for(const auto &[coord, transitions] : coordToEligibleTransitions)
      {
        if(!eligibleTransitionsToState.contains(transitions))
          {
            StateId newState = fsm.getNextStateId();
            eligibleTransitionsToState[transitions] = newState;
            fsm.addNewState(newState);
          }
      }

    return {eligibleTransitionsToState, coordToEligibleTransitions};
  }

  void buildMistyStepTransitions(StateMachine &fsm, const std::vector<std::pair<Actoid *, StateId>> &msPostTransitions,
                                 const std::unordered_map<Actoid *, std::vector<Coord>> &transitionToEligibleCoords,
                                 std::unordered_map<Actoid *, std::pair<Coord, MovementThreatType>> &movementTransToCoordAndType)
  {
    auto [eligibleTransitionsToState, coordToEligibleTransitions] = createMovementStates(fsm, transitionToEligibleCoords);

    for(const auto &[action, destState] : msPostTransitions)
      {
        auto it = transitionToEligibleCoords.find(action);
        if(it == transitionToEligibleCoords.end())
          continue; // Skip if no eligible coords

        for(const auto &coord : it->second)
          {
            auto &transitions = coordToEligibleTransitions[coord];
            StateId postMsState = eligibleTransitionsToState[transitions];

            // Create Misty Step movement action
            auto msFactory = std::make_shared<MovementFactory>(action->getFactory().getCombatant(), CoordVector{coord}, AbilityType::MISTY_STEP);
            auto msAction = msFactory->create(nullptr);

            // Add transitions
            movementTransToCoordAndType[msAction] = {coord, MovementThreatType::MISTY_STEPPED};
            fsm.addTransition(msAction, 0, postMsState);
            fsm.addTransition(action, postMsState, destState);
          }
      }
  }

  void buildPriorityTransitions(
    StateMachine &fsm,
    const std::unordered_map<Actoid *, std::vector<std::pair<Actoid *, StateId>>> &postPriorityTransitions,
    const std::unordered_map<Actoid *, std::vector<Coord>> &transitionToEligibleCoords,
    std::unordered_map<Actoid *, std::pair<Coord, MovementThreatType>> &movementTransToCoordAndType,
    const std::unordered_map<AbilityType, PriorityActionInfo> &prioActionDict)
  {
    auto [eligibleTransitionsToState, coordToEligibleTransitions] = createMovementStates(fsm, transitionToEligibleCoords);

    std::vector<StateId> newlyAddedStates;

    for(const auto &[priorityAction, postTransitions] : postPriorityTransitions)
      {
        if(postTransitions.empty())
          {
            fsm.addTransition(priorityAction, 0, -1); // Connect to NOP state
            continue;
          }

        auto actionType = priorityAction->getAbilityType();
        auto prioInfo = prioActionDict.at(actionType);

        StateId newPrioState = fsm.getNextStateId();
        fsm.addNewState(newPrioState);
        newlyAddedStates.push_back(newPrioState);
        fsm.addTransition(priorityAction, 0, newPrioState);

        for(const auto &[postAction, destState] : postTransitions)
          {
            auto it = transitionToEligibleCoords.find(postAction);
            if(it == transitionToEligibleCoords.end())
              continue;

            for(const auto &coord : it->second)
              {
                auto &transitions = coordToEligibleTransitions[coord];
                StateId postPtState = eligibleTransitionsToState[transitions];

                // Create priority movement action
                auto moveFactory = std::make_shared<MovementFactory>(priorityAction->getFactory().getCombatant(), CoordVector{coord}, actionType);
                auto moveAction = moveFactory->create(nullptr);

                movementTransToCoordAndType[moveAction] = {coord, prioInfo.threatType};
                fsm.addTransition(moveAction, newPrioState, postPtState);
                fsm.addTransition(postAction, postPtState, destState);
              }
          }
      }

    // Connect any unconnected priority states to NOP
    for(StateId state : newlyAddedStates)
      {
        if(fsm.getForwardTransitions(state).empty())
          {
            auto dummyAction = new DummyActoid(DummyActoidFactory::getInstance(), "dummy");
            fsm.addTransition(dummyAction, state, -1);
          }
      }
  }

  ActionDagResult buildActionDag(Combatant &combatant, StateMachine protoFsm, const blaze::DynamicVector<int> &distances,
                                 const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    auto &battleMap = BattleMap::getInstance();
    battleMap.calcVisibilityDictForAllCoords(combatant, shortestPaths);

    // Get priority transitions
    auto [postPriorityActionTransitions, postPriorityBonusActionTransitions] = getPostTransitionsOfAllPriorityTransitions(protoFsm);

    // Handle Misty Step if present
    std::vector<std::pair<Actoid *, StateId>> postMistyStepTransitions;
    if(auto initialTransitions = protoFsm.getForwardTransitions(0);
       std::any_of(initialTransitions.begin(), initialTransitions.end(),
                   [](const auto &trans) { return trans.first->getAbilityType() == AbilityType::MISTY_STEP; }))
      {
        postMistyStepTransitions = getPostMistyStepTransitions(protoFsm);
      }

    StateMachine fsm = protoFsm; // Create working copy

    // Get eligible coordinates for each type of action
    std::unordered_map<Actoid *, std::vector<Coord>> transitionToEligibleCoords;
    for(auto &[action, _] : fsm.getForwardTransitions(0))
      {
        if(action->getAbilityType() == AbilityType::MISTY_STEP)
          {
            continue;
          }

        if(action->getFactory().getCombatant()->isWildshapeForm())
          {
            Combatant& baseForm = action->getFactory().getCombatant()->getBaseForm();
            // Handle wildshape form actions
            battleMap.withCombatantWildshapeReplacement(*action, baseForm, battleMap.getCombatantCoordinates(baseForm).getRoot(),
                                                        [&](Combatant &form) {
                                                          if(auto coords = action->getEligibleCoords(distances, shortestPaths))
                                                            {
                                                              transitionToEligibleCoords[action] = *coords;
                                                            }
                                                        });
          }
        else
          {
            if(auto coords = action->getEligibleCoords(distances, shortestPaths))
              {
                transitionToEligibleCoords[action] = *coords;
              }
          }
      }

    // Remove actions without eligible coordinates
    auto initialTransitions = fsm.getForwardTransitions(0);
    for(const auto &[action, _] : initialTransitions)
      {
        if(!transitionToEligibleCoords.contains(action))
          {
            fsm.removeTransition(action, 0);
          }
      }

    // Create movement states and transitions
    auto [eligibleTransitionsToState, coordToEligibleTransitions] = createMovementStates(fsm, transitionToEligibleCoords);

    std::unordered_map<Actoid *, std::pair<Coord, MovementThreatType>> movementTransToCoordAndType;

    // Build standard movement transitions
    for(const auto &[action, coords] : transitionToEligibleCoords)
      {
        if(action->getAbilityType() == AbilityType::MISTY_STEP)
          continue;

        auto transitions = fsm.getForwardTransitions(0);
        auto it = std::find_if(transitions.begin(), transitions.end(), [&action](const auto &t) { return t.first == action; });
        if(it == transitions.end())
          continue;

        for(const auto &coord : coords)
          {
            auto &eligibleTransitions = coordToEligibleTransitions[coord];
            StateId movementState = eligibleTransitionsToState[eligibleTransitions];

            auto moveFactory
              = std::make_shared<MovementFactory>(action->getFactory().getCombatant(), CoordVector{coord}, AbilityType::STANDARD_MOVEMENT);
            auto moveAction = moveFactory->create(nullptr);

            movementTransToCoordAndType[moveAction] = {coord, MovementThreatType::STANDARD};
            fsm.addTransition(moveAction, 0, movementState);
            fsm.addTransition(action, movementState, it->second);
          }
        fsm.removeTransition(action, 0);
      }

    // Build special transitions
    if(!postMistyStepTransitions.empty())
      {
        buildMistyStepTransitions(fsm, postMistyStepTransitions, transitionToEligibleCoords, movementTransToCoordAndType);
      }

    buildPriorityTransitions(fsm, postPriorityActionTransitions, transitionToEligibleCoords, movementTransToCoordAndType, PRIORITY_ACTIONS);
    buildPriorityTransitions(fsm, postPriorityBonusActionTransitions, transitionToEligibleCoords, movementTransToCoordAndType,
                             PRIORITY_BONUS_ACTIONS);

    return {std::move(fsm), std::move(movementTransToCoordAndType), std::move(transitionToEligibleCoords)};
  }

} // namespace enc