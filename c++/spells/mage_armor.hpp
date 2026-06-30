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

  class MageArmorFactory : public ThreatModifierFactory
  {
    friend class MageArmor;

  public:
    static constexpr int level = 1;
    static constexpr SpellRange range = SpellRange::TOUCH;
    static constexpr SpellTarget target = SpellTarget::ONE_CREATURE;
    static constexpr Duration duration = Duration::UNLIMITED;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::BUFF;

    MageArmorFactory(Combatant *caster, Resource *resource, int armoredBaseAc, AbilityType abilityType = AbilityType::MAGE_ARMOR);

    std::vector<Combatant *> getEligibleTargets() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateMaxThreat() const;

  private:
    Resource *_resource;
    int _armoredBaseAc;
  };

  class MageArmor : public Actoid, public LimitedDurationEffect, public CombatantEffect, public DirectThreat
  {
  public:
    MageArmor(Combatant &target, const MageArmorFactory &factory)
        : Effect(factory._combatant), Actoid(const_cast<MageArmorFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),
          LimitedDurationEffect(factory._combatant, 4800), CombatantEffect(factory._combatant, {&target}), _target(target), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;
    EffectType getEffectType() const override { return EffectType::MAGE_ARMOR; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    Combatant &_target;
    const MageArmorFactory &_factory;
    int _appliedAcDelta = 0;
  };
}
