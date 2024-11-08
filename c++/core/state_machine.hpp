#pragma once

#include <iostream>
#include <unordered_map>
#include <vector>
#include <algorithm>
#include <stdexcept>

namespace enc {

class StateMachine {
private:
    using StateId = int;

    struct Transition {
        std::string name;
        StateId origin;
        StateId destination;
    };

    std::unordered_map<StateId, std::vector<Transition>> states;
    StateId current_state;
    StateId next_available_id;

public:
    StateMachine() : current_state(0), next_available_id(1) {
        addNewState(0); // Initial state
        addNewState(-1); // NOP state
    }

    void addNewState(StateId id) {
        if (states.find(id) != states.end()) {
            throw std::runtime_error("State ID already exists");
        }
        states[id] = {};
        next_available_id = std::max(next_available_id, id + 1);
    }

    StateId getNextStateId() {
        return next_available_id++;
    }

    void removeState(StateId state_id) {
        if (state_id != 0 && state_id != 1) {
            states.erase(state_id);
            for (auto& [_, transitions] : states) {
                transitions.erase(
                    std::remove_if(transitions.begin(), transitions.end(),
                        [&](const Transition& t) { return t.destination == state_id; }),
                    transitions.end()
                );
            }
        }
    }

    StateId getCurrentState() const {
        return current_state;
    }

    std::vector<std::string> getAvailableTransitionsInCurrentState() const {
        return getAvailableTransitionsInState(current_state);
    }

    std::unordered_map<StateId, std::vector<std::string>> getTransitionsInAllStates() const {
        std::unordered_map<StateId, std::vector<std::string>> result;
        for (const auto& [state, transitions] : states) {
            result[state] = getAvailableTransitionsInState(state);
        }
        return result;
    }

    std::vector<std::string> getAvailableTransitionsInState(StateId state) const {
        std::vector<std::string> result;
        if (states.find(state) != states.end()) {
            for (const auto& transition : states.at(state)) {
                result.push_back(transition.name);
            }
        }
        return result;
    }

    void addTransition(const std::string& name, StateId origin, StateId dest) {
        if (states.find(origin) != states.end() && states.find(dest) != states.end()) {
            states[origin].push_back({name, origin, dest});
        } else {
            throw std::runtime_error("Origin or destination state does not exist");
        }
    }

    void removeTransition(const std::string& transition_name, StateId origin) {
        if (states.find(origin) != states.end()) {
            auto& transitions = states[origin];
            transitions.erase(
                std::remove_if(transitions.begin(), transitions.end(),
                    [&](const Transition& t) { return t.name == transition_name; }),
                transitions.end()
            );
        }
    }

    void reset() {
        current_state = 0;
    }

    void triggerTransition(const std::string& transition_name) {
        auto& current_transitions = states[current_state];
        auto it = std::find_if(current_transitions.begin(), current_transitions.end(),
            [&](const Transition& t) { return t.name == transition_name; });
        
        if (it != current_transitions.end()) {
            current_state = it->destination;
        } else {
            throw std::runtime_error("Invalid transition for current state");
        }
    }

    std::vector<StateId> getAllStates() const {
        std::vector<StateId> state_ids;
        state_ids.reserve(states.size());
        for (const auto& [state, _] : states) {
            state_ids.push_back(state);
        }
        return state_ids;
    }
};

}
