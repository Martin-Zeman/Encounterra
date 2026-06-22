#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  // Scorching Ray (2024) — level 2. Creates three rays of fire, each a separate spell attack for
  // 2d6 fire. The threat model concentrates all three rays on a single target (the threat-maximising
  // play), so the projected threat equals three single-ray attacks against that target.
  class ScorchingRayFactory : public DirectThreatFactory
  {
    friend class ScorchingRay;

  public:
    static constexpr int level = 2;
    static constexpr int numRays = 3;
    static constexpr SpellRange range = SpellRange::FEET_120;
    static constexpr SpellTarget target = SpellTarget::THREE_CREATURES;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr DamageType dmgType = DamageType::Fire;
    static constexpr Die rayDmgDice = {2, 6};

    ScorchingRayFactory(int toHit, AbilityType abilityType, Combatant *caster, Resource *resource);

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

  class ScorchingRay : public Actoid, public DirectThreat
  {
  public:
    ScorchingRay(Combatant &target, const ScorchingRayFactory &factory, RollType rollType = RollType::STRAIGHT)
        : Actoid(const_cast<ScorchingRayFactory &>(factory), ActoidFlags::IS_SPELL | ActoidFlags::IS_ATTACK_LIKE, factory._abilityType), _target(target),
          _factory(factory), _rollType(rollType)
    {}

    std::string toString() const override;

    std::string shorthandStr() const;

    Combatant &getTarget() const { return _target; }
    int getToHit() const { return _factory._toHit; }
    Die getDmgDice() const { return _factory._dmgDice; }
    static constexpr int getNumRays() { return ScorchingRayFactory::numRays; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    Combatant &_target;
    const ScorchingRayFactory &_factory;
    RollType _rollType;
  };
}
