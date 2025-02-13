#include <vector>
#include <memory>
#include <queue>
#include <shared_mutex>
#include <stdexcept>
#include "core/state_machine.hpp"
#include "core/types.hpp"

namespace enc
{

  StateMachine::StateMachine() : _currentState(INITIAL_STATE), _nextAvailableId(2), _isDagDirty(true)
  {
    // Ensure space for initial and NOP states
    _states.resize(2);
    _dependencies.resize(2);
  }

  StateMachine::StateMachine(const StateMachine &other)
      : _states(other._states.size()), _dependencies(other._dependencies), _currentState(other._currentState),
        _nextAvailableId(other._nextAvailableId), _cachedToposort(other._cachedToposort), _isDagDirty(other._isDagDirty)
  {
    // Create a map of old actoid pointers to their new copies
    std::unordered_map<Actoid *, Actoid *> actoidMap;

    // First, create copies of all unique Actoids
    for(Actoid *oldActoid : other._ownedActoids)
      {
        Actoid *newActoid = oldActoid->clone();
        actoidMap[oldActoid] = newActoid;
        _ownedActoids.insert(newActoid);
      }

    // Now copy the transitions using the new Actoid pointers
    for(size_t i = 0; i < other._states.size(); ++i)
      {
        _states[i].reserve(other._states[i].size());
        for(const Transition &oldTransition : other._states[i])
          {
            Actoid *newAction = actoidMap[oldTransition.action];
            _states[i].push_back({newAction, oldTransition.destination});
          }
      }
  }

  StateMachine::~StateMachine()
  {
    for(Actoid *action : _ownedActoids)
      {
        delete action;
      }
  }

  void StateMachine::releaseActoidOwnership(Actoid *actoid)
  {
    if(_ownedActoids.contains(actoid))
      {
        _ownedActoids.erase(actoid);
      }
  }

  // For multiple actoids:
  void StateMachine::releaseActoidOwnership(const std::vector<Actoid *> &actoids)
  {
    for(Actoid *actoid : actoids)
      {
        releaseActoidOwnership(actoid);
      }
  }

  void StateMachine::addNewState(StateId id)
  {
    if(id == _states.size())
      {
        _states.resize(id + 1);
        _dependencies.resize(id + 1);
      }
    else if(id > _states.size())
      {
        throw std::runtime_error("State ID must be the next available ID");
      }
    else
      {
        throw std::runtime_error("State already exists");
      }
    _nextAvailableId = std::max(_nextAvailableId, id + 1);
  }

  StateId StateMachine::getNextStateId() { return _nextAvailableId++; }

  StateId StateMachine::getNumStates() { return _states.size(); }

  // void StateMachine::removeState(StateId stateId)
  // {
  //   if(stateId == INITIAL_STATE || stateId == TERMINAL_STATE)
  //   {
  //     return; // Protect initial and NOP states
  //   }

  //   if(stateId < _states.size())
  //     {
  //       // Clear transitions from this state
  //       _states[stateId].clear();
  //       _dependencies[stateId].clear();

  //       // Remove transitions to this state and dependencies
  //       for(size_t i = 0; i < _states.size(); ++i)
  //         {
  //           auto &transitions = _states[i];
  //           transitions.erase(
  //             std::remove_if(transitions.begin(), transitions.end(), [stateId](const Transition &t) { return t.destination == stateId; }),
  //             transitions.end());

  //           auto &deps = _dependencies[i];
  //           deps.erase(std::remove(deps.begin(), deps.end(), stateId), deps.end());
  //         }
  //       _isDagDirty = true;
  //     }
  // }

  void StateMachine::addTransition(Actoid *action, StateId origin, StateId dest)
  {
    if(origin >= _states.size() || dest >= _states.size())
      {
        throw std::runtime_error("Origin or destination state does not exist");
      }
    _states[origin].push_back({action, dest});
    addDependency(origin, dest);
    _isDagDirty = true;
    _ownedActoids.insert(action);
  }

  void StateMachine::removeTransition(Actoid *action, StateId origin)
  {
    if(origin < _states.size())
      {
        auto &transitions = _states[origin];
        auto it = std::find_if(transitions.begin(), transitions.end(), [&](const Transition &t) { return t.action == action; });

        if(it != transitions.end())
          {
            removeDependency(origin, it->destination);
            transitions.erase(it);
            _isDagDirty = true;
          }
      }
  }

  void StateMachine::removeTransitionFromAllStates(Actoid *action)
  {
    for(StateId originState = 0; originState < _states.size(); ++originState)
      {
        auto &transitions = _states[originState];
        auto it = std::find_if(transitions.begin(), transitions.end(), [&](const Transition &t) { return t.action == action; });

        if(it != transitions.end())
          {
            removeDependency(originState, it->destination);
            transitions.erase(it);
            _isDagDirty = true;
          }
      }
  }

  std::vector<std::pair<Actoid *, StateId>> StateMachine::getForwardTransitions(StateId state) const
  {
    if(state >= _states.size())
      return {};

    std::vector<std::pair<Actoid *, StateId>> result;
    result.reserve(_states[state].size());
    for(const auto &transition : _states[state])
      {
        result.emplace_back(transition.action, transition.destination);
      }
    return result;
  }

  std::vector<std::pair<Actoid *, StateId>> StateMachine::getCurrentForwardTransitions() const
  {
    std::vector<std::pair<Actoid *, StateId>> result;
    result.reserve(_states[_currentState].size());
    for(const auto &transition : _states[_currentState])
      {
        result.emplace_back(transition.action, transition.destination);
      }
    return result;
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

  bool StateMachine::triggerTransition(Actoid *action)
  {
    auto &current_transitions = _states[_currentState];
    auto it = std::find_if(current_transitions.begin(), current_transitions.end(), [&](const Transition &t) { return t.action == action; });

    if(it != current_transitions.end())
      {
        _currentState = it->destination;
        return true;
      }
    return false;
  }

  std::vector<Actoid *> StateMachine::getAllTransitions() const
  {
    std::vector<Actoid *> result;
    for(const auto &transitions : _states)
      {
        for(const auto &transition : transitions)
          {
            result.push_back(transition.action);
          }
      }
    return result;
  }

  std::vector<StateId> StateMachine::getAllStates() const
  {
    std::vector<StateId> result;
    for(StateId i = 0; i < _states.size(); ++i)
      {
        if(!_states[i].empty() || !_dependencies[i].empty())
          {
            result.push_back(i);
          }
      }
    return result;
  }

  StateId StateMachine::getCurrentState() const { return _currentState; }

  void StateMachine::reset() { _currentState = 0; }

  std::vector<StateId> StateMachine::computeToposort() const
  {
    std::vector<StateId> result;
    result.reserve(_states.size());

    std::vector<int> inDegree(_states.size(), 0);
    std::queue<StateId> zeroInDegree;

    // Calculate in-degrees
    for(size_t i = 0; i < _dependencies.size(); ++i)
      {
        inDegree[i] = _dependencies[i].size();
        if(inDegree[i] == 0)
          {
            zeroInDegree.push(i);
          }
      }

    while(!zeroInDegree.empty())
      {
        StateId current = zeroInDegree.front();
        zeroInDegree.pop();
        result.push_back(current);

        for(const auto &transition : _states[current])
          {
            StateId dest = transition.destination;
            if(--inDegree[dest] == 0)
              {
                zeroInDegree.push(dest);
              }
          }
      }

    if(result.size() != _states.size())
      {
        throw std::runtime_error("Graph contains a cycle");
      }

    return result;
  }
} // namespace enc
