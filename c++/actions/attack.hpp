#pragma once

#include "core/interfaces.hpp"
#include "core/misc.hpp"
#include "core/resources.hpp"
#include "core/types.hpp"
#include "abilities/on_hit_effect.hpp"
#include <vector>

namespace enc
{
  class Combatant;

  class AttackFactory : public DirectThreatFactory
  {

    friend class Attack;

  public:
    AttackFactory(const std::string &name, const std::string &abilityName, Combatant *combatant, AbilityType abilityType, int toHit,
                  std::vector<Die> dmgDice, int dmgBonus, DamageType dmgType, int attackRange, int critRange = 1, Uses &&ammo = Uses(),
                  std::vector<std::unique_ptr<OnHit>> onHit = {}, std::vector<DmgDieWithType> extraDmg = {}, bool usesDex = false,
                  bool twoHanded = false, Die toHitBonusDie = {});

    AttackFactory(const AttackFactory& other);

    AttackFactory(AttackFactory&& other) noexcept;

    AttackFactory& operator=(const AttackFactory& other);

    AttackFactory& operator=(AttackFactory&& other) noexcept;

    //! This ensures that you get a proper copy of the derived class, even when working with base class pointers.
    virtual std::unique_ptr<AttackFactory> clone() const = 0;

    std::vector<Combatant *> getEligibleTargets() const;
    std::optional<Resource *> getResource() override { return &_ammo; }
     int getRange() const override { return _attackRange; }
    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;
    bool usesDex() { return _usesDex; }
    bool isTwoHanded() { return _twoHanded; }

  protected:
    int _toHit;
    std::vector<Die> _dmgDice;
    int _dmgBonus;
    DamageType _dmgType;
    int _attackRange;
    int _shortRange;
    int _critRange;
    Uses _ammo;
    std::vector<std::unique_ptr<OnHit>> _onHit;
    std::vector<DmgDieWithType> _extraDmg;
    bool _usesDex;
    bool _twoHanded;
    Die _toHitBonusDie;
  };

  class Attack : public Actoid, public DirectThreat
  {
  protected:
    Attack(AbilityType abilityType, Combatant &target, AttackFactory &factory, RollType rollType = RollType::STRAIGHT)
        : Actoid(const_cast<AttackFactory &>(factory), ActoidFlags::IS_ATTACK_LIKE, abilityType), _target(target), _factory(factory),
          _rollType(rollType)
    {}

    std::string toString() const override;
    std::string shorthandStr() const;
    double calculateThreat(const Kwargs &kwargs) override;
    double calculateThreatDelta(const ThreatModifiers &modifiers) const override;

    Combatant &_target;
    AttackFactory &_factory;
    RollType _rollType;
  };
}
