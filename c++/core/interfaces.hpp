#pragma once

#include <memory>
#include <vector>
#include "core/types.hpp"

namespace enc
{

  enum class ActoidFlags
  {
    DEFAULT = 1 << 0,
    IS_ATTACK_LIKE = 1 << 1,
    IS_ATTACK_MODIFIER = 1 << 2,
    IS_MOVEMENT = 1 << 3,
    IS_SPELL = 1 << 4,
    IS_DASH = 1 << 5,
    IS_HIDE = 1 << 6,
    IS_GET_UP_FROM_PRONE = 1 << 7,
    IS_BREAK_GRAPPLE = 1 << 8,
    IS_ACTION_ENABLER = 1 << 9,
    LOCATION_INDEPENDENT = 1 << 10,
    IS_PRIORITY = 1 << 11
  };

  inline ActoidFlags operator|(ActoidFlags a, ActoidFlags b) { return static_cast<ActoidFlags>(static_cast<int>(a) | static_cast<int>(b)); }

  class Actoid
  {
  public:
    explicit Actoid(ActoidFlags flags = ActoidFlags::DEFAULT) : actoid_flags(flags) {}
    virtual ~Actoid() = default;
    ActoidFlags getFlags() const { return actoid_flags; }

  private:
    ActoidFlags actoid_flags;
  };

  enum class FactoryFlags
  {
    DEFAULT = 1 << 0,
    IS_ATTACK_LIKE = 1 << 1,
    IS_HASTE_ELIGIBLE_ATTACK = 1 << 2,
    IS_MELEE = 1 << 3,
    USES_DEX = 1 << 4,
    IS_RANGED = 1 << 5,
    IS_DIRECT_THREAT = 1 << 6,
    IS_ATTACK_MODIFIER = 1 << 7,
    IS_RECHARGE = 1 << 8,
    DEX_SAVE_APPLIES = 1 << 9,
    TARGETS_COORDS = 1 << 10,
    TARGETS_SELF = 1 << 11,
    PREVENT_ENDLESS_RECURSION = 1 << 12,
    TRANSITIONS_TO_WILDSHAPE = 1 << 13,
    TWO_HANDED = 1 << 14,
    IS_PRECISION = 1 << 15
  };

  inline FactoryFlags operator|(FactoryFlags a, FactoryFlags b) { return static_cast<FactoryFlags>(static_cast<int>(a) | static_cast<int>(b)); }

  // class ICombatant{};
  class Combatant;

  class ActoidFactory
  {
  protected:
    uint32_t _flags;

  public:
    ActoidFactory() : _flags(static_cast<uint32_t>(FactoryFlags::DEFAULT)) {}
    void setFlag(FactoryFlags flag) { _flags |= static_cast<uint32_t>(flag); }
    void clearFlag(FactoryFlags flag) { _flags &= ~static_cast<uint32_t>(flag); }
    bool hasFlag(FactoryFlags flag) const { return (_flags & static_cast<uint32_t>(flag)) != 0; }
    virtual ~ActoidFactory() = default;
    virtual std::vector<std::shared_ptr<Actoid>> createAll(void *previous_action_in_dag = nullptr) = 0;
    virtual std::shared_ptr<Actoid> create(void *target) = 0;
  };

  class DirectThreatFactory : public ActoidFactory
  {
  protected:
    DirectThreatFactory() : ActoidFactory() { setFlag(FactoryFlags::IS_DIRECT_THREAT); }
    virtual double calculateThreatToTarget(Combatant *target, const Kwargs& kwargs) = 0;
    virtual double calculateThreatToTargetDelta(Combatant *target /*Add modifiers*/) = 0;
    virtual double calculateMaxThreat() = 0;
  };
}