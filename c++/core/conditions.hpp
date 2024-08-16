#pragma once

#include <cstdint>
#include <vector>
#include <optional>
#include "misc.hpp"
#include "effects/effect.hpp"

namespace enc
{
  class Combatant;

  enum class Conditions : uint32_t
  {
    NONE = 0,
    BLINDED = 1 << 0,
    CHARMED = 1 << 1,
    DEAFENED = 1 << 2,
    FRIGHTENED = 1 << 3,
    GRAPPLED = 1 << 4,
    INCAPACITATED = 1 << 5,
    INVISIBLE = 1 << 6,
    PARALYZED = 1 << 7,
    PETRIFIED = 1 << 8,
    POISONED = 1 << 9,
    PRONE = 1 << 10,
    RESTRAINED = 1 << 11,
    STUNNED = 1 << 12,
    UNCONSCIOUS = 1 << 13,
    SWALLOWED = 1 << 14,
    GRAPPLING = 1 << 15,
    AWAKENED_BY_DMG = 1 << 16,
    CAN_BE_SHAKEN_AWAKE = 1 << 17
  };

  // Operator overloading for bitwise operations on Conditions
  inline Conditions operator|(Conditions a, Conditions b) { return static_cast<Conditions>(static_cast<uint32_t>(a) | static_cast<uint32_t>(b)); }

  inline Conditions &operator|=(Conditions &a, Conditions b) { return a = a | b; }

  struct Condition
  {
    Conditions conditionComposite;
    Combatant *initiator;
    std::optional<Effect *> effect;
    std::optional<Combatant *> target;

    Condition(Conditions conds, Combatant *init, Effect *eff = nullptr, Combatant *targ = nullptr)
        : conditionComposite(conds), initiator(init), effect(eff), target(targ)
    {}
  };

  struct ConditionWithDC : Condition
  {
    SavingThrow st;
    int dc;
    PhaseOfTurn phase;

    ConditionWithDC(Conditions conds, SavingThrow savingThrow, int difficultyClass, Combatant *init, PhaseOfTurn phaseTurn,
                    Effect *eff = nullptr, Combatant *targ = nullptr)
        : Condition(conds, init, eff, targ), st(savingThrow), dc(difficultyClass), phase(phaseTurn)
    {}
  };

  // Helper function to check if a condition is present in a Conditions enum
  inline bool containsCondition(Conditions conditions, Conditions condition)
  {
    return (static_cast<uint32_t>(conditions) & static_cast<uint32_t>(condition)) != 0;
  }

}
