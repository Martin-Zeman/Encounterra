#pragma once
#include <vector>
#include <memory>
#include <utility>
#include <unordered_set>
#include "core/interfaces.hpp"
#include "core/state_machine.hpp"

namespace enc
{
  class Combatant;

  struct ActionFootprint
  {
    std::unordered_set<size_t> actionHashes;
    // Optionally keep the actions if we need them later
    // std::vector<Actoid *> actions;

    explicit ActionFootprint(const std::vector<Actoid *> &actoids)// : actions(actoids) // Optional
    {
      for(const auto &actoid : actoids)
        {
          actionHashes.insert(actoid->getHash());
        }
    }

    bool operator==(const ActionFootprint &other) const { return actionHashes == other.actionHashes; }
  };

  struct ActionFootprintHash
  {
    size_t operator()(const ActionFootprint &fp) const
    {
      size_t hash = 0;
      for(auto h : fp.actionHashes)
        {
          hash ^= h + 0x9e3779b9 + (hash << 6) + (hash >> 2);
        }
      return hash;
    }
  };

  std::vector<ActoidFactory *> getAllFeasibleActionFactories(const Combatant &combatant, int depth);

  /**
   * Finds the path through the FSM which represents all possible movements and actions for a combatant.
   * The FSM construction takes advantage of the fact that as a result of the DFS traversal, the actions
   * in generated sequences are coordianate-wise. Therefore, we can process the sequences by these
   * coord-wise blocks and call as_if_combatant_position once per block.
   *
   * @param combatant The combatant for whom the FSM is modeled
   * @return The state machine representing all possible action combinations
   */
  StateMachine generateProtoFSM(Combatant &combatant);

  /**
   * A special variation of generateProtoFSM which generates an action FSM where only Wildshape
   * actions are allowed as the first action.
   *
   * @param combatant The combatant for whom the FSM is modeled
   * @return The state machine representing all possible action combinations starting with Wildshape
   */
  StateMachine generateWildshapeProtoFSM(Combatant &combatant);
}