#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include "effects/limited_duration_effect.hpp"
#include "effects/combatant_effect.hpp"

namespace enc
{
  class Combatant;

  // Hold Person (2024) — level 2 concentration spell. One humanoid within 60 ft must succeed on a
  // Wisdom save or be Paralyzed, re-rolling the save at the end of each of its turns. The threat
  // value combines the outgoing threat we prevent by paralyzing the target with the bonus our allies
  // gain attacking a paralyzed creature (advantage, auto-crit in melee), weighted across a short
  // horizon by the cumulative probability the target keeps failing its save.
  class HoldPersonFactory : public DirectThreatFactory
  {
    friend class HoldPerson;

  public:
    static constexpr int level = 2;
    static constexpr SpellRange range = SpellRange::FEET_60;
    static constexpr SpellTarget target = SpellTarget::ONE_CREATURE;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = true;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr SavingThrow savingThrow = SavingThrow::WIS;

    HoldPersonFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<Combatant *> getEligibleTargets() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;

    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateMaxThreat() const override;

  private:
    int _dc;
    Resource *_resource;
  };

  class HoldPerson : public Actoid, public LimitedDurationEffect, public CombatantEffect, public Threat
  {
  public:
    HoldPerson(Combatant &target, const HoldPersonFactory &factory)
        : Effect(factory._combatant),
          Actoid(const_cast<HoldPersonFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),
          LimitedDurationEffect(factory._combatant, 10),
          CombatantEffect(factory._combatant, {&target}), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    EffectType getEffectType() const override { return EffectType::HOLD_PERSON; }

    double calculateThreat(const Kwargs &kwargs) override;

    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;
    bool combatantSavedAtEndOfTurn(Combatant *combatant) override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    const HoldPersonFactory &_factory;
  };
}
