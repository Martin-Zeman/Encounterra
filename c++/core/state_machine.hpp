#pragma once

#include <iostream>
#include <unordered_map>
#include <vector>
#include <string>
#include <utility>
#include <algorithm>
#include <stdexcept>
// #include <ranges>

namespace enc {

  using StateId = int;

  class Actoid;

  /**
   * Flattened, index-based representation of the action DAG used by the DFS traversal in action selection.
   * The start state maps to index 0 and every terminal/nop sink is collapsed onto index 1.
   * (Counterpart of Python's StateMachineTemplate.get_numba_compatible_data(), minus the numba specifics.)
   */
  struct FlattenedDag {
    std::vector<std::vector<std::pair<int, int>>> dagForward; // [stateIndex] -> list of (transitionIndex, nextStateIndex)
    size_t numStates;
    std::unordered_map<size_t, StateId> indexToState;
    std::unordered_map<size_t, std::string> indexToTransition;
    std::unordered_map<std::string, std::string> transitionToSimplified; // transitionIndex-as-string -> simplifiedIndex-as-string
    std::unordered_map<size_t, Actoid *> indexToActoid; // transitionIndex -> owning actoid (nullptr for the None sentinel)
  };

  class StateMachine
  {
  private:

    struct Transition {
        std::string name;
        Actoid *action; // identity of the action this transition represents (nullptr for the None sentinel)
        StateId origin;
        StateId destination;
    };

    std::unordered_map<StateId, std::vector<Transition>> _states;
    std::unordered_map<StateId, std::vector<StateId>> _dependencies;
    StateId _currentState;
    StateId _nextAvailableId;
    mutable bool _isDagDirty;
    mutable std::vector<StateId> _cachedToposort;
    mutable std::vector<std::vector<std::pair<int, int>>> _dagForward; // cache populated by getNumbaCompatibleData(), consumed by dfs()

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

    // Actoid-aware overload: records the action's identity alongside its (legacy) string name so downstream consumers
    // can be migrated off string transition names incrementally.
    void addTransition(Actoid* action, const std::string& name, StateId origin, StateId dest);

    void removeTransition(const std::string& transitionName, StateId origin);

    void reset();

    bool triggerTransition(const std::string& transitionName);

    std::vector<StateId> getAllStates() const;

    std::vector<StateId> toposort() const;

    // Get the destination state for a given transition from a given state
    StateId getTransitionDestination(StateId state, const std::string &transitionName) const;

    // Get all forward transitions from a state (as pairs of transition name and destination state)
    std::vector<std::pair<std::string, StateId>> getForwardTransitions(StateId state) const;

    std::vector<std::string> getAllTransitions() const;

    // Build the flattened DAG representation (start->0, nop sinks->1) and cache it for dfs().
    FlattenedDag getFlattenedDag() const;

    // Depth-first enumeration of all transition-index sequences from currentState to a nop sink (index 1).
    // Each returned sequence element is a transition index encoded as a string. Mirrors numba_functions.dfs.
    std::vector<std::vector<std::string>> dfs(int currentState, size_t maxSequenceLength) const;
    // auto getAllTransitions() const
    //   -> std::ranges::join_view<
    //     std::ranges::transform_view<std::ranges::ref_view<const std::unordered_map<StateId, std::vector<Transition>>>, std::vector<std::string>>>;

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
