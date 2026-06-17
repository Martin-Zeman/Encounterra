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

  bool StateMachine::triggerTransition(const std::string &transitionName)
  {
    auto &current_transitions = _states[_currentState];
    auto it = std::find_if(current_transitions.begin(), current_transitions.end(), [&](const Transition &t) { return t.name == transitionName; });

    if(it != current_transitions.end())
      {
        _currentState = it->destination;
        return true;
      }
    else
      {
        return false;
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

  std::vector<std::string> StateMachine::getAllTransitions() const
  {
    std::vector<std::string> result;
    size_t totalSize = 0;
    for(const auto &[state, transitions] : _states)
      {
        totalSize += transitions.size();
      }
    result.reserve(totalSize);

    // Add transition names
    for(const auto &[state, transitions] : _states)
      {
        for(const auto &transition : transitions)
          {
            result.push_back(transition.name);
          }
      }
    return result;
  }

  FlattenedDag StateMachine::getFlattenedDag() const
  {
    // Build the state index map. Mirrors the Python single-nop model: the start state (id 0) is index 0
    // and every terminal sink (no outgoing transitions, e.g. the nop states created in build_action_dag) is
    // collapsed onto a single nop index 1. All remaining interior states get indices starting at 2.
    std::vector<StateId> sortedStates = getAllStates();
    std::sort(sortedStates.begin(), sortedStates.end());

    auto isTerminal = [&](StateId s) {
      auto it = _states.find(s);
      return it == _states.end() || it->second.empty();
    };

    std::unordered_map<StateId, size_t> stateToIndex;
    std::unordered_map<size_t, StateId> indexToState;
    stateToIndex[0] = 0;
    indexToState[0] = 0;
    size_t nextIndex = 2; // 0 = start, 1 = nop sink
    for(StateId s : sortedStates)
      {
        if(s == 0)
          {
            continue;
          }
        if(isTerminal(s))
          {
            stateToIndex[s] = 1; // collapse all terminal/nop sinks onto the single nop index
          }
        else
          {
            stateToIndex[s] = nextIndex;
            indexToState[nextIndex] = s;
            ++nextIndex;
          }
      }
    size_t numStates = nextIndex; // start + nop + interior states

    std::unordered_map<std::string, size_t> transitionToIndex;
    std::unordered_map<size_t, std::string> indexToTransition;
    std::unordered_map<std::string, size_t> simplifiedTransitions;
    std::unordered_map<std::string, std::string> transitionToSimplified;

    std::vector<std::vector<std::pair<int, int>>> dagForward(numStates);

    for(StateId s : sortedStates)
      {
        auto it = _states.find(s);
        if(it == _states.end())
          {
            continue;
          }
        size_t srcIdx = stateToIndex[s];
        if(srcIdx == 1)
          {
            continue; // nop sink has no outgoing transitions
          }
        for(const auto &transition : it->second)
          {
            size_t tIdx;
            auto tiIt = transitionToIndex.find(transition.name);
            if(tiIt == transitionToIndex.end())
              {
                tIdx = transitionToIndex.size();
                transitionToIndex[transition.name] = tIdx;
                indexToTransition[tIdx] = transition.name;

                // Simplified name drops a trailing "_X" level designator (mirrors the Python optimization).
                std::string shortened = transition.name;
                if(shortened.size() >= 2 && shortened[shortened.size() - 2] == '_')
                  {
                    shortened = shortened.substr(0, shortened.size() - 2);
                  }
                size_t simpIdx;
                auto sIt = simplifiedTransitions.find(shortened);
                if(sIt == simplifiedTransitions.end())
                  {
                    simpIdx = simplifiedTransitions.size();
                    simplifiedTransitions[shortened] = simpIdx;
                  }
                else
                  {
                    simpIdx = sIt->second;
                  }
                transitionToSimplified[std::to_string(tIdx)] = std::to_string(simpIdx);
              }
            else
              {
                tIdx = tiIt->second;
              }
            size_t destIdx = stateToIndex.count(transition.destination) ? stateToIndex[transition.destination] : 1;
            dagForward[srcIdx].emplace_back(static_cast<int>(tIdx), static_cast<int>(destIdx));
          }
      }

    _dagForward = dagForward; // cache for dfs()
    return FlattenedDag{std::move(dagForward), numStates, std::move(indexToState), std::move(indexToTransition),
                        std::move(transitionToSimplified)};
  }

  std::vector<std::vector<std::string>> StateMachine::dfs(int currentState, size_t maxSequenceLength) const
  {
    std::vector<std::vector<std::string>> sequences;
    std::vector<std::pair<int, std::vector<std::string>>> stack;
    stack.emplace_back(currentState, std::vector<std::string>{});

    while(!stack.empty())
      {
        auto [state, sequence] = std::move(stack.back());
        stack.pop_back();

        if(state == 1) // nop sink: a complete path
          {
            sequences.push_back(std::move(sequence));
            continue;
          }

        if(state < 0 || static_cast<size_t>(state) >= _dagForward.size())
          {
            continue;
          }

        for(const auto &[transition, nextState] : _dagForward[state])
          {
            if(sequence.size() < maxSequenceLength)
              {
                std::vector<std::string> newSequence = sequence;
                newSequence.push_back(std::to_string(transition));
                stack.emplace_back(nextState, std::move(newSequence));
              }
          }
      }
    return sequences;
  }

  // auto StateMachine::getAllTransitions() const
  //   -> std::ranges::join_view<
  //     std::ranges::transform_view<std::ranges::ref_view<const std::unordered_map<StateId, std::vector<Transition>>>, std::vector<std::string>>>
  // {
  //   return std::views::join(_states | std::views::values | std::views::transform([](const auto &transitions) {
  //                             return transitions | std::views::transform([](const Transition &t) { return t.name; }) | std::ranges::to<std::vector>();
  //                           }));
  // }
}
