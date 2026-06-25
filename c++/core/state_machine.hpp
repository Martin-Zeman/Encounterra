#pragma once

#include <iostream>
#include <unordered_map>
#include <vector>
#include <string>
#include <utility>
#include <algorithm>
#include <stdexcept>
#include <functional>
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
    std::vector<int> transitionToSimplified; // [transitionIndex] -> simplifiedIndex (dense, indices are sequential)
    std::vector<Actoid *> indexToActoid; // [transitionIndex] -> owning actoid (nullptr for the None sentinel)
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

    // Actoid-aware overload: records the action's identity alongside a descriptive string name (used only for the
    // flattened-DAG debug/simplification path and the None sentinel). Transition identity is the Actoid pointer.
    void addTransition(Actoid* action, const std::string& name, StateId origin, StateId dest);

    // Actoid-identity transition API. Transitions are matched by pointer identity (the same Actoid* registered when the
    // transition was added). The derived string name (action->toString(), or "None") is still stored for the
    // flattened-DAG path.
    void addTransition(Actoid* action, StateId origin, StateId dest);

    void removeTransition(Actoid* action, StateId origin);

    void removeTransitionFromAllStates(Actoid* action);

    bool triggerTransition(Actoid* action);

    // Forward transitions from a state / the current state, and all transitions, keyed by Actoid identity.
    std::vector<std::pair<Actoid*, StateId>> getForwardActoidTransitions(StateId state) const;

    std::vector<std::pair<Actoid*, StateId>> getCurrentForwardTransitions() const;

    std::vector<Actoid*> getAllActoidTransitions() const;

    void reset();

    std::vector<StateId> getAllStates() const;

    std::vector<StateId> toposort() const;

    // Build the flattened DAG representation (start->0, nop sinks->1) and cache it for dfs().
    FlattenedDag getFlattenedDag() const;

    // Depth-first enumeration of all transition-index sequences from currentState to a nop sink (index 1).
    // Each returned sequence element is a transition index. Mirrors numba_functions.dfs.
    std::vector<std::vector<int>> dfs(int currentState, size_t maxSequenceLength) const;

    // Streaming variant of dfs(): invokes onLeaf(path) for each complete path (path == the shared transition-index
    // buffer) instead of collecting every sequence into a vector. Lets callers deduplicate/aggregate on the fly
    // without materializing the (potentially tens of millions of) full sequence list. The buffer passed to onLeaf
    // is only valid for the duration of the call; copy it if it needs to outlive the callback.
    void dfs(int currentState, size_t maxSequenceLength,
             const std::function<void(const std::vector<int> &)> &onLeaf) const;

  private:
    // Backtracking helper for dfs(): walks the DAG with a single shared `path` buffer (push/pop) so each
    // complete path is materialized exactly once instead of copying the prefix at every branch. Each complete
    // path is handed to onLeaf.
    void dfsRecurse(int state, size_t maxSequenceLength, std::vector<int> &path,
                    const std::function<void(const std::vector<int> &)> &onLeaf) const;

  public:
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
