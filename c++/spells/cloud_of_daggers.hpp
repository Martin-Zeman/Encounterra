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

    std::vector<Combatant *> getEligibleTargets() const;
    std::vector<Actoid *> createAll(void *previousActionInDag = nullptr) override;

    Actoid * create(void *target) override;

    int getRange() const override { return static_cast<int>(CloudOfDaggersFactory::range); }

    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(const Combatant &target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(const Combatant &target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

  private:
    AbilityType _abilityType;
    Resource *_resource;
    Die _dmgDice;
  };

  class CloudOfDaggers : public Actoid, public LimitedDurationEffect, public AoeSquareEffect, public DirectThreat
  {
  public:
    CloudOfDaggers(const Coord &coord, const CloudOfDaggersFactory &factory);

    CloudOfDaggers(const CloudOfDaggers &other)
        : Effect(other._initiator), // Initialize virtual base first
          Actoid(const_cast<CloudOfDaggersFactory &>(other._factory), static_cast<ActoidFlags>(other._actoidFlags), other._abilityType),
          LimitedDurationEffect(other._initiator, other._turns), AoeEffect(other._initiator),
          AoeSquareEffect(other._initiator, other._origin, other._length), _factory(other._factory)
    {}

    ~CloudOfDaggers() override;

    Actoid *clone() const override { return new CloudOfDaggers(*this); }

    std::string toString() const override;

    std::string shorthandStr() const;

    double calculateThreat(const Kwargs &kwargs) override;
    // double calculateThreatForAttack(const Combatant &attacker, Actoid *attack, const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

    bool equals(const Actoid &other) const override;

    void onStartOfTurn(Combatant &combatant) override;
    void onEndOfTurn(Combatant &combatant) override;
    void onEnter(Combatant &combatant) override;
    void onMoveWithin(Combatant &combatant) override;
    void onExit(Combatant &combatant) override;

    double threatOnEnter(const Combatant &target, const Kwargs &kwargs) const override;
    double threatOnEndOfTurn(const Combatant &target, const Kwargs &kwargs) const override;

    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant &combatant) override;
    bool isAffecting(const Combatant &combatant) const override;
    EffectType getEffectType() const override;

    const CoordVector &getAffectedCoords() const override;

  protected:
    size_t hash() const override;

  private:
    const CloudOfDaggersFactory &_factory;
  };
}