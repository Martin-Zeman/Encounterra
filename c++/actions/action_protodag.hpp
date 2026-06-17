#pragma once

#include <memory>
#include <vector>
#include "core/state_machine.hpp"
#include "core/interfaces.hpp"
#include "actions/action_dag.hpp"

namespace enc
{
  /**
   * Result of building a combatant's proto action DAG.
   * Mirrors the (fsm, transition_name_to_action) tuple returned by Python generate_proto_dag().
   */
  struct ProtoDagResult
  {
    StateMachine fsm;
    TransitionNameToActoid transitionNameToActoid;
  };

  /**
   * Collects all feasible (action / bonus action / haste action) factories for a combatant, excluding Misty Step
   * (resolved separately). Mirrors Python get_all_feasible_action_factories().
   */
  std::vector<std::shared_ptr<ActoidFactory>> getAllFeasibleActionFactories(Combatant *combatant, int depth);

  /**
   * Builds a combatant-specific FSM expressing all possible (bonus) action combinations for their turn.
   * Mirrors Python generate_proto_dag().
   */
  ProtoDagResult generateProtoDag(Combatant *combatant);
}
