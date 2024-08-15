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
    Conditions conditions;
    const Combatant *initiator;
    std::optional<Effect *> effect;
    std::optional<const Combatant *> target;

    Condition(Conditions conds, const Combatant *init, Effect *eff = nullptr, const Combatant *targ = nullptr)
        : conditions(conds), initiator(init), effect(eff), target(targ)
    {}
  };

  struct ConditionWithDC : Condition
  {
    SavingThrow st;
    int dc;
    PhaseOfTurn phase;

    ConditionWithDC(Conditions conds, SavingThrow savingThrow, int difficultyClass, const Combatant *init, PhaseOfTurn phaseTurn,
                    Effect *eff = nullptr, const Combatant *targ = nullptr)
        : Condition(conds, init, eff, targ), st(savingThrow), dc(difficultyClass), phase(phaseTurn)
    {}
  };

  // Helper function to check if a condition is present in a Conditions enum
  inline bool containsCondition(Conditions conditions, Conditions condition)
  {
    return (static_cast<uint32_t>(conditions) & static_cast<uint32_t>(condition)) != 0;
  }

  void applyCondition(Combatant &combatant, const Condition &condition);
  std::optional<size_t> findConditionIndex(const std::vector<Condition> &conditionList, Conditions condition, const Combatant *initiator = nullptr);
  std::optional<Condition> removeCondition(Combatant &combatant, Conditions condition, const Combatant *initiator = nullptr);
  void removeAllConditionsOfType(Combatant &combatant, Conditions condition);
  bool isAffectedBy(const Combatant &combatant, Conditions condition);
  const Combatant *getGrappler(const Combatant &combatant);
  const Combatant *getSourceOfFrightened(const Combatant &combatant);
  const Combatant *getSourceOfParalyzed(const Combatant &combatant);
  const Combatant *getGrappled(const Combatant &combatant);
  std::optional<ConditionWithDC> needsToBreakOutOfGrapple(const Combatant &combatant);
  void breakOutOfGrapple(Combatant &combatant);
  bool isAffectedByAny(const Combatant &combatant, const std::vector<Conditions> &conditions);
  void applyDCCondition(Combatant &combatant, const ConditionWithDC &condition);
  std::optional<ConditionWithDC> removeDCCondition(Combatant &combatant, Conditions condition, const Combatant *initiator = nullptr);
}
