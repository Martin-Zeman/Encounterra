#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include "effects/limited_duration_effect.hpp"
#include "effects/combatant_effect.hpp"
#include <unordered_set>

namespace enc
{
  class Combatant;

  class SleepFactory : public DirectThreatFactory
  {
    friend class Sleep;

  public:
    static constexpr int level = 1;
    static constexpr SpellRange range = SpellRange::FEET_60;
    static constexpr SpellTarget target = SpellTarget::RADIUS_5;
    static constexpr Duration duration = Duration::MINUTE;
    static constexpr bool concentration = true;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr SavingThrow savingThrow = SavingThrow::WIS;

    SleepFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource);

    Coord findBestArgs() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

  private:
    int _dc;
    Resource *_resource;
  };

  class Sleep : public Actoid, public LimitedDurationEffect, public CombatantEffect, public DirectThreat
  {
  public:
    Sleep(const Coord &coord, const SleepFactory &factory)
        : Effect(factory._combatant), Actoid(const_cast<SleepFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),
          LimitedDurationEffect(factory._combatant, 10), CombatantEffect(factory._combatant, {}), _coord(coord), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;
    EffectType getEffectType() const override { return EffectType::SLEEP; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;
    bool combatantSavedAtEndOfTurn(Combatant *combatant) override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    bool canAffect(Combatant *target) const;
    void removeSleepConditions(Combatant *target) const;

    Coord _coord;
    const SleepFactory &_factory;
    std::unordered_set<Combatant *> _awaitingSecondSave;
  };
}
