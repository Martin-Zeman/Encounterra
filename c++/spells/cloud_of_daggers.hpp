#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include "effects/limited_duration_effect.hpp"
#include "effects/spheric_aoe.hpp"

namespace enc
{
  class Combatant;

  class CloudOfDaggersFactory : public DirectThreatFactory
  {
    friend class CloudOfDaggers; // Allow CloudOfDaggers to access private members of CloudOfDaggersFactory

  public:
    static constexpr int level = 2;
    static constexpr SpellRange range = SpellRange::FEET_60;
    static constexpr SpellTarget target = SpellTarget::BOX_5;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = true;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr DamageType dmgType = DamageType::Slashing;

    //! @todo Can I remove the resource here?
    CloudOfDaggersFactory(AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<Combatant *> getEligibleTargets() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;

    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

  private:
    AbilityType _abilityType;
    Resource *_resource;
    Die _dmgDice;
  };

  class CloudOfDaggers : public Actoid, public LimitedDurationEffect, public SphericAoe, public DirectThreat, public AoeThreat
  {
  public:
    CloudOfDaggers(const Coord &coord, const CloudOfDaggersFactory &factory);

    ~CloudOfDaggers() override;

    std::string toString() const override;

    std::string shorthandStr() const;

    double calculateThreat(const Kwargs &kwargs) override;
    // double calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

    bool equals(const Actoid &other) const override;

    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;
    bool isAffecting(Combatant *combatant) const override;
    EffectType getEffectType() const override;

  protected:
    size_t hash() const override;

  private:
    Coord _coord;
    const CloudOfDaggersFactory &_factory;
  };
}