#pragma once

#include "spells/spell_stats.hpp"
#include "core/interfaces.hpp"
#include "core/misc.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include "effects/combatant_effect.hpp"
#include "effects/limited_duration_effect.hpp"

namespace enc
{
  class Combatant;

  class GuidingBoltFactory : public DirectThreatFactory
  {
    friend class GuidingBolt;

  public:
    static constexpr int level = 1;
    static constexpr SpellRange range = SpellRange::FEET_120;
    static constexpr SpellTarget target = SpellTarget::ONE_CREATURE;
    static constexpr Duration duration = Duration::ROUND_ONE;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr DamageType dmgType = DamageType::Radiant;

    GuidingBoltFactory(int toHit, AbilityType abilityType, Combatant *caster, Resource *resource);

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
    Die _dmgDice{4, 6};
  };

  class GuidingBolt : public Actoid, public DirectThreat
  {
  public:
    GuidingBolt(Combatant &target, const GuidingBoltFactory &factory)
        : Actoid(const_cast<GuidingBoltFactory &>(factory), ActoidFlags::IS_SPELL | ActoidFlags::IS_ATTACK_LIKE, factory._abilityType),
          _target(target), _factory(factory)
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
    const GuidingBoltFactory &_factory;
  };

  class GuidingBoltEffect : public CombatantEffect, public LimitedDurationEffect
  {
  public:
    GuidingBoltEffect(Combatant *caster, Combatant *target)
        : Effect(caster, target), CombatantEffect(caster, {target}), LimitedDurationEffect(caster, 1)
    {}

    EffectType getEffectType() const override { return EffectType::GUIDING_BOLT; }
    void activate(const Kwargs &kwargs = {}) override {}
    void deactivate() override {}
    bool deactivateForCombatant(Combatant *combatant) override { return false; }
  };
}
