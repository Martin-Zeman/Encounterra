#pragma once

#include "spells/spell_stats.hpp"
#include "core/misc.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "actions/action_types.hpp"

namespace enc
{
  class Combatant;

  class FireboltFactory : public DirectThreatFactory
  {
    friend class Firebolt; // Allow Firebolt to access private members of FireboltFactory

  public:
    static constexpr int level = 0;
    static constexpr SpellRange range = SpellRange::FEET_120;
    static constexpr SpellTarget target = SpellTarget::ONE_CREATURE;
    static constexpr Duration duration = Duration::INSTANTANEOUS;
    static constexpr bool concentration = false;
    static constexpr SpellType type = SpellType::HARMFUL;
    static constexpr DamageType dmgType = DamageType::Fire;

    static Die getDmgDice(int level)
    {
      if(level >= 1 && level <= 4)
        {
          return {1, 10};
        }
      else if(level >= 5 && level <= 10)
        {
          return {2, 10};
        }
      else if(level >= 11 && level <= 16)
        {
          return {3, 10};
        }
      else if(level >= 17)
        {
          return {4, 10};
        }
      else
        {
          throw std::runtime_error("Incorrect caster level of Firebolt");
        }
    }

    //! @todo Can I remove the resource here?
    FireboltFactory(int toHit, AbilityType abilityType, Combatant *caster, Resource *resource);

    std::vector<Combatant *> getEligibleTargets() const;
    std::vector<Actoid *> createAll(void *previousActionInDag = nullptr) override;

    Actoid * create(void *target) override;

    std::optional<Resource *> getResource() override { return _resource; }
    int getRange() const override { return static_cast<int>(FireboltFactory::range); }

    double calculateThreatToTarget(const Combatant& target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(const Combatant &target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;

  private:
    int _toHit;
    Resource *_resource;
    Die _dmgDice;
  };

  class Firebolt : public Actoid, public DirectThreat
  {
  public:
    Firebolt(Combatant &target, const FireboltFactory &factory, RollType rollType = RollType::STRAIGHT)
        : Actoid(const_cast<FireboltFactory &>(factory), ActoidFlags::IS_SPELL | ActoidFlags::IS_ATTACK_LIKE, AbilityType::FIREBOLT), _target(target),
          _factory(factory)
    {}

    std::string toString() const override;

    std::string shorthandStr() const;

    double calculateThreat(const Kwargs &kwargs) override;
    // double calculateThreatForAttack(const Combatant &attacker, Actoid *attack, const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;

    bool equals(const Actoid &other) const override;

  protected:
    size_t hash() const override;

  private:
    Combatant &_target;
    const FireboltFactory &_factory;
    RollType _rollType;
  };
}