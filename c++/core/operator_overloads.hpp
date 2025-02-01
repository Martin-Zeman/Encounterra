#pragma once
#include "core/combatant.hpp"

namespace enc
{
  inline bool operator==(const Combatant &lhs, Combatant *rhs) { return lhs._instanceId == rhs->_instanceId; }

  inline bool operator==(const Combatant &lhs, const Combatant &rhs) { return lhs._instanceId == rhs._instanceId; }

  inline bool operator==(Combatant *lhs, const Combatant &rhs) { return lhs->_instanceId == rhs._instanceId; }

  inline bool operator==(const Combatant &lhs, Combatant &rhs) { return lhs._instanceId == rhs._instanceId; }

  inline bool operator==(Combatant &lhs, const Combatant &rhs) { return lhs._instanceId == rhs._instanceId; }

  inline bool operator!=(const Combatant &lhs, Combatant *rhs) { return !(lhs == rhs); }

  inline bool operator!=(const Combatant &lhs, const Combatant &rhs) { return !(lhs == rhs); }

  inline bool operator!=(Combatant *lhs, const Combatant &rhs) { return !(lhs == rhs); }

  inline bool operator!=(const Combatant &lhs, Combatant &rhs) { return !(lhs == rhs); }

  inline bool operator!=(Combatant &lhs, const Combatant &rhs) { return !(lhs == rhs); }
} // namespace enc
