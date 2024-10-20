#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  class FireballFactory : public DirectThreatFactory
  {
    friend class Fireball; // Allow Fireball to access private members of FireballFactory

  public:
    static constexpr int level = 3;
    static constexpr SpellRange range = SpellRange::FEET_150;
    static constexpr SpellTarget target = SpellTarget::RADIUS_20;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr DamageType dmgType = DamageType::Fire;

    FireballFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource, bool hasSpellSculpting = false)
        : DirectThreatFactory("FireballFactory", caster, abilityType), _dc(dc), _resource(resource), _hasSpellSculpting(hasSpellSculpting),
          _savingThrow(SavingThrow::DEX), _dmgDice({{8, 6}})
    {
      // _additionalUpcastDmg = {{1, 6}};
    }

    std::string getAbilityName() const { return "Fireball"; }

    Coord findBestArgs() const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;

    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateMaxThreat() const override;

  private:
    int _dc;
    Resource *_resource;
    bool _hasSpellSculpting;
    SavingThrow _savingThrow;
    std::vector<Die> _dmgDice;
    // std::vector<Die>_additionalUpcastDmg;
  };

  class Fireball : public Actoid, public DirectThreat
  {
  public:
    Fireball(const Coord &coord, const FireballFactory &factory, bool empowered = false, bool heightened = false)
        : Actoid(const_cast<FireballFactory &>(factory), ActoidFlags::IS_SPELL, AbilityType::FIREBALL), _coord(coord), _factory(factory),
          _empowered(empowered), _heightened(heightened)
    {}

    std::string toString() const
    {
      std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_FIREBALL) ? "Quickened " : "";
      return prefix + "Fireball at (" + std::to_string(_coord[0]) + ", " + std::to_string(_coord[1]) + ")";
    }

    std::string shorthandStr() const
    {
      std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_FIREBALL) ? "Quickened " : "";
      return prefix + "Fireball";
    }

    double calculateThreat(const Kwargs &kwargs) override;
    std::optional<std::vector<Coord>>
    getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                      const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

  private:
    Coord _coord;
    const FireballFactory &_factory;
    bool _empowered;
    bool _heightened;
  };
}