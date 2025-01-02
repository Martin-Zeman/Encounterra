#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include "effects/limited_duration_effect.hpp"
#include "effects/aoe_spheric_effect.hpp"

namespace enc
{
  class Combatant;

  class SpikeGrowthFactory : public DirectThreatFactory
  {
    friend class SpikeGrowth; // Allow SpikeGrowth to access private members of SpikeGrowthFactory

  public:
    static constexpr int level = 2;
    static constexpr SpellRange range = SpellRange::FEET_150;
    static constexpr SpellTarget target = SpellTarget::RADIUS_20;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = true;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr DamageType dmgType = DamageType::Piercing;

    //! @todo Can I remove the resource here?
    SpikeGrowthFactory(AbilityType abilityType, Combatant *caster, Resource *resource);

    Coord findBestArgs() const;

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

  class SpikeGrowth : public Actoid, public LimitedDurationEffect, public AoeSphericEffect, public DirectThreat
  {
  public:
    SpikeGrowth(const Coord &coord, const SpikeGrowthFactory &factory)
        : Effect(factory._combatant),    // Explicitly construct the virtual base
          AoeEffect(factory._combatant), // Explicitly construct the virtual base
          Actoid(const_cast<SpikeGrowthFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),

          LimitedDurationEffect(factory._combatant, 100),
          AoeSphericEffect(factory._combatant, coord, TRANSLATE_RADIUS.at(SpikeGrowthFactory::target)), _coord(coord), _factory(factory)
    {}

    std::string toString() const override;

    std::string shorthandStr() const;

    EffectType getEffectType() const override { return EffectType::SPIKE_GROWTH; }

    double calculateThreat(const Kwargs &kwargs) override;
    // double calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;
    void onEnter(Combatant *combatant) override;
    void onMoveWithin(Combatant *combatant) override;

    void onExit(Combatant *combatant) override;
    void onStartOfTurn(Combatant *combatant) override;
    void onEndOfTurn(Combatant *combatant) override;

    double threatOnEnter(Combatant *target, const Kwargs &kwargs) const override;
    double threatOnMoveWithin(Combatant *target, const Kwargs &kwargs) const override;

    const CoordVector &getAffectedCoords() const { return SphericAoe::getAffectedCoords(); }

    bool equals(const Actoid &other) const override;

  protected:
    size_t hash() const override;

  private:
    Coord _coord;
    const SpikeGrowthFactory &_factory;
  };
}