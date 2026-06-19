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
    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
    double calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const override;
    double calculateMaxThreat() const override;
    int getRange() const override { return _attackRange; }
    bool usesDex() { return _usesDex; }
    bool isTwoHanded() { return _twoHanded; }
    int getToHit() const { return _toHit; }
    const std::vector<Die> &getDmgDice() const { return _dmgDice; }
    int getDmgBonus() const { return _dmgBonus; }
    DamageType getDmgType() const { return _dmgType; }
    int getCritRange() const { return _critRange; }
    const std::vector<std::unique_ptr<OnHit>> &getOnHits() const { return _onHit; }
    void setAdvantageVsGrappledTarget(bool value) { _advantageVsGrappledTarget = value; }
    bool hasAdvantageVsGrappledTarget() const { return _advantageVsGrappledTarget; }

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
    bool _advantageVsGrappledTarget = false;
  };

  class Attack : public Actoid, public DirectThreat
  {
  public:
    Combatant &getTarget() const { return _target; }
    AttackFactory &getAttackFactory() const { return _factory; }
    void setRollType(RollType rollType) { _rollType = rollType; }

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
