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

  class BlessFactory : public ThreatModifierFactory
  {
    friend class Bless;

  public:
    static constexpr int level = 1;
    static constexpr SpellRange range = SpellRange::FEET_30;
    static constexpr SpellTarget target = SpellTarget::THREE_CREATURES;
    static constexpr Duration duration = Duration::MINUTE;
    static constexpr bool concentration = true;
    static constexpr SpellType type = SpellType::BUFF;
    static constexpr double SAVING_THROW_BONUS_MULTIPLIER = 1.25;
    static constexpr double ROUND_HORIZON = 3.0;

    BlessFactory(AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<std::vector<Combatant *>> getEligibleTargetGroups() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;

  private:
    Resource *_resource;
  };

  class Bless : public AttackThreatModifier, public CombatantEffect, public LimitedDurationEffect
  {
  public:
    static constexpr Die bonusDie{1, 4};

    Bless(std::vector<Combatant *> targets, BlessFactory &factory);

    EffectType getEffectType() const override { return EffectType::BLESS; }
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;

    std::string toString() const override;
    std::string shorthandStr() const;

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs) override;
    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    BlessFactory &_factory;
  };
}
