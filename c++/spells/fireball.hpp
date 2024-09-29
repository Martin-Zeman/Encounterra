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
        : _dc(dc), _abilityType(abilityType), _caster(caster), _resource(resource), _hasSpellSculpting(hasSpellSculpting)
    {
      _savingThrow = SavingThrow::DEX;
      _dmgDice = {{8, 6}};
      // _additionalUpcastDmg = {{1, 6}};
    }

    std::string getAbilityName() const { return "Fireball"; }

    Coord findBestArgs(const Combatant &combatant) const;
    std::vector<std::shared_ptr<Actoid>> createAll(void *previous_action_in_dag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;

    std::optional<Resource *> getResource() override { return _resource; }

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) override;
    double calculateThreatToTargetDelta(Combatant *target /*Add modifiers*/) override;
    double calculateMaxThreat() override;

  private:
    int _dc;
    AbilityType _abilityType;
    Combatant *_caster;
    Resource *_resource;
    bool _hasSpellSculpting;
    SavingThrow _savingThrow;
    std::vector<std::pair<int, int>> _dmgDice;
    // std::vector<std::pair<int, int>> _additionalUpcastDmg;
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
    double calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs) override;
    double calculateThreatDelta(/*Add modifiers*/ const Kwargs &kwargs) override;

  private:
    Coord _coord;
    const FireballFactory &_factory;
    bool _empowered;
    bool _heightened;
  };
}