#pragma once

#include "actions/action_types.hpp"
#include "actions/melee_attack.hpp"
#include "actions/ranged_attack.hpp"

namespace enc
{

  // Type trait to map AbilityType to factory type
  template <AbilityType> struct AbilityFactoryMap
  {
    using type = void; // Default case for unsupported types
  };

  // Specializations for each ability type
  template <> struct AbilityFactoryMap<AbilityType::MELEE_ATTACK>
  {
    using type = MeleeAttackFactory;
  };

  template <> struct AbilityFactoryMap<AbilityType::RANGED_ATTACK>
  {
    using type = RangedAttackFactory;
  };

  // ... other specializations here

} // namespace enc
