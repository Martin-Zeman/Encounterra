#pragma once

#include <vector>

namespace enc
{

  class ActoidFactory;

  /**
   * Lightweight finite state machine that gates multiattack sequences. Faithful port of the way Python's
   * StateMachineTemplate is used for a combatant's `attack_fsm` (simulator/combatants/*.build_attack_fms).
   *
   * States are plain integers; the start state is 0 and the terminal "nop" sink is NOP. Transitions are keyed by
   * the attack's ActoidFactory identity (the same pointer registered on the combatant). A single-attack combatant
   * builds 0 -> NOP transitions (so one attack then nothing); a multiattack combatant chains interior states so a
   * second, complementary attack remains available after the first is spent.
   */
  class AttackFsm
  {
  public:
    static constexpr int START = 0;
    static constexpr int NOP = -1;

    void addTransition(const ActoidFactory *factory, int origin, int destination)
    {
      _edges.push_back({factory, origin, destination});
    }

    // Python is_0(): true while the FSM has not advanced past its start state.
    bool isAtStart() const { return _currentState == START; }

    // Whether the given factory labels an outgoing transition from the current state.
    bool hasAvailableTransition(const ActoidFactory *factory) const
    {
      for(const auto &edge : _edges)
        if(edge.origin == _currentState && edge.factory == factory)
          return true;
      return false;
    }

    // Follow the transition labeled by the given factory from the current state. No-op if no such transition exists
    // (e.g. combatants that never built an attack FSM), keeping single-attack behaviour unchanged.
    void trigger(const ActoidFactory *factory)
    {
      for(const auto &edge : _edges)
        if(edge.origin == _currentState && edge.factory == factory)
          {
            _currentState = edge.destination;
            return;
          }
    }

    void reset() { _currentState = START; }

    int getState() const { return _currentState; }
    void setState(int state) { _currentState = state; }

  private:
    struct Edge
    {
      const ActoidFactory *factory;
      int origin;
      int destination;
    };

    std::vector<Edge> _edges;
    int _currentState = START;
  };

} // namespace enc
