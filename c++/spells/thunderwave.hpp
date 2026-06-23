#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  /**
   * Thunderwave (2024): level 1, a 15-foot cube originating from the caster. Each creature in the area makes
   * a Constitution save, taking 2d8 Thunder damage on a failure and half on a success. Instantaneous
   * (threat / planning only, mirroring Fireball's DirectThreat box-AoE pattern).
   */
  class ThunderwaveFactory : public DirectThreatFactory
  {
    friend class Thunderwave;

  public:
    static constexpr int level = 1;
    static constexpr SpellRange range = SpellRange::TOUCH; // cube originates from the caster
    static constexpr SpellTarget target = SpellTarget::BOX_15;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr DamageType dmgType = DamageType::Thunder;

    ThunderwaveFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource);

    Coord findBestArgs() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;
    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

    int getDc() const { return _dc; }
    SavingThrow getSavingThrow() const { return _savingThrow; }
    const std::vector<Die> &getDmgDice() const { return _dmgDice; }

  private:
    int _dc;
    Resource *_resource;
    SavingThrow _savingThrow;
    std::vector<Die> _dmgDice;
  };

  class Thunderwave : public Actoid, public DirectThreat
  {
  public:
    Thunderwave(const Coord &coord, const ThunderwaveFactory &factory)
        : Actoid(const_cast<ThunderwaveFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType), _coord(coord), _factory(factory)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;

    const Coord &getCoord() const { return _coord; }
    const ThunderwaveFactory &getThunderwaveFactory() const { return _factory; }

    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    Coord _coord;
    const ThunderwaveFactory &_factory;
  };
}
