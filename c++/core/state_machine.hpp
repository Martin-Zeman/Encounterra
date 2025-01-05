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
      std::shared_ptr<Actoid> action;
      StateId destination;
    };

    std::vector<std::vector<Transition>> _states; // Using vectors with StateId as index for better cache locality
    std::vector<std::vector<StateId>> _dependencies;
    StateId _currentState;
    StateId _nextAvailableId;

    mutable std::vector<StateId> _cachedToposort;
    mutable bool _isDagDirty;

  public:
    StateMachine();

    void addNewState(StateId id);

    StateId getNextStateId();

    StateId getNumStates();

    // void removeState(StateId stateId);

    void addTransition(std::shared_ptr<Actoid> action, StateId origin, StateId dest);

    void removeTransition(std::shared_ptr<Actoid> action, StateId origin);

    void removeTransitionFromAllStates(std::shared_ptr<Actoid> action);

    std::vector<std::pair<std::shared_ptr<Actoid>, StateId>> getForwardTransitions(StateId state) const;

    std::vector<std::pair<std::shared_ptr<Actoid>, StateId>> getCurrentForwardTransitions() const;

    std::vector<StateId> toposort() const;

    bool triggerTransition(std::shared_ptr<Actoid> action);

    std::vector<std::shared_ptr<Actoid>> getAllTransitions() const;

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
