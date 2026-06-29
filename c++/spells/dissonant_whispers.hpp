#pragma once

#include "spells/spell_stats.hpp"
#include "core/interfaces.hpp"
#include "core/misc.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  // Dissonant Whispers (2024): level 1 bard enchantment. One creature within 60 ft makes a Wisdom save,
  // taking 3d6 psychic on a failure (half on a success) and, on a failure, must spend its Reaction to flee.
  // Modelled as a DC-save damage spell (half on success), mirroring Sacred Flame's threat shape.
  class DissonantWhispersFactory : public DirectThreatFactory
  {
    friend class DissonantWhispers;

  public:
    static constexpr int level = 1;
    static constexpr SpellRange range = SpellRange::FEET_60;
    static constexpr SpellTarget target = SpellTarget::ONE_CREATURE;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr DamageType dmgType = DamageType::Psychic;
    static constexpr SavingThrow savingThrow = SavingThrow::WIS;
    static constexpr Die dmgDice{3, 6};

    DissonantWhispersFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource);

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
  };

  class DissonantWhispers : public Actoid, public DirectThreat
  {
  public:
    DissonantWhispers(Combatant &target, const DissonantWhispersFactory &factory)
        : Actoid(const_cast<DissonantWhispersFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType), _target(target), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    Combatant &getTarget() const { return _target; }
    int getDc() const { return _factory._dc; }
    Die getDmgDice() const { return DissonantWhispersFactory::dmgDice; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;
    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    Combatant &_target;
    const DissonantWhispersFactory &_factory;
  };
}
