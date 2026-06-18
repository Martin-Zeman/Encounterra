#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include "effects/limited_duration_effect.hpp"
#include "effects/aoe_square_effect.hpp"

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


    std::vector<Combatant*> getEligibleTargets() const;
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

  class CloudOfDaggers : public Actoid, public LimitedDurationEffect, public AoeSquareEffect, public DirectThreat, public AoeThreat
  {
  public:
    CloudOfDaggers(const Coord &coord, const CloudOfDaggersFactory &factory)
        : Effect(factory._combatant),    // Explicitly construct the virtual base
          Actoid(const_cast<CloudOfDaggersFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),
          LimitedDurationEffect(factory._combatant, 10),
          AoeSquareEffect(factory._combatant, coord, TRANSLATE_BOX.at(CloudOfDaggersFactory::target)), _coord(coord), _factory(factory)
    {}

    std::string toString() const override;

    std::string shorthandStr() const;

    EffectType getEffectType() const override { return EffectType::CLOUD_OF_DAGGERS; }

    double calculateThreat(const Kwargs &kwargs) override;
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

    double threatOnEnter(Combatant *target, const Kwargs & kwargs) const override;
    double threatOnStartOfTurn(Combatant *target, const Kwargs & kwargs) const override;
    double threatOnMoveWithin(Combatant *target, const Kwargs & kwargs) const override;
    double threatOnEndOfTurn(Combatant *target, const Kwargs & kwargs) const override;

    const CoordVector &getAffectedCoords() const override { return SquareAoe::getAffectedCoords(); }

  private:
    Coord _coord;
    const CloudOfDaggersFactory &_factory;
  };
}