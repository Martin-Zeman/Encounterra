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

  class ShieldOfFaithFactory : public ThreatModifierFactory
  {
    friend class ShieldOfFaith;

  public:
    static constexpr int level = 1;
    static constexpr SpellRange range = SpellRange::FEET_60;
    static constexpr SpellTarget target = SpellTarget::ONE_CREATURE;
    static constexpr Duration duration = Duration::TEN_MINUTES;
    static constexpr bool concentration = true;
    static constexpr SpellType type = SpellType::BUFF;
    static constexpr int acBonus = 2;

    ShieldOfFaithFactory(Combatant *caster, Resource *resource);

    std::vector<Combatant *> getEligibleTargets() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;

  private:
    Resource *_resource;
  };

  class ShieldOfFaith : public Actoid, public CombatantEffect, public LimitedDurationEffect, public Threat
  {
  public:
    ShieldOfFaith(Combatant &target, ShieldOfFaithFactory &factory);

    EffectType getEffectType() const override { return EffectType::SHIELD_OF_FAITH; }
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;

    std::string toString() const override;
    std::string shorthandStr() const;

    double calculateThreat(const Kwargs &kwargs) override;
    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    ShieldOfFaithFactory &_factory;
    bool _applied = false;
  };
}
