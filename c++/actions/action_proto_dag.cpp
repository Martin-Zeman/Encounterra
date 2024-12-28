#include "actions/action_proto_dag.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include "core/feasibility.hpp"
#include <functional>

namespace enc
{

  std::vector<std::shared_ptr<ActoidFactory>> getAllFeasibleActionFactories(Combatant *combatant, int depth)
  {
    std::vector<std::shared_ptr<ActoidFactory>> allActionFactories;

    auto feasibleActionFactories = getFeasibleFactories(combatant->getActionFactoriesConst(), combatant);
    allActionFactories.insert(allActionFactories.end(), feasibleActionFactories.begin(), feasibleActionFactories.end());

    if(depth > 1)
      {
        auto feasibleBonusActionFactories = getFeasibleFactories(combatant->getBonusActionFactoriesConst(), combatant);
        // Filter out Misty Step
        feasibleBonusActionFactories.erase(std::remove_if(feasibleBonusActionFactories.begin(), feasibleBonusActionFactories.end(),
                                                          [](const auto &factory) { return factory->getAbilityType() == AbilityType::MISTY_STEP; }),
                                           feasibleBonusActionFactories.end());
        allActionFactories.insert(allActionFactories.end(), feasibleBonusActionFactories.begin(), feasibleBonusActionFactories.end());
      }
    else
      {
        auto feasibleBonusActionFactories = getFeasibleFactories(combatant->getBonusActionFactoriesConst(), combatant);
        allActionFactories.insert(allActionFactories.end(), feasibleBonusActionFactories.begin(), feasibleBonusActionFactories.end());
      }

    auto feasibleHasteActionFactories = getFeasibleFactories(combatant->getHasteActionFactoriesConst(), combatant);
    allActionFactories.insert(allActionFactories.end(), feasibleHasteActionFactories.begin(), feasibleHasteActionFactories.end());

    return allActionFactories;
  }

  StateMachine generateProtoDAG(Combatant *combatant)
  {
    StateMachine fsm;
    std::unordered_map<ActionFootprint, StateId, ActionFootprintHash> stateFootprintToStateId;
    std::unordered_set<ActionFootprint, ActionFootprintHash> visited;

    /**
     * Recursively builds the action Finite State Machine (FSM) for a given combatant using depth-first search.
     * 
     *  This function traverses through all feasible action combinations, considering both actions and bonus actions,
     *  at each depth level. It creates states in the FSM for each unique combination of actions, connects states with transitions,
     *  and handles special cases like Action Enablers and wildshape actions.
     * 
     *  @param subject: The combatant for whom the FSM is being built.
     *  @param previousStateId: The id of the previous state in the FSM.
     *  @param depth: The current depth in the action decision tree.
     *  @param actionTaken: The action taken to reach the current state, if any.
     *  @param previousFas: Prevents endless recursion in case of 3 consecutive attacks of the same type
     *  @return: None. The function works by side-effect, modifying the FSM directly.
     * 
     *  Note: This function assumes that it's called within the context of `generate_proto_dag`
     *  where the FSM and other necessary structures are initialized.
     */
    std::function<void(Combatant *, StateId, int, std::shared_ptr<Actoid>, const ActionFootprint *)> dfs;

    dfs = [&](Combatant *subject, StateId previousStateId, int depth, std::shared_ptr<Actoid> actionTaken, const ActionFootprint *previousFas) {
      auto fafs = getAllFeasibleActionFactories(subject, depth);
      std::vector<std::shared_ptr<Actoid>> fas;
      for(const auto &factory : fafs)
        {
          auto actions = factory->createAll();
          fas.insert(fas.end(), actions.begin(), actions.end());
        }

      ActionFootprint stateFootprint{fas};
      if(previousFas && stateFootprint == *previousFas)
        {
          // Protection against three consecutive attacks
          stateFootprint.actionHashes.insert(std::make_shared<DummyActoid>(*new DummyActoidFactory(), std::to_string(depth))->getHash());
        }

      if(actionTaken)
        {
          if(fas.empty())
            {
              // No more actions -> connect to the nop state
              fsm.addTransition(actionTaken, previousStateId, -1);
              return;
            }
        }

      if(visited.find(stateFootprint) == visited.end())
        {
          visited.insert(stateFootprint);
          StateId currStateId = fsm.getNextStateId();
          stateFootprintToStateId[stateFootprint] = currStateId;

          if(actionTaken)
            {
              fsm.addNewState(currStateId);
              fsm.addTransition(actionTaken, previousStateId, currStateId);
            }

          for(const auto &fa : fas)
            {
              auto exportedResources = subject->exportResources();
              useResources(subject, *fa);

              auto &battleMap = BattleMap::getInstance();
              battleMap.withCombatantWildshapeReplacement(
                *fa, subject, battleMap.getCombatantCoordinates(*subject).getRoot(), [&](bool actionEnablerUsed) {
                  if(actionEnablerUsed)
                    {
                      auto newFafs = getAllFeasibleActionFactories(fa->getFactory().getCombatant(), depth);
                      std::vector<std::shared_ptr<Actoid>> newActions;
                      for(const auto &factory : newFafs)
                        {
                          auto actions = factory->createAll(actionTaken.get());
                          newActions.insert(newActions.end(), actions.begin(), actions.end());
                        }
                      dfs(fa->getFactory().getCombatant(), currStateId, depth + 1, fa, &stateFootprint);
                    }
                  else if(fa->hasFlag(ActoidFlags::IS_ACTION_ENABLER))
                    {
                      std::vector<std::shared_ptr<Actoid>> newActions;
                      for(const auto &factory : fafs)
                        {
                          auto actions = factory->createAll(fa.get());
                          newActions.insert(newActions.end(), actions.begin(), actions.end());
                        }
                      dfs(subject, currStateId, depth + 1, fa, &stateFootprint);
                    }
                  else
                    {
                      dfs(subject, currStateId, depth + 1, fa, &stateFootprint);
                    }
                });

              subject->importResources(exportedResources);
            }
        }
      else
        {
          // State already exists, just hook up the transition
          if(actionTaken)
            {
              fsm.addTransition(actionTaken, previousStateId, stateFootprintToStateId[stateFootprint]);
            }
        }
    };

    // Initialize with first level of actions
    auto fafs = getAllFeasibleActionFactories(combatant, 0);
    std::vector<std::shared_ptr<Actoid>> initialActions;
    for(const auto &factory : fafs)
      {
        auto actions = factory->createAll();
        initialActions.insert(initialActions.end(), actions.begin(), actions.end());
      }

    dfs(combatant, 0, 0, nullptr, nullptr);

    return fsm;
  }

  StateMachine generateWildshapeProtoDAG(Combatant* combatant) {
    StateMachine fsm;
    std::unordered_map<ActionFootprint, StateId, ActionFootprintHash> stateFootprintToStateId;
    std::unordered_set<ActionFootprint, ActionFootprintHash> visited;

    std::function<void(Combatant*, StateId, int, std::shared_ptr<Actoid>)> dfs;
    
    dfs = [&](Combatant* subject, 
              StateId previousStateId,
              int depth,
              std::shared_ptr<Actoid> actionTaken) {
        
        auto fafs = getAllFeasibleActionFactories(subject, depth);
        std::vector<std::shared_ptr<Actoid>> fas;
        for (const auto& factory : fafs) {
            auto actions = factory->createAll();
            fas.insert(fas.end(), actions.begin(), actions.end());
        }

        ActionFootprint stateFootprint{fas};

        if (actionTaken) {
            if (fas.empty()) {
                fsm.addTransition(actionTaken, previousStateId, -1);  // Connect to NOP state
                return;
            }
        }

        if (visited.find(stateFootprint) == visited.end()) {
            visited.insert(stateFootprint);
            StateId currStateId = fsm.getNextStateId();
            stateFootprintToStateId[stateFootprint] = currStateId;

            if (actionTaken) {
                fsm.addNewState(currStateId);
                fsm.addTransition(actionTaken, previousStateId, currStateId);
            }

            for (const auto& fa : fas) {
                // Skip non-Wildshape actions at depth 0
                if(!actionTaken && (fa->getAbilityType() != AbilityType::WILDSHAPE || fa->getAbilityType() != AbilityType::MOON_WILDSHAPE))
                {
                  continue;
                }

                auto exportedResources = subject->exportResources();
                useResources(subject, *fa);

                auto& battleMap = BattleMap::getInstance();
                battleMap.withCombatantWildshapeReplacement(*fa, subject, 
                    battleMap.getCombatantCoordinates(*subject).getRoot(),
                    [&](bool actionEnablerUsed) {
                        if (actionEnablerUsed) {
                            auto newFafs = getAllFeasibleActionFactories(fa->getFactory().getCombatant(), depth);
                            std::vector<std::shared_ptr<Actoid>> newActions;
                            for (const auto& factory : newFafs) {
                                auto actions = factory->createAll(actionTaken.get());
                                newActions.insert(newActions.end(), actions.begin(), actions.end());
                            }
                            dfs(fa->getFactory().getCombatant(), currStateId, depth, fa);
                        }
                        else if (fa->hasFlag(ActoidFlags::IS_ACTION_ENABLER)) {
                            std::vector<std::shared_ptr<Actoid>> newActions;
                            for (const auto& factory : fafs) {
                                auto actions = factory->createAll(fa.get());
                                newActions.insert(newActions.end(), actions.begin(), actions.end());
                            }
                            dfs(subject, currStateId, depth, fa);
                        }
                        else {
                            dfs(subject, currStateId, depth, fa);
                        }
                    });

                subject->importResources(exportedResources);
            }
        } else {
            if (actionTaken) {
                fsm.addTransition(actionTaken, previousStateId, 
                                stateFootprintToStateId[stateFootprint]);
            }
        }
    };

    // Initialize with first level of actions
    auto fafs = getAllFeasibleActionFactories(combatant, 0);
    std::vector<std::shared_ptr<Actoid>> initialActions;
    for (const auto& factory : fafs) {
        auto actions = factory->createAll();
        initialActions.insert(initialActions.end(), actions.begin(), actions.end());
    }

    dfs(combatant, 0, 0, nullptr);

    return fsm;
}

} // namespace enc
