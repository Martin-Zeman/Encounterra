#pragma once

#include <vector>
#include <memory>
#include <queue>
#include <shared_mutex>
#include <stdexcept>
#include "core/types.hpp"
#include "core/interfaces.hpp"

namespace enc
{
  using StateId = int;

  constexpr StateId INITIAL_STATE = 0;
  constexpr StateId TERMINAL_STATE = 1;

  class StateMachine
  {
  private:
    struct Transition
    {
      Actoid * action;
      StateId destination;
    };

    std::vector<std::vector<Transition>> _states; // Using vectors with StateId as index for better cache locality
    std::vector<std::vector<StateId>> _dependencies;
    StateId _currentState;
    StateId _nextAvailableId;
    std::unordered_set<Actoid *> _ownedActoids; // Keep track of unique Actoids to delete them in destructor

    mutable std::vector<StateId> _cachedToposort;
    mutable bool _isDagDirty;

  public:
    StateMachine();

    StateMachine(const StateMachine &other);

    ~StateMachine();

    void addNewState(StateId id);

    StateId getNextStateId();

    StateId getNumStates();

    // void removeState(StateId stateId);

    void addTransition(Actoid * action, StateId origin, StateId dest);

    void removeTransition(Actoid * action, StateId origin);

    void removeTransitionFromAllStates(Actoid * action);

    std::vector<std::pair<Actoid *, StateId>> getForwardTransitions(StateId state) const;

    std::vector<std::pair<Actoid *, StateId>> getCurrentForwardTransitions() const;

    std::vector<StateId> toposort() const;

    bool triggerTransition(Actoid * action);

    std::vector<Actoid *> getAllTransitions() const;

    std::vector<StateId> getAllStates() const;

    StateId getCurrentState() const;

    void reset();

  private:
    std::vector<StateId> computeToposort() const;

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
      if(to < _dependencies.size())
        {
          auto &deps = _dependencies[to];
          deps.erase(std::remove(deps.begin(), deps.end(), from), deps.end());
        }
    }
  };

} // namespace enc
