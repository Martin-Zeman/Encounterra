#pragma once

#include "actions/action_types.hpp"
#include "actions/melee_attack.hpp"
#include "actions/ranged_attack.hpp"
#include "core/types.hpp"
#include <unordered_map>
#include <string>
#include <memory>
#include <utility>

namespace enc
{

  struct PriorityActionInfo
  {
    std::string prefix;
    MovementThreatType threatType;
  };

  // const std::unordered_map<AbilityType, PriorityActionInfo> PRIORITY_ACTIONS
  //   = {{AbilityType::DODGE, {"do_", MovementThreatType::DODGED}}, {AbilityType::DISENGAGE, {"di_", MovementThreatType::DISENGAGED}}};

  // const std::unordered_map<AbilityType, PriorityActionInfo> PRIORITY_BONUS_ACTIONS
  //   = {{AbilityType::CUNNING_DISENGAGE, {"cdi_", MovementThreatType::DISENGAGED}},
  //      {AbilityType::TOTEM_RAGE, {"m_", MovementThreatType::STANDARD}},
  //      {AbilityType::RAGE, {"m_", MovementThreatType::STANDARD}},
  //      {AbilityType::AGGRESSIVE, {"m_", MovementThreatType::STANDARD}}};

  // Factory mappings TODO This May not be needed with my new concept
  // using ActionFactoryCreator = std::unique_ptr<ActionFactory> (*)(/* params */);

  // const std::unordered_map<AbilityType, ActionFactoryCreator> TO_FACTORY = {
  //   {AbilityType::MELEE_ATTACK, &MeleeAttackFactory::create},
  //   {AbilityType::RANGED_ATTACK, &RangedAttackFactory::create},
  //   // ... other mappings
  // };

  // Conversion maps
  const std::unordered_map<AbilityType, AbilityType> TO_QUICKENED = {
    {AbilityType::FIREBALL, AbilityType::QUICKENED_FIREBALL},
    {AbilityType::FIREBOLT, AbilityType::QUICKENED_FIREBOLT},
    {AbilityType::CHAOSBOLT, AbilityType::QUICKENED_CHAOSBOLT},
    {AbilityType::HASTE, AbilityType::QUICKENED_HASTE},
    {AbilityType::HUNGER_OF_HADAR, AbilityType::QUICKENED_HUNGER_OF_HADAR},
    {AbilityType::SPIKE_GROWTH, AbilityType::QUICKENED_SPIKE_GROWTH},
    {AbilityType::CLOUD_OF_DAGGERS, AbilityType::QUICKENED_CLOUD_OF_DAGGERS},
    {AbilityType::SCORCHING_RAY, AbilityType::QUICKENED_SCORCHING_RAY},
    {AbilityType::FAERIE_FIRE, AbilityType::QUICKENED_FAERIE_FIRE},
    {AbilityType::BLESS, AbilityType::QUICKENED_BLESS},
    {AbilityType::FLAMING_SPHERE, AbilityType::QUICKENED_FLAMING_SPHERE},
    {AbilityType::HOLD_PERSON, AbilityType::QUICKENED_HOLD_PERSON},
    {AbilityType::RAY_OF_FROST, AbilityType::QUICKENED_RAY_OF_FROST},
  };

  const std::unordered_map<AbilityType, AbilityType> TO_TWINNED = {
    {AbilityType::FIREBOLT, AbilityType::TWINNED_FIREBOLT},
    {AbilityType::HASTE, AbilityType::TWINNED_HASTE},
  };

  const std::unordered_map<AbilityType, AbilityType> TO_HASTED = {
    {AbilityType::MELEE_ATTACK, AbilityType::HASTE_MELEE_ATTACK},
    {AbilityType::RANGED_ATTACK, AbilityType::HASTE_RANGED_ATTACK},
    {AbilityType::DASH, AbilityType::HASTE_DASH},
    {AbilityType::DISENGAGE, AbilityType::HASTE_DISENGAGE},
    {AbilityType::HIDE, AbilityType::HASTE_HIDE},
    {AbilityType::PRE_SWALLOW_BITE, AbilityType::HASTE_PRE_SWALLOW_BITE},
    {AbilityType::BITE_AND_SWALLOW, AbilityType::HASTE_BITE_AND_SWALLOW},
    {AbilityType::GRAPPLE_ATTACK, AbilityType::HASTE_GRAPPLE_ATTACK},
    {AbilityType::GRAPPLE, AbilityType::HASTE_GRAPPLE},
    {AbilityType::VAMPIRIC_BITE, AbilityType::HASTE_VAMPIRIC_BITE},
    {AbilityType::PARALYZING_MELEE_ATTACK, AbilityType::HASTE_PARALYZING_MELEE_ATTACK},
  };

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
