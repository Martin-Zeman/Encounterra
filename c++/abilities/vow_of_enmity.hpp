#pragma once

#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "effects/combatant_effect.hpp"
#include "effects/limited_duration_effect.hpp"

namespace enc
{
  class Combatant;

  class VowOfEnmityFactory : public ThreatModifierFactory
  {
    friend class VowOfEnmity;

  public:
    static constexpr int range = 6; // 30 ft.
    static constexpr int durationRounds = 10;

    VowOfEnmityFactory(Combatant *combatant, Resource *channelDivinity);

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _channelDivinity; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;

  private:
    Resource *_channelDivinity;
  };

  class VowOfEnmity : public AttackThreatModifier, public CombatantEffect, public LimitedDurationEffect
  {
  public:
    VowOfEnmity(Combatant &target, VowOfEnmityFactory &factory);

    EffectType getEffectType() const override { return EffectType::VOW_OF_ENMITY; }
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;

    std::string toString() const override;
    std::string shorthandStr() const;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs) override;

  private:
    VowOfEnmityFactory &_factory;
  };
}
