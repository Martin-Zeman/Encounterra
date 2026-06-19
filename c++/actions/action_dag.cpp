#include <algorithm>
#include "actions/action_dag.hpp"
#include "actions/movement.hpp"
#include "actions/dummy_actoid.hpp"
#include "actions/dummy_actoid_factory.hpp"
#include "core/combatant.hpp"
#include "core/state_machine.hpp"
#include "core/battle_map.hpp"

namespace enc
{

  const std::unordered_map<AbilityType, PriorityActionInfo> PRIORITY_ACTIONS
    = {{AbilityType::DODGE, {"do_", MovementThreatType::DODGED}}, {AbilityType::DISENGAGE, {"di_", MovementThreatType::DISENGAGED}}};

  const std::unordered_map<AbilityType, PriorityActionInfo> PRIORITY_BONUS_ACTIONS
    = {{AbilityType::CUNNING_DISENGAGE, {"cdi_", MovementThreatType::DISENGAGED}},
       {AbilityType::TOTEM_RAGE, {"m_", MovementThreatType::STANDARD}},
       {AbilityType::RAGE, {"m_", MovementThreatType::STANDARD}},
       {AbilityType::AGGRESSIVE, {"m_", MovementThreatType::STANDARD}}};

  namespace
  {
    // Creates a synthetic movement actoid carrying the target coordinate, owns it in the pool and returns the raw pointer.
    Actoid *makeMovementActoid(const Coord &coord, MovementThreatType type, std::vector<std::shared_ptr<Actoid>> &pool, ActoidFactory &factory)
    {
      bool incursAOO = (type == MovementThreatType::STANDARD);
      auto actoid = std::make_shared<MovementIncrement>(coord, incursAOO, factory);
      Actoid *raw = actoid.get();
      pool.push_back(std::move(actoid));
      return raw;
    }

    // Creates a synthetic sentinel actoid (e.g. "dummy"/"nop"), owns it in the pool and returns the raw pointer.
    Actoid *makeSentinelActoid(const std::string &name, std::vector<std::shared_ptr<Actoid>> &pool)
    {
      auto actoid = std::make_shared<DummyActoid>(DummyActoidFactory::getInstance(), name);
      Actoid *raw = actoid.get();
      pool.push_back(std::move(actoid));
      return raw;
    }
  } // namespace

  std::unordered_map<Actoid *, std::vector<std::pair<Actoid *, StateId>>>
  getPostTransitionsOfPriorityTransitions(StateMachine &stateMachine, const std::unordered_map<AbilityType, PriorityActionInfo> &priorityActions)
  {
    std::unordered_map<Actoid *, std::vector<std::pair<Actoid *, StateId>>> postPriorityTransitions;

    for(const auto &[action, dest] : stateMachine.getForwardActoidTransitions(0))
      {
        if(!action)
          {
            continue;
          }
        if(priorityActions.find(action->getAbilityType()) != priorityActions.end())
          {
            std::vector<std::pair<Actoid *, StateId>> postTransitions;

            if(stateMachine.triggerTransition(action))
              {
                for(const auto &ft : stateMachine.getCurrentForwardTransitions())
                  {
                    if(ft.first && !ft.first->hasFlag(ActoidFlags::IS_PRIORITY))
                      {
                        postTransitions.push_back(ft);
                      }
                  }
                stateMachine.reset();
              }
            postPriorityTransitions[action] = postTransitions;
          }
      }
    return postPriorityTransitions;
  }

  PostTransitionResult getPostTransitionsOfAllPriorityTransitions(StateMachine &protoStateMachine)
  {
    auto postPriorityActionTransitions = getPostTransitionsOfPriorityTransitions(protoStateMachine, PRIORITY_ACTIONS);
    auto postPriorityBonusActionTransitions = getPostTransitionsOfPriorityTransitions(protoStateMachine, PRIORITY_BONUS_ACTIONS);

    for(const auto &[priorityAction, _] : postPriorityActionTransitions)
      {
        protoStateMachine.removeTransitionFromAllStates(priorityAction);
      }

    for(const auto &[priorityAction, _] : postPriorityBonusActionTransitions)
      {
        protoStateMachine.removeTransitionFromAllStates(priorityAction);
      }

    return {postPriorityActionTransitions, postPriorityBonusActionTransitions};
  }

  MovementStatesResult createMovementStates(StateMachine &stateMachine, const TransitionToEligibleCoords &transitionToEligibleCoords)
  {
    std::unordered_map<Coord, std::unordered_set<Actoid *>> coordToEligibleTransitions;

    for(const auto &[transition, coords] : transitionToEligibleCoords)
      {
        for(const auto &coord : coords)
          {
            coordToEligibleTransitions[coord].insert(transition);
          }
      }

    std::unordered_map<std::unordered_set<Actoid *>, StateId, ActoidSetHash, ActoidSetEqual> eligibleTransitionsToState;

    for(const auto &[coord, transitions] : coordToEligibleTransitions)
      {
        if(eligibleTransitionsToState.find(transitions) == eligibleTransitionsToState.end())
          {
            StateId newState = stateMachine.getNextStateId();
            eligibleTransitionsToState[transitions] = newState;
            stateMachine.addNewState(newState);
          }
      }

    return {eligibleTransitionsToState, coordToEligibleTransitions};
  }

  std::vector<std::pair<Actoid *, StateId>> getPostMistyStepTransitions(StateMachine &stateMachine)
  {
    auto initialTransitions = stateMachine.getForwardActoidTransitions(0);
    auto msIt = std::find_if(initialTransitions.begin(), initialTransitions.end(),
                             [](const auto &t) { return t.first && t.first->getAbilityType() == AbilityType::MISTY_STEP; });

    if(msIt == initialTransitions.end())
      {
        return {};
      }

    std::vector<std::pair<Actoid *, StateId>> msPostTransitions;
    if(stateMachine.triggerTransition(msIt->first))
      {
        for(const auto &pt : stateMachine.getCurrentForwardTransitions())
          {
            if(pt.first && !pt.first->hasFlag(ActoidFlags::IS_PRIORITY))
              {
                msPostTransitions.push_back(pt);
              }
          }
        stateMachine.reset();
      }

    stateMachine.removeTransition(msIt->first, 0);
    return msPostTransitions;
  }

  void buildMistyStepTransitions(StateMachine &stateMachine, const std::vector<std::pair<Actoid *, StateId>> &msPostTransitions,
                                 const TransitionToEligibleCoords &transitionToEligibleCoords, MovementTransToCoordAndType &movementTransToCoordAndType,
                                 std::vector<std::shared_ptr<Actoid>> &syntheticActoids, ActoidFactory &movementFactory)
  {
    auto [eligibleTransitionsToState, coordToEligibleTransitions] = createMovementStates(stateMachine, transitionToEligibleCoords);

    for(const auto &[action, destState] : msPostTransitions)
      {
        auto it = transitionToEligibleCoords.find(action);
        if(it == transitionToEligibleCoords.end())
          {
            continue;
          }
        for(const auto &coord : it->second)
          {
            const auto &transitions = coordToEligibleTransitions.at(coord);
            StateId postMsState = eligibleTransitionsToState.at(transitions);

            Actoid *msAction = makeMovementActoid(coord, MovementThreatType::MISTY_STEPPED, syntheticActoids, movementFactory);
            movementTransToCoordAndType[msAction] = {coord, MovementThreatType::MISTY_STEPPED};

            stateMachine.addTransition(msAction, 0, postMsState);
            stateMachine.addTransition(action, postMsState, destState);
          }
      }
  }

  void buildPriorityTransitions(StateMachine &stateMachine,
                                const std::unordered_map<Actoid *, std::vector<std::pair<Actoid *, StateId>>> &postPriorityTransitions,
                                const TransitionToEligibleCoords &transitionToEligibleCoords, MovementTransToCoordAndType &movementTransToCoordAndType,
                                const std::unordered_map<AbilityType, PriorityActionInfo> &priorityActionDict,
                                std::vector<std::shared_ptr<Actoid>> &syntheticActoids, ActoidFactory &movementFactory)
  {
    auto [eligibleTransitionsToState, coordToEligibleTransitions] = createMovementStates(stateMachine, transitionToEligibleCoords);

    std::vector<StateId> newlyAddedStates;

    for(const auto &[priorityAction, postTransitions] : postPriorityTransitions)
      {
        if(postTransitions.empty())
          {
            StateId nopState = stateMachine.getNextStateId();
            stateMachine.addNewState(nopState);
            stateMachine.addTransition(priorityAction, 0, nopState);
            continue;
          }

        const auto &priorityInfo = priorityActionDict.at(priorityAction->getAbilityType());

        StateId newPrioState = stateMachine.getNextStateId();
        stateMachine.addNewState(newPrioState);
        newlyAddedStates.push_back(newPrioState);
        stateMachine.addTransition(priorityAction, 0, newPrioState);

        for(const auto &[postAction, destState] : postTransitions)
          {
            auto it = transitionToEligibleCoords.find(postAction);
            if(it == transitionToEligibleCoords.end())
              {
                continue;
              }
            for(const auto &coord : it->second)
              {
                const auto &transitions = coordToEligibleTransitions.at(coord);
                StateId postPtState = eligibleTransitionsToState.at(transitions);

                Actoid *moveAction = makeMovementActoid(coord, priorityInfo.threatType, syntheticActoids, movementFactory);
                movementTransToCoordAndType[moveAction] = {coord, priorityInfo.threatType};

                stateMachine.addTransition(moveAction, newPrioState, postPtState);
                stateMachine.addTransition(postAction, postPtState, destState);
              }
          }
      }

    for(const auto &newState : newlyAddedStates)
      {
        if(stateMachine.getForwardActoidTransitions(newState).empty())
          {
            StateId nopState = stateMachine.getNextStateId();
            stateMachine.addNewState(nopState);
            Actoid *dummy = makeSentinelActoid("dummy", syntheticActoids);
            stateMachine.addTransition(dummy, newState, nopState);
          }
      }
  }

  // In the pythonv version this is in action_selector.py 
  ActionStateMachineResult buildActionStateMachine(Combatant *combatant, const StateMachine &protoStateMachine,
                                                   const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    // Work on a private copy of the proto FSM: getPostTransitions* / getPostMistyStep mutate it.
    StateMachine protoCopy = protoStateMachine;

    // Precompute the visibility of every reachable coord towards each enemy, mirroring Python's build_action_dag.
    BattleMap::getInstance().calcVisibilityDictForAllCoords(combatant, shortestPaths);

    auto [postPriorityActionTransitions, postPriorityBonusActionTransitions] = getPostTransitionsOfAllPriorityTransitions(protoCopy);

    std::vector<std::pair<Actoid *, StateId>> msPostTransitions;
    {
      auto initialTransitions = protoCopy.getForwardActoidTransitions(0);
      bool hasMistyStep = std::any_of(initialTransitions.begin(), initialTransitions.end(),
                                      [](const auto &t) { return t.first && t.first->getAbilityType() == AbilityType::MISTY_STEP; });
      if(hasMistyStep)
        {
          msPostTransitions = getPostMistyStepTransitions(protoCopy);
        }
    }

    ActionStateMachineResult result;
    result.stateMachine = std::make_unique<StateMachine>(protoCopy);
    result.movementTransToCoordAndType = std::make_unique<MovementTransToCoordAndType>();
    result.transitionToEligibleCoords = std::make_unique<TransitionToEligibleCoords>();
    result.movementFactory = std::make_shared<MovementFactory>(combatant, CoordVector{}, AbilityType::STANDARD_MOVEMENT);

    StateMachine &stateMachine = *result.stateMachine;
    MovementTransToCoordAndType &movementTransToCoordAndType = *result.movementTransToCoordAndType;
    TransitionToEligibleCoords &transitionToEligibleCoords = *result.transitionToEligibleCoords;

    auto allTransitions = stateMachine.getAllActoidTransitions();
    if(allTransitions.empty())
      {
        return result;
      }

    // Compute eligible coordinates for each (unique) action transition.
    for(Actoid *action : allTransitions)
      {
        if(!action || dynamic_cast<DummyActoid *>(action))
          {
            continue;
          }
        if(transitionToEligibleCoords.find(action) != transitionToEligibleCoords.end())
          {
            continue;
          }
        try
          {
            auto eligibleCoords = action->getEligibleCoords(distances, shortestPaths);
            if(eligibleCoords)
              {
                transitionToEligibleCoords[action] = *eligibleCoords;
              }
          }
        catch(const std::out_of_range &)
          {
            continue;
          }
      }

    // Remove transitions without eligible coordinates from the initial state.
    for(const auto &[action, dest] : stateMachine.getForwardActoidTransitions(0))
      {
        if(!action || dynamic_cast<DummyActoid *>(action))
          {
            continue;
          }
        auto it = transitionToEligibleCoords.find(action);
        if(it == transitionToEligibleCoords.end() || it->second.empty())
          {
            stateMachine.removeTransition(action, 0);
          }
      }

    // Prepend STANDARD movement to each (non-priority, non-Misty-Step) action transition originating at state 0.
    {
      auto [eligibleTransitionsToState, coordToEligibleTransitions] = createMovementStates(stateMachine, transitionToEligibleCoords);

      // One shared movement actoid per target coord (mirrors Python's per-coord "m_(x,y)" transition name).
      std::unordered_map<Coord, Actoid *> coordToMovementActoid;

      for(const auto &[action, coords] : transitionToEligibleCoords)
        {
          if(!action || action->getAbilityType() == AbilityType::MISTY_STEP)
            {
              continue;
            }

          // Resolve the action's original destination from state 0 in the proto FSM.
          StateId dest = 0;
          bool found = false;
          for(const auto &[protoAction, protoDest] : protoCopy.getForwardActoidTransitions(0))
            {
              if(protoAction == action)
                {
                  dest = protoDest;
                  found = true;
                  break;
                }
            }
          if(!found)
            {
              continue; // Action originates from a state other than 0.
            }

          for(const auto &coord : coords)
            {
              const auto &transitions = coordToEligibleTransitions.at(coord);
              StateId movementState = eligibleTransitionsToState.at(transitions);

              auto mit = coordToMovementActoid.find(coord);
              if(mit == coordToMovementActoid.end())
                {
                  Actoid *moveAction = makeMovementActoid(coord, MovementThreatType::STANDARD, result.syntheticActoids, *result.movementFactory);
                  coordToMovementActoid[coord] = moveAction;
                  movementTransToCoordAndType[moveAction] = {coord, MovementThreatType::STANDARD};
                  stateMachine.addTransition(moveAction, 0, movementState);
                }

              stateMachine.addTransition(action, movementState, dest);
            }

          stateMachine.removeTransition(action, 0); // Remove the original direct transition.
        }
    }

    // Misty Step transitions (preserves the original behaviour of supplying an empty eligible-coords map here).
    if(!msPostTransitions.empty())
      {
        TransitionToEligibleCoords msTransitionToEligibleCoords;
        buildMistyStepTransitions(stateMachine, msPostTransitions, msTransitionToEligibleCoords, movementTransToCoordAndType, result.syntheticActoids,
                                  *result.movementFactory);
      }

    buildPriorityTransitions(stateMachine, postPriorityActionTransitions, transitionToEligibleCoords, movementTransToCoordAndType, PRIORITY_ACTIONS,
                             result.syntheticActoids, *result.movementFactory);
    buildPriorityTransitions(stateMachine, postPriorityBonusActionTransitions, transitionToEligibleCoords, movementTransToCoordAndType,
                             PRIORITY_BONUS_ACTIONS, result.syntheticActoids, *result.movementFactory);

    // Connect any remaining unconnected states to a fresh NOP sink.
    for(const auto &state : stateMachine.getAllStates())
      {
        if(stateMachine.getForwardActoidTransitions(state).empty())
          {
            StateId nopState = stateMachine.getNextStateId();
            stateMachine.addNewState(nopState);
            Actoid *nop = makeSentinelActoid("nop", result.syntheticActoids);
            stateMachine.addTransition(nop, state, nopState);
          }
      }

    return result;
  }

} // namespace enc
