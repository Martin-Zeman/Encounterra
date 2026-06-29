#pragma once

#include "spells/spell_stats.hpp"
#include "core/interfaces.hpp"
#include "core/misc.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  // Vicious Mockery (2024): bard cantrip. One creature within 60 ft must succeed on a Wisdom save or take
  // psychic damage and have Disadvantage on its next attack roll before the end of its next turn. The damage
  // scales with caster level (1d6 / 2d6 / 3d6 / 4d6). Modelled as a DC-save damage cantrip like Sacred Flame.
  class ViciousMockeryFactory : public DirectThreatFactory
  {
    friend class ViciousMockery;

  public:
    static constexpr int level = 0;
    static constexpr SpellRange range = SpellRange::FEET_60;
    static constexpr SpellTarget target = SpellTarget::ONE_CREATURE;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr DamageType dmgType = DamageType::Psychic;
    static constexpr SavingThrow savingThrow = SavingThrow::WIS;

    static Die getDmgDice(int level);

    ViciousMockeryFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<Combatant *> getEligibleTargets() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

  private:
    int _dc;
    Resource *_resource;
    Die _dmgDice;
  };

  class ViciousMockery : public Actoid, public DirectThreat
  {
  public:
    ViciousMockery(Combatant &target, const ViciousMockeryFactory &factory)
        : Actoid(const_cast<ViciousMockeryFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType), _target(target), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    Combatant &getTarget() const { return _target; }
    int getDc() const { return _factory._dc; }
    Die getDmgDice() const { return _factory._dmgDice; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;
    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    Combatant &_target;
    const ViciousMockeryFactory &_factory;
  };
}
