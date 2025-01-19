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

  class HungerOfHadarFactory : public DirectThreatFactory
  {
    friend class HungerOfHadar; // Allow HungerOfHadar to access private members

  public:
    static constexpr int level = 3;
    static constexpr SpellRange range = SpellRange::FEET_150;
    static constexpr SpellTarget target = SpellTarget::RADIUS_20;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = true;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr DamageType dmgType = DamageType::Cold;

    HungerOfHadarFactory(int dc, AbilityType abilityType, const std::shared_ptr<Combatant> &caster, Resource *resource);

    std::vector<Combatant *> getEligibleTargets() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;

    int getRange() const override { return static_cast<int>(HungerOfHadarFactory::range); }

    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(const Combatant &target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(const Combatant &target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

  private:
    int _dc;
    AbilityType _abilityType;
    Resource *_resource;
    SavingThrow _savingThrow;
    Die _dmgDice;
  };

  class HungerOfHadar : public Actoid, public LimitedDurationEffect, public AoeSphericEffect, public DirectThreat
  {
  public:
    HungerOfHadar(const Coord &coord, const HungerOfHadarFactory &factory);

    std::string toString() const override;
    std::string shorthandStr() const;

    void onStartOfTurn(Combatant &combatant) override;
    void onEndOfTurn(Combatant &combatant) override;
    void onEnter(Combatant &combatant) override;
    void onMoveWithin(Combatant &combatant) override;
    void onExit(Combatant &combatant) override;

    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant &combatant) override;

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;
    EffectType getEffectType() const override;

    const CoordVector &getAffectedCoords() const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;
    bool equals(const Actoid &other) const override;

  protected:
    size_t hash() const override;

  private:
    Coord _coord;
    const HungerOfHadarFactory &_factory;
  };
}
