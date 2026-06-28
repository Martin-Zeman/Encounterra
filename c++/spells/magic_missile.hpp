#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"
#include <array>

namespace enc
{
  class Combatant;

  class MagicMissileFactory : public DirectThreatFactory
  {
    friend class MagicMissile;

  public:
    static constexpr int level = 1;
    static constexpr SpellRange range = SpellRange::FEET_120;
    static constexpr SpellTarget target = SpellTarget::THREE_CREATURES;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr DamageType dmgType = DamageType::Force;
    static constexpr Die dmgDice = Die{1, 4};
    static constexpr int dmgBonus = 1;

    MagicMissileFactory(AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<std::array<Combatant *, 3>> getEligibleTargetSets() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

  private:
    Resource *_resource;
  };

  class MagicMissile : public Actoid, public DirectThreat
  {
  public:
    MagicMissile(const std::array<Combatant *, 3> &targets, const MagicMissileFactory &factory)
        : Actoid(const_cast<MagicMissileFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType), _targets(targets), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;
    const std::array<Combatant *, 3> &getTargets() const { return _targets; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    std::array<Combatant *, 3> _targets;
    const MagicMissileFactory &_factory;
  };
}
