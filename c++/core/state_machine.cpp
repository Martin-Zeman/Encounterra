#include "core/state_machine.hpp"
#include <queue>

namespace enc
{

  StateMachine::StateMachine() : _currentState(0), _nextAvailableId(1), _isDagDirty(true)
  {
    addNewState(0);  // Initial state
    addNewState(-1); // NOP state
  }

  void StateMachine::addNewState(StateId id)
  {
    if(_states.find(id) != _states.end())
      {
        throw std::runtime_error("State ID already exists");
      }
    _states[id] = {};
    _nextAvailableId = std::max(_nextAvailableId, id + 1);
  }

  StateId StateMachine::getNextStateId() { return _nextAvailableId++; }

  void StateMachine::removeState(StateId state_id)
  {
    if(state_id != 0 && state_id != 1)
      {
        // Remove all transitions to/from this state
        _states.erase(state_id);
        _dependencies.erase(state_id);

        // Remove transitions to this state from other states
        for(auto &[_, transitions] : _states)
          {
            transitions.erase(std::remove_if(transitions.begin(), transitions.end(), [&](const Transition &t) { return t.destination == state_id; }),
                              transitions.end());
          }

        // Remove dependencies involving this state
        for(auto &[_, deps] : _dependencies)
          {
            deps.erase(std::remove(deps.begin(), deps.end(), state_id), deps.end());
          }

        _isDagDirty = true;
      }
  }

  StateId StateMachine::getCurrentState() const { return _currentState; }

  // std::vector<std::string> StateMachine::getAvailableTransitionsInCurrentState() const { return getAvailableTransitionsInState(_currentState); }

  // std::unordered_map<StateId, std::vector<std::string>> StateMachine::getTransitionsInAllStates() const
  // {
  //   std::unordered_map<StateId, std::vector<std::string>> result;
  //   for(const auto &[state, transitions] : _states)
  //     {
  //       result[state] = getAvailableTransitionsInState(state);
  //     }
  //   return result;
  // }

  // std::vector<std::string> StateMachine::getAvailableTransitionsInState(StateId state) const
  // {
  //   std::vector<std::string> result;
  //   if(_states.find(state) != _states.end())
  //     {
  //       for(const auto &transition : _states.at(state))
  //         {
  //           result.push_back(transition.name);
  //         }
  //     }
  //   return result;
  // }

  void StateMachine::addTransition(const std::string &name, StateId origin, StateId dest)
  {
    if(_states.find(origin) != _states.end() && _states.find(dest) != _states.end())
      {
        _states[origin].push_back({name, origin, dest});
        addDependency(origin, dest);
        _isDagDirty = true;
      }
    else
      {
        throw std::runtime_error("Origin or destination state does not exist");
      }
  }

  void StateMachine::removeTransition(const std::string &transition_name, StateId origin)
  {
    if(_states.find(origin) != _states.end())
      {
        auto &transitions = _states[origin];
        auto it = std::find_if(transitions.begin(), transitions.end(), [&](const Transition &t) { return t.name == transition_name; });

        if(it != transitions.end())
          {
            removeDependency(origin, it->destination);
            transitions.erase(it);
            _isDagDirty = true;
          }
      }
  }

  void StateMachine::reset() { _currentState = 0; }

  void StateMachine::triggerTransition(const std::string &transitionName)
  {
    auto &current_transitions = _states[_currentState];
    auto it = std::find_if(current_transitions.begin(), current_transitions.end(), [&](const Transition &t) { return t.name == transitionName; });

    if(it != current_transitions.end())
      {
        _currentState = it->destination;
      }
    else
      {
        throw std::runtime_error("Invalid transition for current state");
      }
  }

  std::vector<StateId> StateMachine::getAllStates() const
  {
    std::vector<StateId> stateIds;
    stateIds.reserve(_states.size());
    for(const auto &[state, _] : _states)
      {
        stateIds.push_back(state);
      }
    return stateIds;
  }

  std::vector<StateId> StateMachine::toposort() const
  {
    if(_isDagDirty)
      {
        _cachedToposort = computeToposort();
        _isDagDirty = false;
      }
    return _cachedToposort;
  }

  std::vector<StateId> StateMachine::computeToposort() const
  {
    std::vector<StateId> result;
    result.reserve(_states.size());

    std::unordered_map<StateId, int> inDegree;
    std::queue<StateId> zeroInDegree;

    // Initialize in-degrees using stored dependencies
    for(const auto &[state, _] : _states)
      {
        auto dep_it = _dependencies.find(state);
        inDegree[state] = (dep_it != _dependencies.end()) ? dep_it->second.size() : 0;
        if(inDegree[state] == 0)
          {
            zeroInDegree.push(state);
          }
      }

    while(!zeroInDegree.empty())
      {
        StateId current = zeroInDegree.front();
        zeroInDegree.pop();
        result.push_back(current);

        auto state_it = _states.find(current);
        if(state_it != _states.end())
          {
            for(const auto &transition : state_it->second)
              {
                StateId dest = transition.destination;
                if(--inDegree[dest] == 0)
                  {
                    zeroInDegree.push(dest);
                  }
              }
          }
      }

    if(result.size() != _states.size())
      {
        throw std::runtime_error("Graph contains a cycle");
      }

    return result;
  }

  StateId StateMachine::getTransitionDestination(StateId state, const std::string &transitionName) const
  {
    if(_states.find(state) != _states.end())
      {
        for(const auto &transition : _states.at(state))
          {
            if(transition.name == transitionName)
              {
                return transition.destination;
              }
          }
      }
    throw std::runtime_error("Transition not found");
  }

  std::vector<std::pair<std::string, StateId>> StateMachine::getForwardTransitions(StateId state) const
  {
    std::vector<std::pair<std::string, StateId>> result;
    if(_states.find(state) != _states.end())
      {
        for(const auto &transition : _states.at(state))
          {
            result.emplace_back(transition.name, transition.destination);
          }
      }
    return result;
  }
}
