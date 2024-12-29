#include <set>
#include "actions/action_fsm.hpp"
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

  std::unordered_map<std::string, std::vector<std::pair<std::string, StateId>>>
  getPostTransitionsOfPriorityTransitions(StateMachine &stateMachine, const TransitionNameToActoid &transitionNameToActoid,
                                          const std::unordered_map<AbilityType, PriorityActionInfo> &priorityActions)
  {
    std::unordered_map<std::string, std::vector<std::pair<std::string, StateId>>> postPriorityTransitions;

    for(const auto &transition : stateMachine.getAllTransitions())
      {
        if(transition == "None_0")
          {
            break;
          }

        auto actoid = transitionNameToActoid.at(transition);
        if(priorityActions.find(actoid->getAbilityType()) != priorityActions.end())
          {
            std::vector<std::pair<std::string, StateId>> postTransitions;

            if(stateMachine.triggerTransition(transition))
              {
                try
                  {
                    auto forwardTrans = stateMachine.getForwardTransitions(stateMachine.getCurrentState());
                    for(const auto &ft : forwardTrans)
                      {
                        if(!transitionNameToActoid.at(ft.first)->hasFlag(ActoidFlags::IS_PRIORITY))
                          {
                            postTransitions.push_back(ft);
                          }
                      }
                  }
                catch(const std::out_of_range &)
                  {
                    // Handle case when target state is nop
                  }
                stateMachine.reset();
              }
            postPriorityTransitions[transition] = postTransitions;
          }
      }
    return postPriorityTransitions;
  }

  PostTransitionResult
  getPostTransitionsOfAllPriorityTransitions(StateMachine &protoStateMachine, const TransitionNameToActoid &transitionNameToActoid)
  {
    auto postPriorityActionTransitions = getPostTransitionsOfPriorityTransitions(protoStateMachine, transitionNameToActoid, PRIORITY_ACTIONS);
    auto postPriorityBonusActionTransitions
      = getPostTransitionsOfPriorityTransitions(protoStateMachine, transitionNameToActoid, PRIORITY_BONUS_ACTIONS);

    for(const auto &[priorityTransition, _] : postPriorityActionTransitions)
      {
        for(const auto &originState : protoStateMachine.getAllStates())
          {
            protoStateMachine.removeTransition(priorityTransition, originState);
          }
      }

    for(const auto &[priorityTransition, _] : postPriorityBonusActionTransitions)
      {
        for(const auto &originState : protoStateMachine.getAllStates())
          {
            protoStateMachine.removeTransition(priorityTransition, originState);
          }
      }

    return {postPriorityActionTransitions, postPriorityBonusActionTransitions};
  }

  MovementStatesResult createMovementStates(StateMachine &stateMachine, const TransitionToEligibleCoords &transitionToEligibleCoords)
  {
    std::unordered_map<Coord, std::set<std::string>> coordToTransitions;

    for(const auto &[transitionName, coords] : transitionToEligibleCoords)
      {
        for(const auto &coord : coords)
          {
            coordToTransitions[coord].insert(transitionName);
          }
      }

    std::unordered_map<std::string, StateId> eligibleTransitionsToState;
    std::unordered_map<Coord, std::string> coordToEligibleTransitions;

    for(const auto &[coord, transitions] : coordToTransitions)
      {
        std::string transitionKey;
        for(const auto &t : transitions)
          {
            transitionKey += t + ";";
          }
        coordToEligibleTransitions[coord] = transitionKey;

        if(eligibleTransitionsToState.find(transitionKey) == eligibleTransitionsToState.end())
          {
            StateId newState = stateMachine.getNextStateId();
            eligibleTransitionsToState[transitionKey] = newState;
            stateMachine.addNewState(newState);
          }
      }

    return {eligibleTransitionsToState, coordToEligibleTransitions};
  }

  std::vector<std::pair<std::string, StateId>>
  getPostMistyStepTransitions(StateMachine &stateMachine, const TransitionNameToActoid &transitionNameToActoid)
  {
    stateMachine.triggerTransition("Misty Step to 0, 0_1");
    std::vector<std::pair<std::string, StateId>> msPostTransitions;

    try
      {
        auto forwardTrans = stateMachine.getForwardTransitions(stateMachine.getCurrentState());
        for(const auto &pt : forwardTrans)
          {
            if(!transitionNameToActoid.at(pt.first)->hasFlag(ActoidFlags::IS_PRIORITY))
              {
                msPostTransitions.push_back(pt);
              }
          }
      }
    catch(const std::out_of_range &)
      {
        // Handle case when no transitions found
      }

    stateMachine.reset();
    stateMachine.removeTransition("Misty Step to 0, 0_1", 0);
    return msPostTransitions;
  }

  void
  buildMistyStepTransitions(StateMachine &stateMachine, const std::vector<std::pair<std::string, StateId>> &msPostTransitions,
                            const TransitionToEligibleCoords &transitionToEligibleCoords, MovementTransToCoordAndType &movementTransToCoordAndType)
  {
    auto [eligibleTransitionsToState, coordToEligibleTransitions] = createMovementStates(stateMachine, transitionToEligibleCoords);

    for(const auto &mspt : msPostTransitions)
      {
        try
          {
            const auto &coords = transitionToEligibleCoords.at(mspt.first);
            for(const auto &coord : coords)
              {
                StateId postMsState = eligibleTransitionsToState.at(coordToEligibleTransitions.at(coord));
                std::string movementTransitionName = "ms_" + std::to_string(coord[0]) + "_" + std::to_string(coord[1]);

                movementTransToCoordAndType[movementTransitionName] = {coord, MovementThreatType::MISTY_STEPPED};

                stateMachine.addTransition(movementTransitionName, 0, postMsState);
                stateMachine.addTransition(mspt.first, postMsState, mspt.second);
              }
          }
        catch(const std::out_of_range &)
          {
            // Handle case when coordinates not available
          }
      }
  }

  void buildPriorityTransitions(StateMachine &stateMachine,
                                const std::unordered_map<std::string, std::vector<std::pair<std::string, StateId>>> &postPriorityTransitions,
                                const TransitionToEligibleCoords &transitionToEligibleCoords,
                                MovementTransToCoordAndType &movementTransToCoordAndType, const TransitionNameToActoid &transitionNameToActoid,
                                const std::unordered_map<AbilityType, PriorityActionInfo> &priorityActionDict)
  {
    auto [eligibleTransitionsToState, coordToEligibleTransitions] = createMovementStates(stateMachine, transitionToEligibleCoords);

    std::vector<StateId> newlyAddedStates;

    for(const auto &[transition, postTransitions] : postPriorityTransitions)
      {
        if(postTransitions.empty())
          {
            StateId nopState = stateMachine.getNextStateId();
            stateMachine.addNewState(nopState);
            stateMachine.addTransition(transition, 0, nopState);
            continue;
          }

        std::string actionType = transition.substr(0, transition.find(" "));
        StateId newPrioState = stateMachine.getNextStateId();

        const auto &priorityInfo = priorityActionDict.at(transitionNameToActoid.at(transition)->getAbilityType());
        const auto &prefix = priorityInfo.prefix;

        stateMachine.addNewState(newPrioState);
        newlyAddedStates.push_back(newPrioState);
        stateMachine.addTransition(transition, 0, newPrioState);

        for(const auto &postTransition : postTransitions)
          {
            try
              {
                const auto &coords = transitionToEligibleCoords.at(postTransition.first);
                for(const auto &coord : coords)
                  {
                    StateId postPtState = eligibleTransitionsToState.at(coordToEligibleTransitions.at(coord));
                    std::string movementTransitionName = prefix + std::to_string(coord[0]) + "_" + std::to_string(coord[1]);

                    movementTransToCoordAndType[movementTransitionName] = {coord, priorityInfo.threatType};

                    stateMachine.addTransition(movementTransitionName, newPrioState, postPtState);
                    stateMachine.addTransition(postTransition.first, postPtState, postTransition.second);
                  }
              }
            catch(const std::out_of_range &)
              {
                // Handle case when coordinates not available
              }
          }
      }

    // Connect unconnected states to NOP
    for(const auto &newState : newlyAddedStates)
      {
        auto forwardTrans = stateMachine.getForwardTransitions(newState);
        if(forwardTrans.empty())
          {
            StateId nopState = stateMachine.getNextStateId();
            stateMachine.addNewState(nopState);
            stateMachine.addTransition("dummy", newState, nopState);
          }
      }
  }

  ActionStateMachineResult
  buildActionStateMachine(Combatant *combatant, const StateMachine &protoStateMachine, const TransitionNameToActoid &transitionNameToActoid,
                          const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    auto [postPriorityActionTransitions, postPriorityBonusActionTransitions]
      = getPostTransitionsOfAllPriorityTransitions(const_cast<StateMachine &>(protoStateMachine), transitionNameToActoid);

    std::vector<std::pair<std::string, StateId>> msPostTransitions;
    TransitionToEligibleCoords msTransitionToEligibleCoords;

    const auto &transitionNames = protoStateMachine.getAllTransitions();
    if(std::find(transitionNames.begin(), transitionNames.end(), "Misty Step to 0, 0_1") != transitionNames.end())
      {
        msPostTransitions = getPostMistyStepTransitions(const_cast<StateMachine &>(protoStateMachine), transitionNameToActoid);
      }

    auto stateMachine = std::make_unique<StateMachine>(protoStateMachine);
    auto movementTransToCoordAndType = std::make_unique<MovementTransToCoordAndType>();
    auto transitionToEligibleCoords = std::make_unique<TransitionToEligibleCoords>();

    if(transitionNames.empty() || transitionNames[0] == "None_0")
      {
        return {std::move(stateMachine), std::move(movementTransToCoordAndType), std::move(transitionToEligibleCoords)};
      }

    // Get eligible coordinates for each transition
    for(const auto &transitionName : transitionNames)
      {
        try
          {
            auto actoid = transitionNameToActoid.at(transitionName);
            auto eligibleCoords = actoid->getEligibleCoords(distances, shortestPaths);
            if(eligibleCoords)
              {
                (*transitionToEligibleCoords)[transitionName] = *eligibleCoords;
              }
          }
        catch(const std::out_of_range &)
          {
            continue;
          }
      }

    // Remove transitions without eligible coordinates
    for(const auto &transitionName : transitionNames)
      {
        try
          {
            if(transitionName == "None_0" || transitionName == "dummy" || transitionName == "nop")
              {
                continue;
              }

            const auto &coords = transitionToEligibleCoords->at(transitionName);
            if(coords.empty())
              {
                stateMachine->removeTransition(transitionName, 0);
              }
          }
        catch(const std::out_of_range &)
          {
            stateMachine->removeTransition(transitionName, 0);
          }
      }

    // Handle Misty Step transitions if present
    if(!msPostTransitions.empty())
      {
        buildMistyStepTransitions(*stateMachine, msPostTransitions, msTransitionToEligibleCoords, *movementTransToCoordAndType);
      }

    // Build priority transitions
    buildPriorityTransitions(*stateMachine, postPriorityActionTransitions, *transitionToEligibleCoords, *movementTransToCoordAndType,
                             transitionNameToActoid, PRIORITY_ACTIONS);
    buildPriorityTransitions(*stateMachine, postPriorityBonusActionTransitions, *transitionToEligibleCoords, *movementTransToCoordAndType,
                             transitionNameToActoid, PRIORITY_BONUS_ACTIONS);

    // Connect any remaining unconnected states to NOP
    auto allStates = stateMachine->getAllStates();
    for(const auto &state : allStates)
      {
        auto forwardTrans = stateMachine->getForwardTransitions(state);
        if(forwardTrans.empty())
          {
            StateId nopState = stateMachine->getNextStateId();
            stateMachine->addNewState(nopState);
            stateMachine->addTransition("nop", state, nopState);
          }
      }

    return {std::move(stateMachine), std::move(movementTransToCoordAndType), std::move(transitionToEligibleCoords)};
  }

} // namespace enc