#pragma once

#include <iostream>
#include <unordered_map>
#include <vector>
#include <algorithm>
#include <stdexcept>

namespace enc {

  using StateId = int;

  class StateMachine
  {
  private:

    struct Transition {
        std::string name;
        StateId origin;
        StateId destination;
    };

    std::unordered_map<StateId, std::vector<Transition>> _states;
    std::unordered_map<StateId, std::vector<StateId>> _dependencies;
    StateId _currentState;
    StateId _nextAvailableId;
    mutable bool _isDagDirty;
    mutable std::vector<StateId> _cachedToposort;

public:
    StateMachine();

    void addNewState(StateId id);

    StateId getNextStateId();

    void removeState(StateId stateId);

    StateId getCurrentState() const;

    // std::vector<std::string> getAvailableTransitionsInCurrentState() const;

    // std::unordered_map<StateId, std::vector<std::string>> getTransitionsInAllStates() const;

    // std::vector<std::string> getAvailableTransitionsInState(StateId state) const;

    void addTransition(const std::string& name, StateId origin, StateId dest);

    void removeTransition(const std::string& transitionName, StateId origin);

    void reset();

    void triggerTransition(const std::string& transitionName);

    std::vector<StateId> getAllStates() const;

    std::vector<StateId> toposort() const;

    // Get the destination state for a given transition from a given state
    StateId getTransitionDestination(StateId state, const std::string &transitionName) const;

    // Get all forward transitions from a state (as pairs of transition name and destination state)
    std::vector<std::pair<std::string, StateId>> getForwardTransitions(StateId state) const;

    std::vector<std::string> getAllTransitions() const;

  private:
    inline void addDependency(StateId from, StateId to)
    {
      auto &deps = _dependencies[to];
      if(std::find(deps.begin(), deps.end(), from) == deps.end())
        {
          deps.push_back(from);
        }
    }

    inline void removeDependency(StateId from, StateId to)
    {
      auto &deps = _dependencies[to];
      deps.erase(std::remove(deps.begin(), deps.end(), from), deps.end());
    }

    std::vector<StateId> computeToposort() const;
};

}
