#pragma once

#include <memory>
#include <optional>
#include <vector>
#include <limits>
#include <blaze/Math.h>
#include "core/types.hpp"
#include "core/threat_modifiers.hpp"
#include "actions/action_types.hpp"

namespace enc
{

  enum class ActoidFlags : uint32_t
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

  class ActoidFactory;
  class Combatant;
  class Actoid;

  class BasicThreat
  {
  public:
    virtual ~BasicThreat() = default;
    virtual double calculateThreat(const Kwargs &kwargs) { return 0; };
    virtual double calculateThreatForAttack(const Combatant &attacker, Actoid *attack, const Kwargs &kwargs) { return 0; };
  };

  class DirectThreat
  {
  public:
    virtual ~DirectThreat() = default;
    virtual double calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0; };
  };

  class AoeThreat
  {
  public:
    virtual ~AoeThreat() = default;
    virtual double threatOnEnter(const Combatant &target, const Kwargs &kwargs) const { return 0; };
    virtual double threatOnMoveWithin(const Combatant &target, const Kwargs &kwargs) const { return 0; };
    virtual double threatOnStartOfTurn(const Combatant &target, const Kwargs &kwargs) const { return 0; };
    virtual double threatOnEndOfTurn(const Combatant &target, const Kwargs &kwargs) const { return 0; };
  };

  class Actoid : public BasicThreat
  {
    mutable std::optional<size_t> _cachedHash;

  public:
    explicit Actoid(ActoidFactory &factory, ActoidFlags flags = ActoidFlags::DEFAULT, AbilityType abilityType = AbilityType::NOP)
        : _factory(factory), _actoidFlags(static_cast<uint32_t>(flags)), _abilityType(abilityType)
    {}
    virtual ~Actoid() = default;
    ActoidFlags getFlags() const { return static_cast<ActoidFlags>(_actoidFlags); }
    bool hasFlag(ActoidFlags flag) const { return (_actoidFlags & static_cast<uint32_t>(flag)) != 0; }
    AbilityType getAbilityType() const;
    ActoidFactory &getFactory() { return _factory; }
    virtual std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                         const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>())
      = 0;
    virtual std::string toString() const = 0;

    virtual bool equals(const Actoid &other) const = 0;

    size_t getHash() const
    {
      if(!_cachedHash)
        {
          _cachedHash = hash();
        }
      return *_cachedHash;
    }

  protected:
    ActoidFactory &_factory;
    uint32_t _actoidFlags;
    AbilityType _abilityType;

    virtual size_t hash() const = 0;
  };

  class AttackThreatModifier : public Actoid
  {
  protected:
    AttackThreatModifier(ActoidFactory &factory, ActoidFlags flags = ActoidFlags::DEFAULT) : Actoid(factory, flags | ActoidFlags::IS_ATTACK_MODIFIER)
    {}

  public:
    virtual ~AttackThreatModifier() = default;

    virtual double calculateThreatForAttack(const Combatant &attacker, Actoid *attack, const Kwargs &kwargs) = 0;
  };

  enum class FactoryFlags : uint32_t
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

  class Resource;

  class ActoidFactory
  {
  public:
    std::string _name;
    std::string _abilityName;

  protected:
    std::weak_ptr<Combatant> _combatant;
    uint32_t _flags;
    AbilityType _abilityType;

  public:
    ActoidFactory(std::string name, std::string abilityName, const std::shared_ptr<Combatant>& combatant, AbilityType abilityType)
        : _name(name), _abilityName(abilityName), _combatant(combatant), _flags(static_cast<uint32_t>(FactoryFlags::DEFAULT)),
          _abilityType(abilityType)
    {}
    void setFlag(FactoryFlags flag) { _flags |= static_cast<uint32_t>(flag); }
    void clearFlag(FactoryFlags flag) { _flags &= ~static_cast<uint32_t>(flag); }
    bool hasFlag(FactoryFlags flag) const { return (_flags & static_cast<uint32_t>(flag)) != 0; }
    uint32_t getFlags() const { return _flags; }
    std::weak_ptr<Combatant> getCombatant() { return _combatant; }
    void setCombatant(const std::shared_ptr<Combatant>& combatant) { _combatant = combatant; }
    virtual ~ActoidFactory() = default;
    virtual std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) = 0;
    virtual std::shared_ptr<Actoid> create(void *target) = 0;
    virtual std::optional<Resource *> getResource() = 0;
    AbilityType getAbilityType() const { return _abilityType; }
  };

  inline AbilityType Actoid::getAbilityType() const { return _factory.getAbilityType(); }

  class DirectThreatFactory : public ActoidFactory
  {
  protected:
    DirectThreatFactory(const std::string &name, const std::string &abilityName, const std::shared_ptr<Combatant>& combatant, AbilityType abilityType)
        : ActoidFactory(name, abilityName, combatant, abilityType)
    {
      setFlag(FactoryFlags::IS_DIRECT_THREAT);
    }
    virtual double calculateMaxThreat() const = 0;

  public:
    virtual int getRange() const = 0;
    virtual double calculateThreatToTarget(const Combatant& target, const Kwargs &kwargs) const = 0;
    virtual double calculateThreatToTargetDelta(const Combatant& target, const ThreatModifiers &modifiers) const { return 0; }; //  Not always needed
  };

  /**
   * A factory that modifies the user and the factories they have at their disposal
   */
  class TransformerFactory : public BasicThreat, public ActoidFactory
  {
  public:
    explicit TransformerFactory(const std::string &name, const std::string &abilityName, const std::shared_ptr<Combatant>& combatant, AbilityType abilityType)
        : ActoidFactory(name, abilityName, combatant, abilityType)
    {}

    virtual ~TransformerFactory() = default;
  };
}