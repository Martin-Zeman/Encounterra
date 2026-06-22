#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  // Ray of Frost (2024) — a cantrip frost ray. We model only the damage component (as the threat
  // engine does for Python's RayOfFrost, whose threat is pure mean damage); the 2024 "Speed reduced
  // by 10 ft." rider is intentionally omitted as it has no bearing on the projected threat value.
  class RayOfFrostFactory : public DirectThreatFactory
  {
    friend class RayOfFrost;

  public:
    static constexpr int level = 0;
    static constexpr SpellRange range = SpellRange::FEET_60;
    static constexpr SpellTarget target = SpellTarget::ONE_CREATURE;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr DamageType dmgType = DamageType::Cold;

    static Die getDmgDice(int level)
    {
      if(level >= 1 && level <= 4)
        {
          return {1, 8};
        }
      else if(level >= 5 && level <= 10)
        {
          return {2, 8};
        }
      else if(level >= 11 && level <= 16)
        {
          return {3, 8};
        }
      else if(level >= 17)
        {
          return {4, 8};
        }
      else
        {
          throw std::runtime_error("Incorrect caster level of Ray of Frost");
        }
    }

    RayOfFrostFactory(int toHit, AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<Combatant *> getEligibleTargets() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;

    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

  private:
    int _toHit;
    Resource *_resource;
    Die _dmgDice;
  };

  class RayOfFrost : public Actoid, public DirectThreat
  {
  public:
    RayOfFrost(Combatant &target, const RayOfFrostFactory &factory, RollType rollType = RollType::STRAIGHT)
        : Actoid(const_cast<RayOfFrostFactory &>(factory), ActoidFlags::IS_SPELL | ActoidFlags::IS_ATTACK_LIKE, factory._abilityType), _target(target),
          _factory(factory), _rollType(rollType)
    {}

    std::string toString() const override;

    std::string shorthandStr() const;

    Combatant &getTarget() const { return _target; }
    int getToHit() const { return _factory._toHit; }
    Die getDmgDice() const { return _factory._dmgDice; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    Combatant &_target;
    const RayOfFrostFactory &_factory;
    RollType _rollType;
  };
}
